"""
TikTok Beta US Automation Notifier - Core Engine
================================================
Điều phối trung tâm: Nạp cấu hình Excel động ➔ Quét YouTube RSS ➔ Lọc Shorts & Thời lượng
➔ Kiểm tra Idempotency SQLite ➔ Bắn thông báo Telegram theo định danh Máy/Kênh.
"""

import time
import signal
import threading
from typing import Optional, List, Dict
from pathlib import Path

from config.settings import logger, config
from src.parser.excel_parser import ExcelConfigParser, ChannelConfig
from src.fetcher.youtube_rss import YouTubeFetcher, YouTubeVideo
from src.notifier.telegram_bot import TelegramNotifier
from src.core.database import TrackingDatabase


class AutomationEngine:
    """Bộ điều phối tự động hóa chính của hệ thống."""

    def __init__(
        self,
        parser: Optional[ExcelConfigParser] = None,
        fetcher: Optional[YouTubeFetcher] = None,
        notifier: Optional[TelegramNotifier] = None,
        db: Optional[TrackingDatabase] = None,
    ):
        self.parser = parser or ExcelConfigParser()
        self.fetcher = fetcher or YouTubeFetcher()
        self.notifier = notifier or TelegramNotifier()
        self.db = db or TrackingDatabase()
        self.is_running = True
        self.scan_lock = threading.Lock()

    @property
    def is_scanning(self) -> bool:
        """Kiểm tra xem hệ thống có đang trong chu kỳ quét hay không."""
        return self.scan_lock.locked()

    def scan_once(
        self,
        machine: Optional[str] = None,
        tiktok_channel: Optional[str] = None,
        dry_run: bool = False,
        seed_mode: bool = False,
        max_age_hours: Optional[int] = None,
    ) -> int:
        """
        Thực hiện một chu kỳ quét (Thread-safe có khóa bảo vệ scan_lock).
        """
        with self.scan_lock:
            return self._scan_once_unlocked(
                machine=machine,
                tiktok_channel=tiktok_channel,
                dry_run=dry_run,
                seed_mode=seed_mode,
                max_age_hours=max_age_hours,
            )

    def _scan_once_unlocked(
        self,
        machine: Optional[str] = None,
        tiktok_channel: Optional[str] = None,
        dry_run: bool = False,
        seed_mode: bool = False,
        max_age_hours: Optional[int] = None,
    ) -> int:
        """
        Nội dung thực thi quét chi tiết.
        Hỗ trợ:
        - Quét toàn bộ mạng lưới (mặc định)
        - Quét theo 1 Máy cụ thể (ví dụ: machine='Máy 01')
        - Quét theo 1 Kênh TikTok cụ thể (ví dụ: tiktok_channel='@daily_crime_us')
        - Chế độ dry_run: chỉ hiển thị log, không bắn tin nhắn thật và không lưu DB.
        - Chế độ seed_mode: khởi tạo mốc cơ sở, lưu vết các video hiện tại vào DB mà KHÔNG bắn tin nhắn Telegram.
        - max_age_hours: chỉ thông báo video mới đăng trong vòng X giờ (mặc định config.MAX_VIDEO_AGE_HOURS).
        """
        # 1. Nạp danh sách kênh TikTok theo điều kiện lọc
        target_channels = self.parser.get_channels(
            machine=machine,
            tiktok_channel=tiktok_channel,
            force_reload=True,
        )

        if not target_channels:
            logger.warning(
                f"Không tìm thấy kênh nào khớp với bộ lọc (Máy='{machine}', Kênh='{tiktok_channel}')."
            )
            return 0

        logger.info(
            f"Bắt đầu chu kỳ quét cho {len(target_channels)} kênh TikTok "
            f"[Bộ lọc: Máy='{machine or 'Tất cả'}', Kênh='{tiktok_channel or 'Tất cả'}']"
        )

        # 2. Gom nhóm các nguồn YouTube cần quét (Tránh quét trùng lặp mạng)
        source_to_channels: Dict[str, List[ChannelConfig]] = {}
        for ch_cfg in target_channels:
            for src in ch_cfg.youtube_sources:
                source_to_channels.setdefault(src, []).append(ch_cfg)

        total_unique_sources = len(source_to_channels)
        logger.info(f"Tổng số nguồn YouTube cần quét trong chu kỳ này: {total_unique_sources}")

        new_notifications_count = 0

        # 3. Quét từng nguồn YouTube
        for src_idx, (source_url, interested_channels) in enumerate(source_to_channels.items(), 1):
            logger.info(
                f"[{src_idx}/{total_unique_sources}] Đang xử lý nguồn: {source_url} "
                f"(Phục vụ cho {len(interested_channels)} kênh TikTok)"
            )

            try:
                # Quét nhanh RSS entries mà KHÔNG tốn request HEAD/GET
                videos = self.fetcher.fetch_raw_rss_entries(source_url)
            except Exception as e:
                logger.warning(f"Bỏ qua quét nguồn {source_url} (lỗi: {e})")
                continue

            if not videos:
                continue

            # 4. Kiểm tra từng video
            # A. Chế độ SEED BASELINE: Đánh dấu mốc toàn bộ video cũ siêu tốc (0 request HEAD/GET)
            if seed_mode:
                for vid in videos:
                    for target_ch in interested_channels:
                        if not self.db.is_tracked(vid.video_id, target_ch.tiktok_channel):
                            self.db.mark_as_tracked(
                                video_id=vid.video_id,
                                tiktok_channel=target_ch.tiktok_channel,
                                machine_name=target_ch.machine_name,
                                channel_id=vid.channel_id,
                                video_title=vid.title,
                                published_at=vid.published_at,
                                status="SEEDED",
                            )
                            new_notifications_count += 1
                            logger.debug(f"[SEED] Đã lưu vết mốc: {vid.title} cho {target_ch.display_tag}")
                continue

            # B. Chế độ Giám Sát Bình Thường
            for vid in videos:
                untracked_targets = [
                    ch for ch in interested_channels
                    if not self.db.is_tracked(vid.video_id, ch.tiktok_channel)
                ]
                if not untracked_targets:
                    continue

                # Kiểm tra tuổi video: Nếu video quá cũ (> max_age_hours), tự động lưu vết mà không bắn tin nhắn
                effective_max_age = max_age_hours if max_age_hours is not None else config.MAX_VIDEO_AGE_HOURS
                if effective_max_age > 0 and vid.age_hours > effective_max_age:
                    logger.debug(
                        f"Bỏ qua video cũ ({vid.age_hours:.1f}h > {effective_max_age}h): "
                        f"[{vid.title}] (Đã tự động lưu vết mốc)"
                    )
                    for target_ch in untracked_targets:
                        self.db.mark_as_tracked(
                            video_id=vid.video_id,
                            tiktok_channel=target_ch.tiktok_channel,
                            machine_name=target_ch.machine_name,
                            channel_id=vid.channel_id,
                            video_title=vid.title,
                            published_at=vid.published_at,
                            status="OLD_VIDEO",
                        )
                    continue

                # Video MỚI thật sự! Chỉ lúc này mới gửi HTTP HEAD và GET để làm giàu thông tin
                vid = self.fetcher.enrich_video_details(vid)

                # Lọc Shorts
                if config.FILTER_OUT_SHORTS and vid.is_short:
                    logger.debug(f"Bỏ qua video Shorts: {vid.title} ({vid.video_id})")
                    for target_ch in untracked_targets:
                        self.db.mark_as_tracked(
                            video_id=vid.video_id,
                            tiktok_channel=target_ch.tiktok_channel,
                            machine_name=target_ch.machine_name,
                            channel_id=vid.channel_id,
                            video_title=vid.title,
                            published_at=vid.published_at,
                            status="FILTERED_SHORT",
                        )
                    continue

                # Lọc Livestream
                if config.FILTER_OUT_LIVESTREAMS and vid.is_live:
                    logger.debug(f"Bỏ qua video Livestream: {vid.title} ({vid.video_id})")
                    for target_ch in untracked_targets:
                        self.db.mark_as_tracked(
                            video_id=vid.video_id,
                            tiktok_channel=target_ch.tiktok_channel,
                            machine_name=target_ch.machine_name,
                            channel_id=vid.channel_id,
                            video_title=vid.title,
                            published_at=vid.published_at,
                            status="FILTERED_LIVE",
                        )
                    continue

                # Lọc thời lượng tối thiểu nếu có
                if config.MIN_VIDEO_DURATION_SECONDS > 0 and 0 < vid.duration_seconds < config.MIN_VIDEO_DURATION_SECONDS:
                    logger.debug(f"Bỏ qua video ngắn ({vid.duration_seconds}s): {vid.title}")
                    for target_ch in untracked_targets:
                        self.db.mark_as_tracked(
                            video_id=vid.video_id,
                            tiktok_channel=target_ch.tiktok_channel,
                            machine_name=target_ch.machine_name,
                            channel_id=vid.channel_id,
                            video_title=vid.title,
                            published_at=vid.published_at,
                            status="FILTERED_SHORT_DURATION",
                        )
                    continue

                # Video ĐẠT CHUẨN HOÀN TOÀN!
                for target_ch in untracked_targets:
                    logger.info(
                        f"⚡ PHÁT HIỆN VIDEO MỚI: [{vid.title}] "
                        f"➔ Đích đến: {target_ch.display_tag} ({target_ch.machine_name})"
                    )

                    if dry_run:
                        logger.info(
                            f"[DRY-RUN] Giả lập thông báo tới {target_ch.display_tag}:\n"
                            f"  • Video: {vid.title}\n"
                            f"  • Thời lượng: {vid.duration_formatted}\n"
                            f"  • Link: {vid.link}"
                        )
                        new_notifications_count += 1
                        continue

                    # Bắn thông báo Telegram thật
                    send_success = self.notifier.send_notification(vid, target_ch)
                    if send_success:
                        self.db.mark_as_tracked(
                            video_id=vid.video_id,
                            tiktok_channel=target_ch.tiktok_channel,
                            machine_name=target_ch.machine_name,
                            channel_id=vid.channel_id,
                            video_title=vid.title,
                            published_at=vid.published_at,
                            status="SENT",
                        )
                        new_notifications_count += 1
                        time.sleep(config.NOTIFICATION_DELAY_SECONDS)

            # Tạm nghỉ ngắn giữa các nguồn YouTube để tôn trọng rate limit
            time.sleep(0.5)

        if seed_mode:
            logger.info(
                f"🌱 [SEED BASELINE] Hoàn tất khởi tạo mốc cơ sở! Đã ghi nhận {new_notifications_count} video hiện tại vào DB."
            )
        else:
            logger.info(
                f"✅ Hoàn tất chu kỳ quét. Tổng số video mới đã gửi thông báo: {new_notifications_count}"
            )
        return new_notifications_count

    def run_scheduler(
        self,
        interval_seconds: Optional[int] = None,
        machine: Optional[str] = None,
        tiktok_channel: Optional[str] = None,
        enable_bot: bool = True,
    ) -> None:
        """
        Vòng lặp tự động hóa liên tục (Continuous Automation Loop).
        Tự động xử lý tín hiệu dừng chương trình (Ctrl+C, SIGTERM).
        Hỗ trợ tích hợp song song luồng tương tác Telegram Bot Listener.
        """
        interval = interval_seconds or config.CHECK_INTERVAL_SECONDS

        bot_handler = None
        if enable_bot and self.notifier.is_configured:
            try:
                from src.bot.command_handler import TelegramCommandHandler
                bot_handler = TelegramCommandHandler(engine=self)
                bot_handler.run_in_background()
            except Exception as e:
                logger.warning(f"Không thể khởi động Telegram Bot Listener: {e}")

        def handle_signal(sig, frame):
            logger.info("Nhận tín hiệu dừng (SIGINT/SIGTERM). Đang tắt hệ thống an toàn...")
            self.is_running = False
            if bot_handler:
                bot_handler.stop()

        signal.signal(signal.SIGINT, handle_signal)
        try:
            signal.signal(signal.SIGTERM, handle_signal)
        except Exception:
            pass

        logger.info(
            f"🚀 TikTok Beta US Automation Notifier ĐANG CHẠY "
            f"(Chu kỳ lặp: {interval} giây = {interval/60:.1f} phút)"
        )

        cycle_count = 0
        try:
            while self.is_running:
                cycle_count += 1
                logger.info(f"--- BẮT ĐẦU CHU KỲ #{cycle_count} ---")

                try:
                    self.scan_once(machine=machine, tiktok_channel=tiktok_channel)
                except Exception as e:
                    logger.exception(f"Lỗi không mong muốn trong chu kỳ #{cycle_count}: {e}")

                if not self.is_running:
                    break

                logger.info(f"Nghỉ {interval} giây trước chu kỳ tiếp theo...")
                # Ngủ ngắt quãng để phản hồi tín hiệu dừng ngay lập tức
                for _ in range(int(interval)):
                    if not self.is_running:
                        break
                    time.sleep(1)
        finally:
            if bot_handler:
                bot_handler.stop()

        logger.info("Hệ thống đã dừng hoàn toàn.")
