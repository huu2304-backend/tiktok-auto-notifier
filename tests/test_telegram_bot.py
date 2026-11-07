"""
Test suite cho Telegram Bot Notifier
Kiểm tra format thông báo, xử lý escape HTML và gửi tin nhắn.
"""

import sys
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from src.parser.excel_parser import ChannelConfig
from src.fetcher.youtube_rss import YouTubeVideo
from src.notifier.telegram_bot import TelegramNotifier


class TestTelegramNotifier(unittest.TestCase):

    def setUp(self):
        self.notifier = TelegramNotifier(
            bot_token="mock_bot_token",
            chat_id="mock_chat_id",
            thread_id="123",
        )
        self.sample_cfg = ChannelConfig(
            machine_name="Máy 01",
            tiktok_channel="@daily_crime_us",
            status_bkt="BKT",
            niche="True Crime & Vụ Án",
            youtube_sources=["https://youtube.com/@MrBallen"],
            note="Ưu tiên làm sớm",
        )
        self.sample_video = YouTubeVideo(
            video_id="xyz123abc",
            channel_id="UC12345",
            channel_title="MrBallen <Official>",
            title="3 Scary Stories <True Story>",
            link="https://www.youtube.com/watch?v=xyz123abc",
            published_at="2026-11-06T18:00:00Z",
            duration_seconds=900,
            thumbnail_url="https://img.youtube.com/vi/xyz123abc/0.jpg",
        )

    def test_message_formatting(self):
        """Kiểm tra nội dung tin nhắn và escape ký tự nhạy cảm HTML."""
        msg = self.notifier.format_notification(self.sample_video, self.sample_cfg)

        # Kiểm tra đầy đủ thông tin nhận diện
        self.assertIn("Máy 01", msg)
        self.assertIn("@daily_crime_us", msg)
        self.assertIn("✅ BKT", msg)
        self.assertIn("True Crime &amp; Vụ Án", msg)  # & được escape thành &amp;
        self.assertIn("MrBallen &lt;Official&gt;", msg)  # < > được escape
        self.assertIn("3 Scary Stories &lt;True Story&gt;", msg)
        self.assertIn("15 phút 0 giây", msg)
        self.assertIn("https://www.youtube.com/watch?v=xyz123abc", msg)
        self.assertIn("01:00 07/11/2026", msg)  # Giờ Việt Nam GMT+7
        self.assertIn("Ưu tiên làm sớm", msg)

    @patch("src.notifier.telegram_bot.requests.Session.post")
    def test_send_notification_success(self, mock_post):
        """Kiểm tra gọi API Telegram thành công."""
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"ok": True}
        mock_post.return_value = mock_resp

        success = self.notifier.send_notification(self.sample_video, self.sample_cfg)
        self.assertTrue(success)
        self.assertTrue(mock_post.called)

    @patch("src.notifier.telegram_bot.requests.Session.post")
    def test_send_message_with_reply_markup(self, mock_post):
        """Kiểm tra gửi tin nhắn text kèm bàn phím tùy biến."""
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"ok": True}
        mock_post.return_value = mock_resp

        keyboard = {
            "keyboard": [[{"text": "🚀 Quét Video Mới"}]],
            "resize_keyboard": True,
        }
        success = self.notifier.send_message("Xin chào", reply_markup=keyboard)
        self.assertTrue(success)
        call_kwargs = mock_post.call_args[1]
        self.assertEqual(call_kwargs["json"]["text"], "Xin chào")
        self.assertEqual(call_kwargs["json"]["reply_markup"], keyboard)

    @patch("src.notifier.telegram_bot.requests.Session.post")
    def test_set_bot_commands(self, mock_post):
        """Kiểm tra đăng ký slash commands với menu bot."""
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"ok": True}
        mock_post.return_value = mock_resp

        commands = [{"command": "videos", "description": "Quét video"}]
        success = self.notifier.set_bot_commands(commands)
        self.assertTrue(success)
        call_kwargs = mock_post.call_args[1]
        self.assertEqual(call_kwargs["json"]["commands"], commands)

    @patch("src.notifier.telegram_bot.requests.Session.get")
    def test_get_updates(self, mock_get):
        """Kiểm tra lấy updates qua getUpdates."""
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "ok": True,
            "result": [{"update_id": 100, "message": {"text": "/videos"}}],
        }
        mock_get.return_value = mock_resp

        updates = self.notifier.get_updates(offset=100)
        self.assertEqual(len(updates), 1)
        self.assertEqual(updates[0]["update_id"], 100)


if __name__ == "__main__":
    unittest.main()
