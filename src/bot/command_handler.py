"""
TikTok Beta US Automation Notifier - Telegram Command Handler
=============================================================
Xử lý tương tác 2 chiều từ Telegram Chat:
- Các lệnh Slash Menu: /videos, /update, /status, /help, /start
- Bàn phím điều khiển tương tác nhanh (Persistent Reply Keyboard):
  [ 🚀 Quét Video Mới ]       [ 🔄 Cập Nhật Google Drive ]
  [ 📊 Xem Báo Cáo 22 Máy ]   [ 💡 Hướng Dẫn ]
- Bảo mật Whitelist: Chỉ tài khoản cấu hình trong TELEGRAM_CHAT_ID mới có quyền ra lệnh.
- Thread-safe: Đồng bộ an toàn với chu kỳ quét tự động của AutomationEngine.
"""

import threading
import time
from typing import Optional, Dict, Any, Tuple

from config.settings import logger, config
from src.notifier.telegram_bot import TelegramNotifier
from src.core.database import TrackingDatabase
from src.core.engine import AutomationEngine
from src.parser.excel_parser import ExcelConfigParser
from src.fetcher.youtube_rss import YouTubeFetcher
from src.sync.gdrive_sync import GoogleSheetSync


class TelegramCommandHandler:
    """
    Bộ lắng nghe và điều phối lệnh từ Telegram Bot.
    """

    def __init__(
        self,
        engine: Optional[AutomationEngine] = None,
        notifier: Optional[TelegramNotifier] = None,
        parser: Optional[ExcelConfigParser] = None,
        fetcher: Optional[YouTubeFetcher] = None,
        db: Optional[TrackingDatabase] = None,
        syncer: Optional[GoogleSheetSync] = None,
    ):
        self.engine = engine or AutomationEngine()
        self.notifier = notifier or self.engine.notifier
        self.parser = parser or self.engine.parser
        self.fetcher = fetcher or self.engine.fetcher
        self.db = db or self.engine.db
        self.syncer = syncer or GoogleSheetSync()

        self.is_running = False
        self._poll_thread: Optional[threading.Thread] = None
        self.offset_file = config.DATA_DIR / "bot_update_offset.txt"
        self.last_update_id: Optional[int] = self._load_last_offset()

    def _load_last_offset(self) -> Optional[int]:
        """Đọc offset cập nhật gần nhất từ file để tránh nhận lại tin cũ khi khởi động lại bot."""
        if self.offset_file.exists():
            try:
                val = int(self.offset_file.read_text(encoding="utf-8").strip())
                return val
            except Exception:
                pass
        return None

    def _save_last_offset(self, offset: int) -> None:
        """Lưu vết offset để Telegram server giải phóng hàng đợi tin nhắn."""
        try:
            self.offset_file.write_text(str(offset), encoding="utf-8")
        except Exception as e:
            logger.debug(f"Không thể lưu bot offset: {e}")

    @staticmethod
    def get_reply_keyboard() -> Dict[str, Any]:
        """Tạo bàn phím tương tác nhanh hiển thị cố định ở Telegram chat."""
        return {
            "keyboard": [
                [
                    {"text": "🚀 Quét Video Mới"},
                    {"text": "🔄 Cập Nhật Google Drive"},
                ],
                [
                    {"text": "📊 Xem Báo Cáo 22 Máy"},
                    {"text": "💡 Hướng Dẫn"},
                ],
            ],
            "resize_keyboard": True,
            "is_persistent": True,
        }

    def setup_bot_commands(self) -> bool:
        """Đăng ký danh mục slash command với menu Telegram Bot."""
        commands = [
            {"command": "videos", "description": "🚀 Quét video mới ngay lập tức"},
            {"command": "update", "description": "🔄 Đồng bộ dữ liệu mới từ Google Sheets"},
            {"command": "status", "description": "📊 Xem báo cáo tình trạng hệ thống & 22 máy"},
            {"command": "help", "description": "💡 Xem hướng dẫn & hiển thị bàn phím điều khiển"},
        ]
        return self.notifier.set_bot_commands(commands)

    def is_authorized(self, message: Dict[str, Any]) -> Tuple[bool, str, str]:
        """
        Kiểm tra quyền truy cập dựa trên Whitelist TELEGRAM_CHAT_ID.
        Trả về (is_allowed, chat_id, text).
        """
        chat_id = str(message.get("chat", {}).get("id", "")).strip()
        from_id = str(message.get("from", {}).get("id", "")).strip()
        text = str(message.get("text", "")).strip()

        authorized_id = str(config.TELEGRAM_CHAT_ID).strip()
        if not authorized_id:
            # Chưa cấu hình whitelist -> Từ chối để an toàn
            return False, chat_id, text

        # Hợp lệ nếu chat_id hoặc from_id khớp với config
        if chat_id == authorized_id or from_id == authorized_id:
            return True, chat_id, text

        return False, chat_id, text

    def handle_videos_command(self, chat_id: str) -> None:
        """Xử lý lệnh /videos: Quét video mới tức thì."""
        if self.engine.is_scanning:
            self.notifier.send_message(
                "⚠️ <b>Hệ thống đang bận thực hiện chu kỳ quét khác.</b>\n"
                "Vui lòng đợi vài giây rồi thử lại!",
                chat_id=chat_id,
            )
            return

        self.notifier.send_message(
            "⏳ <b>Đang quét kiểm tra 22 máy & 102 nguồn YouTube...</b>\n"
            "<i>Hệ thống đang đối chiếu video mới phát hành. Vui lòng chờ trong giây lát!</i>",
            chat_id=chat_id,
        )

        try:
            new_vids = self.engine.scan_once()
            if new_vids > 0:
                self.notifier.send_message(
                    f"✅ <b>Hoàn tất chu kỳ quét!</b>\n"
                    f"━━━━━━━━━━━━━━━━━━━━\n"
                    f"🎯 Đã phát hiện và gửi <b>{new_vids} video mới</b> lên khung chat cho các máy tương ứng.",
                    chat_id=chat_id,
                )
            else:
                self.notifier.send_message(
                    "✨ <b>Tất cả 22 máy đều đã cập nhật!</b>\n"
                    "Hiện tại chưa có video mới nào xuất hiện từ 102 nguồn YouTube theo dõi.",
                    chat_id=chat_id,
                )
        except Exception as e:
            logger.exception(f"Lỗi khi thực hiện quét video qua Telegram: {e}")
            self.notifier.send_message(
                f"❌ <b>Lỗi trong quá trình quét:</b> <code>{e}</code>",
                chat_id=chat_id,
            )

    def handle_update_command(self, chat_id: str) -> None:
        """Xử lý lệnh /update: Đồng bộ dữ liệu từ Google Sheets."""
        self.notifier.send_message(
            "⏳ <b>Đang tải & đồng bộ dữ liệu cấu hình từ Google Sheets...</b>",
            chat_id=chat_id,
        )

        target_url = config.GOOGLE_SHEET_URL
        if not target_url:
            self.notifier.send_message(
                "❌ <b>Chưa cấu hình GOOGLE_SHEET_URL!</b> Vui lòng kiểm tra file .env trên máy tính.",
                chat_id=chat_id,
            )
            return

        try:
            success, msg, count = self.syncer.sync(target_url)
            if success:
                # Xóa các nguồn bị đánh dấu __DEAD__ để cho phép phân giải lại nếu người dùng vừa sửa link
                dead_keys = [
                    k for k, v in self.fetcher._channel_cache.items()
                    if v == "__DEAD__"
                ]
                for k in dead_keys:
                    self.fetcher._channel_cache.pop(k, None)
                if dead_keys:
                    self.fetcher._save_cache()

                # Tải lại cấu hình mới nhất
                channels = self.parser.get_channels(force_reload=True)
                self.notifier.send_message(
                    "✅ <b>Đồng bộ Google Drive thành công!</b>\n"
                    "━━━━━━━━━━━━━━━━━━━━\n"
                    f"🖥️ <b>Tổng thiết bị:</b> 22 máy\n"
                    f"📱 <b>Tổng kênh TikTok:</b> {len(channels)} kênh ({count} dòng hợp lệ)\n"
                    f"🔄 <b>Trạng thái:</b> Sẵn sàng cho các chu kỳ quét tiếp theo!\n"
                    "━━━━━━━━━━━━━━━━━━━━\n"
                    "💡 <i>Mẹo: Bạn có thể bấm <b>[ 🚀 Quét Video Mới ]</b> để quét ngay theo danh sách mới.</i>",
                    chat_id=chat_id,
                )
            else:
                self.notifier.send_message(
                    f"❌ <b>Đồng bộ thất bại:</b> <code>{msg}</code>",
                    chat_id=chat_id,
                )
        except Exception as e:
            logger.exception(f"Lỗi khi đồng bộ Google Sheets qua Telegram: {e}")
            self.notifier.send_message(
                f"❌ <b>Lỗi ngoại lệ khi đồng bộ:</b> <code>{e}</code>",
                chat_id=chat_id,
            )

    def handle_status_command(self, chat_id: str) -> None:
        """Xử lý lệnh /status: Báo cáo tình trạng hệ thống & 22 máy."""
        try:
            channels = self.parser.get_channels()
            bkt_count = sum(1 for c in channels if c.is_bkt())
            kbkt_count = len(channels) - bkt_count
            all_sources = set([s for c in channels for s in c.youtube_sources])

            valid_sources = [
                s for s, ch_id in self.fetcher._channel_cache.items()
                if ch_id and ch_id != "__DEAD__"
            ]
            dead_sources = [
                s for s, ch_id in self.fetcher._channel_cache.items()
                if ch_id == "__DEAD__"
            ]

            stats = self.db.get_stats()

            report_lines = [
                "📊 <b>BÁO CÁO HỆ THỐNG TIKTOK BETA US</b> 📊",
                "━━━━━━━━━━━━━━━━━━━━",
                "🖥️ <b>Thiết bị quản lý:</b> 22 Máy",
                f"📱 <b>Kênh TikTok:</b> {len(channels)} kênh (<code>{bkt_count} BKT</code> | <code>{kbkt_count} KBKT</code>)",
                f"📺 <b>Nguồn YouTube:</b> {len(all_sources)} nguồn duy nhất",
                f"   • Hợp lệ & Đang theo dõi: <b>{len(valid_sources)} nguồn</b>",
                f"   • Nguồn lỗi/404 (đã tự bỏ qua): <b>{len(dead_sources)} nguồn</b>",
                "━━━━━━━━━━━━━━━━━━━━",
                f"💾 <b>Cơ sở dữ liệu lưu vết:</b> {stats.get('total_tracked', 0)} video",
                f"   • Đã bắn thông báo: <b>{stats.get('total_sent', 0)} video</b>",
                f"   • Video mốc cơ sở (Seed/Cũ): <b>{stats.get('total_seeded', 0)} video</b>",
                f"   • Video bị lọc (Shorts/Live): <b>{stats.get('total_filtered', 0)} video</b>",
                "━━━━━━━━━━━━━━━━━━━━",
                f"⏳ <b>Chu kỳ tự động:</b> Quét lặp lại mỗi {config.CHECK_INTERVAL_SECONDS // 60} phút",
                "🟢 <b>Trạng thái:</b> Đang chạy và sẵn sàng nhận lệnh!",
            ]

            self.notifier.send_message("\n".join(report_lines), chat_id=chat_id)
        except Exception as e:
            logger.exception(f"Lỗi khi tạo báo cáo status: {e}")
            self.notifier.send_message(f"❌ <b>Lỗi khi tạo báo cáo:</b> <code>{e}</code>", chat_id=chat_id)

    def handle_help_command(self, chat_id: str) -> None:
        """Xử lý lệnh /help, /start hoặc Hướng Dẫn."""
        help_text = (
            "🤖 <b>TIKTOK BETA US NOTIFIER - BẢNG ĐIỀU KHIỂN CHAT</b>\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "Chào bạn! Bạn có thể điều khiển toàn bộ mạng lưới 22 máy thông qua các nút bấm tiện lợi bên dưới:\n\n"
            "🚀 <b>/videos</b> hoặc bấm <code>[ 🚀 Quét Video Mới ]</code>\n"
            "➔ Kích hoạt quét tức thì toàn bộ 22 máy và 102 nguồn YouTube.\n\n"
            "🔄 <b>/update</b> hoặc bấm <code>[ 🔄 Cập Nhật Google Drive ]</code>\n"
            "➔ Tự động tải lại file cấu hình từ Google Sheets và cập nhật danh sách kênh.\n\n"
            "📊 <b>/status</b> hoặc bấm <code>[ 📊 Xem Báo Cáo 22 Máy ]</code>\n"
            "➔ Xem báo cáo chi tiết về số lượng kênh, nguồn video và dữ liệu lưu vết.\n\n"
            "💡 <b>/help</b> hoặc bấm <code>[ 💡 Hướng Dẫn ]</code>\n"
            "➔ Mở lại hướng dẫn này và kích hoạt bàn phím tương tác."
        )
        self.notifier.send_message(
            help_text,
            chat_id=chat_id,
            reply_markup=self.get_reply_keyboard(),
        )

    def process_message(self, message: Dict[str, Any]) -> None:
        """Điều hướng tin nhắn đến handler tương ứng."""
        is_allowed, chat_id, text = self.is_authorized(message)

        if not is_allowed:
            logger.warning(
                f"[BẢO MẬT] Từ chối lệnh từ người dùng không được phép (Chat ID: {chat_id}): '{text}'"
            )
            self.notifier.send_message(
                "⛔ <b>Từ chối truy cập:</b> Tài khoản của bạn không nằm trong danh sách được phép quản lý hệ thống này.",
                chat_id=chat_id,
            )
            return

        cmd = text.strip()
        # Chuẩn hóa để so sánh không phân biệt hoa thường và loại bỏ @bot_username nếu có
        cmd_clean = cmd.split("@")[0].lower() if cmd.startswith("/") else cmd.lower()

        logger.info(f"[TELEGRAM COMMAND] Nhận lệnh từ Chat {chat_id}: '{cmd}'")

        if cmd_clean in ["/videos", "🚀 quét video mới", "quét video mới"]:
            self.handle_videos_command(chat_id)
        elif cmd_clean in ["/update", "🔄 cập nhật google drive", "cập nhật google drive"]:
            self.handle_update_command(chat_id)
        elif cmd_clean in ["/status", "📊 xem báo cáo 22 máy", "xem báo cáo 22 máy"]:
            self.handle_status_command(chat_id)
        elif cmd_clean in ["/help", "/start", "💡 hướng dẫn", "hướng dẫn"]:
            self.handle_help_command(chat_id)
        else:
            self.notifier.send_message(
                f"❓ Lệnh không xác định: <code>{cmd}</code>\n"
                f"Vui lòng bấm các nút trên bàn phím điều khiển hoặc gõ <b>/help</b> để xem hướng dẫn.",
                chat_id=chat_id,
                reply_markup=self.get_reply_keyboard(),
            )

    def poll_once(self) -> None:
        """Thực hiện một lần kiểm tra update."""
        offset = (self.last_update_id + 1) if self.last_update_id else None
        updates = self.notifier.get_updates(offset=offset, timeout=5)

        for update in updates:
            upd_id = update.get("update_id")
            if upd_id is not None:
                self.last_update_id = upd_id
                self._save_last_offset(upd_id)

            msg = update.get("message")
            if msg and "text" in msg:
                try:
                    self.process_message(msg)
                except Exception as e:
                    logger.exception(f"Lỗi khi xử lý message từ update {upd_id}: {e}")

    def start_polling(self) -> None:
        """Vòng lặp lắng nghe lệnh Telegram (chạy chặn)."""
        logger.info("🤖 Bắt đầu lắng nghe lệnh từ Telegram Bot (Long Polling)...")
        self.setup_bot_commands()
        self.is_running = True

        while self.is_running:
            try:
                self.poll_once()
            except Exception as e:
                logger.debug(f"Ngoại lệ trong vòng lặp polling bot: {e}")
                time.sleep(2)

        logger.info("Đã dừng lắng nghe lệnh Telegram Bot.")

    def run_in_background(self) -> threading.Thread:
        """Khởi chạy bot listener trong một daemon thread riêng biệt."""
        self.is_running = True
        self.setup_bot_commands()
        self._poll_thread = threading.Thread(
            target=self.start_polling,
            name="TelegramBotListenerThread",
            daemon=True,
        )
        self._poll_thread.start()
        logger.info("🤖 Luồng Telegram Bot Listener đã được kích hoạt chạy ngầm (Background Thread).")
        return self._poll_thread

    def stop(self) -> None:
        """Dừng lắng nghe bot an toàn."""
        self.is_running = False
