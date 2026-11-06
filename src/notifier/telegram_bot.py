"""
TikTok Beta US Automation Notifier - Telegram Bot Notifier
==========================================================
Bắn thông báo video mới về Telegram theo chuẩn HTML format.
Gắn liền định danh: Máy ➔ Kênh TikTok (BKT/KBKT) ➔ Chủ đề ➔ Nguồn YouTube.
"""

import html
import time
from typing import Optional, Dict, Any, Tuple
import requests

from config.settings import logger, config
from src.parser.excel_parser import ChannelConfig
from src.fetcher.youtube_rss import YouTubeVideo


class TelegramNotifier:
    """
    Client gửi thông báo qua Telegram Bot API.
    Hỗ trợ gửi tin nhắn văn bản, gửi kèm thumbnail và hỗ trợ Supergroup Topics (Forum).
    """

    API_BASE = "https://api.telegram.org/bot{token}"

    def __init__(
        self,
        bot_token: Optional[str] = None,
        chat_id: Optional[str] = None,
        thread_id: Optional[str] = None,
    ):
        self.bot_token = (bot_token or config.TELEGRAM_BOT_TOKEN).strip()
        self.chat_id = (chat_id or config.TELEGRAM_CHAT_ID).strip()
        self.thread_id = (thread_id or config.TELEGRAM_MESSAGE_THREAD_ID).strip()
        self.session = requests.Session()

    @property
    def is_configured(self) -> bool:
        """Kiểm tra token và chat id có sẵn sàng không."""
        return bool(self.bot_token and self.chat_id)

    def test_connection(self) -> Tuple[bool, str]:
        """Kiểm tra kết nối và tính hợp lệ của Bot Token."""
        if not self.is_configured:
            return False, "Thiếu TELEGRAM_BOT_TOKEN hoặc TELEGRAM_CHAT_ID trong cấu hình (.env)."

        url = f"{self.API_BASE.format(token=self.bot_token)}/getMe"
        try:
            resp = self.session.get(url, timeout=config.REQUEST_TIMEOUT)
            data = resp.json()
            if data.get("ok"):
                bot_user = data.get("result", {}).get("username", "Unknown")
                return True, f"Kết nối bot thành công (@{bot_user})!"
            return False, f"Lỗi từ Telegram: {data.get('description')}"
        except Exception as e:
            return False, f"Lỗi kết nối tới Telegram: {e}"

    def format_notification(
        self,
        video: YouTubeVideo,
        channel_cfg: ChannelConfig,
    ) -> str:
        """
        Định dạng nội dung tin nhắn HTML chuẩn nhận diện Máy - Kênh TikTok - Nguồn YouTube.
        """
        # Trạng thái BKT
        status_badge = "✅ BKT" if channel_cfg.is_bkt() else "⏳ KBKT"

        # Escape các ký tự đặc biệt trong dữ liệu người dùng
        safe_machine = html.escape(channel_cfg.machine_name)
        safe_tiktok = html.escape(channel_cfg.tiktok_channel)
        safe_niche = html.escape(channel_cfg.niche)
        safe_yt_channel = html.escape(video.channel_title)
        safe_title = html.escape(video.title)
        safe_duration = html.escape(video.duration_formatted)
        safe_pub = html.escape(video.published_at)

        # Template HTML chuẩn production
        msg_lines = [
            "🚨 <b>[VIDEO MỚI PHÁT HIỆN]</b> 🚨",
            "━━━━━━━━━━━━━━━━━━━━",
            f"🖥️ <b>Thiết bị:</b> <code>{safe_machine}</code>",
            f"📱 <b>Kênh TikTok:</b> <b>{safe_tiktok}</b> [{status_badge}]",
            f"🎯 <b>Cụm chủ đề:</b> {safe_niche}",
            "━━━━━━━━━━━━━━━━━━━━",
            f"📺 <b>Nguồn YouTube:</b> {safe_yt_channel}",
            f"🎬 <b>Tiêu đề:</b> {safe_title}",
            f"⏱️ <b>Thời lượng:</b> {safe_duration}",
            f"⏰ <b>Thời gian đăng:</b> {safe_pub}",
            f"🔗 <b>Xem ngay:</b> <a href=\"{video.link}\">Bấm vào đây để mở video</a>",
            "━━━━━━━━━━━━━━━━━━━━",
            f"💡 <i>Gợi ý: Mở <b>{safe_machine}</b> để lấy tư liệu dựng video TikTok Beta ngay!</i>",
        ]

        if channel_cfg.note:
            msg_lines.append(f"📝 <i>Ghi chú: {html.escape(channel_cfg.note)}</i>")

        return "\n".join(msg_lines)

    def send_notification(
        self,
        video: YouTubeVideo,
        channel_cfg: ChannelConfig,
        send_photo: bool = True,
    ) -> bool:
        """
        Gửi thông báo video mới về Telegram.
        Nếu có ảnh thumbnail và bật send_photo thì gửi dạng Photo + Caption.
        """
        message_text = self.format_notification(video, channel_cfg)

        if not self.is_configured:
            logger.warning(
                f"[DRY-RUN - Chưa cấu hình Bot] Thông báo cho {channel_cfg.display_tag}:\n{message_text}"
            )
            return True

        # 1. Thử gửi kèm ảnh Thumbnail nếu có
        if send_photo and video.thumbnail_url:
            photo_url = f"{self.API_BASE.format(token=self.bot_token)}/sendPhoto"
            payload: Dict[str, Any] = {
                "chat_id": self.chat_id,
                "photo": video.thumbnail_url,
                "caption": message_text,
                "parse_mode": "HTML",
            }
            if self.thread_id:
                payload["message_thread_id"] = self.thread_id

            try:
                resp = self.session.post(photo_url, data=payload, timeout=config.REQUEST_TIMEOUT)
                data = resp.json()
                if data.get("ok"):
                    logger.info(
                        f"Đã gửi thông báo Telegram (Photo) thành công tới {channel_cfg.display_tag} cho video: {video.video_id}"
                    )
                    return True
                logger.warning(f"Gửi photo thất bại ({data.get('description')}), chuyển sang gửi text.")
            except Exception as e:
                logger.warning(f"Lỗi khi gửi photo qua Telegram: {e}. Thử fallback gửi text...")

        # 2. Fallback gửi text qua sendMessage
        send_url = f"{self.API_BASE.format(token=self.bot_token)}/sendMessage"
        payload = {
            "chat_id": self.chat_id,
            "text": message_text,
            "parse_mode": "HTML",
            "disable_web_page_preview": False,
        }
        if self.thread_id:
            payload["message_thread_id"] = self.thread_id

        for attempt in range(1, config.MAX_RETRIES + 1):
            try:
                resp = self.session.post(send_url, data=payload, timeout=config.REQUEST_TIMEOUT)
                data = resp.json()
                if data.get("ok"):
                    logger.info(
                        f"Đã gửi thông báo Telegram (Text) thành công tới {channel_cfg.display_tag} cho video: {video.video_id}"
                    )
                    return True
                logger.error(f"Telegram API trả về lỗi: {data.get('description')} (Lần thử {attempt})")
            except Exception as e:
                logger.exception(f"Lỗi khi gọi API Telegram (Lần {attempt}/{config.MAX_RETRIES}): {e}")

            time.sleep(1.5)

        return False
