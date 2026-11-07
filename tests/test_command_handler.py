"""
Test suite cho TelegramCommandHandler
Kiểm tra xử lý lệnh /videos, /update, /status, /help, whitelist bảo mật và bàn phím.
"""

import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from src.bot.command_handler import TelegramCommandHandler
from src.parser.excel_parser import ChannelConfig


class TestTelegramCommandHandler(unittest.TestCase):

    def setUp(self):
        self.mock_engine = MagicMock()
        self.mock_notifier = MagicMock()
        self.mock_parser = MagicMock()
        self.mock_fetcher = MagicMock()
        self.mock_db = MagicMock()
        self.mock_syncer = MagicMock()

        self.handler = TelegramCommandHandler(
            engine=self.mock_engine,
            notifier=self.mock_notifier,
            parser=self.mock_parser,
            fetcher=self.mock_fetcher,
            db=self.mock_db,
            syncer=self.mock_syncer,
        )

    def test_reply_keyboard_structure(self):
        """Kiểm tra cấu trúc bàn phím Reply Keyboard đầy đủ 4 nút."""
        kb = self.handler.get_reply_keyboard()
        self.assertIn("keyboard", kb)
        self.assertTrue(kb.get("resize_keyboard"))
        buttons = [btn["text"] for row in kb["keyboard"] for btn in row]
        self.assertIn("🚀 Quét Video Mới", buttons)
        self.assertIn("🔄 Cập Nhật Google Drive", buttons)
        self.assertIn("📊 Xem Báo Cáo 22 Máy", buttons)
        self.assertIn("💡 Hướng Dẫn", buttons)

    @patch("src.bot.command_handler.config")
    def test_whitelist_authorized(self, mock_config):
        """Kiểm tra tài khoản hợp lệ trong whitelist."""
        mock_config.TELEGRAM_CHAT_ID = "6748670298"
        msg = {
            "chat": {"id": 6748670298},
            "from": {"id": 6748670298},
            "text": "/videos",
        }
        allowed, chat_id, text = self.handler.is_authorized(msg)
        self.assertTrue(allowed)
        self.assertEqual(chat_id, "6748670298")
        self.assertEqual(text, "/videos")

    @patch("src.bot.command_handler.config")
    def test_whitelist_unauthorized_rejected(self, mock_config):
        """Kiểm tra từ chối truy cập từ người lạ ngoài whitelist."""
        mock_config.TELEGRAM_CHAT_ID = "6748670298"
        msg = {
            "chat": {"id": 999999999},
            "from": {"id": 999999999},
            "text": "/videos",
        }
        allowed, chat_id, text = self.handler.is_authorized(msg)
        self.assertFalse(allowed)

        # Xử lý tin nhắn phải gửi cảnh báo từ chối
        self.handler.process_message(msg)
        self.mock_notifier.send_message.assert_called_with(
            "⛔ <b>Từ chối truy cập:</b> Tài khoản của bạn không nằm trong danh sách được phép quản lý hệ thống này.",
            chat_id="999999999",
        )
        self.mock_engine.scan_once.assert_not_called()

    @patch("src.bot.command_handler.config")
    def test_handle_videos_command_success(self, mock_config):
        """Kiểm tra xử lý lệnh /videos khi có video mới."""
        mock_config.TELEGRAM_CHAT_ID = "6748670298"
        self.mock_engine.is_scanning = False
        self.mock_engine.scan_once.return_value = 3

        msg = {
            "chat": {"id": 6748670298},
            "from": {"id": 6748670298},
            "text": "/videos",
        }
        self.handler.process_message(msg)

        self.mock_engine.scan_once.assert_called_once()
        # Phải gửi ít nhất 2 tin nhắn: tin báo đang quét và tin hoàn tất
        self.assertGreaterEqual(self.mock_notifier.send_message.call_count, 2)
        last_call_args = self.mock_notifier.send_message.call_args[0][0]
        self.assertIn("3 video mới", last_call_args)

    @patch("src.bot.command_handler.config")
    def test_handle_videos_button_click(self, mock_config):
        """Kiểm tra bấm nút [ 🚀 Quét Video Mới ] thay vì gõ /videos."""
        mock_config.TELEGRAM_CHAT_ID = "6748670298"
        self.mock_engine.is_scanning = False
        self.mock_engine.scan_once.return_value = 0

        msg = {
            "chat": {"id": 6748670298},
            "from": {"id": 6748670298},
            "text": "🚀 Quét Video Mới",
        }
        self.handler.process_message(msg)

        self.mock_engine.scan_once.assert_called_once()
        last_call_args = self.mock_notifier.send_message.call_args[0][0]
        self.assertIn("Tất cả 22 máy đều đã cập nhật", last_call_args)

    @patch("src.bot.command_handler.config")
    def test_handle_videos_when_busy(self, mock_config):
        """Kiểm tra thông báo khi hệ thống đang quét bận."""
        mock_config.TELEGRAM_CHAT_ID = "6748670298"
        self.mock_engine.is_scanning = True

        msg = {
            "chat": {"id": 6748670298},
            "from": {"id": 6748670298},
            "text": "/videos",
        }
        self.handler.process_message(msg)

        self.mock_engine.scan_once.assert_not_called()
        call_text = self.mock_notifier.send_message.call_args[0][0]
        self.assertIn("đang trong tiến trình quét", call_text)

    @patch("src.bot.command_handler.config")
    def test_handle_update_command(self, mock_config):
        """Kiểm tra xử lý lệnh /update đồng bộ Google Drive."""
        mock_config.TELEGRAM_CHAT_ID = "6748670298"
        mock_config.GOOGLE_SHEET_URL = "https://docs.google.com/test"
        self.mock_syncer.sync.return_value = (True, "Đã tải 22 dòng", 22)
        self.mock_fetcher._channel_cache = {
            "https://bad.url": "__DEAD__",
            "https://good.url": "UC123",
        }
        self.mock_parser.get_channels.return_value = [
            ChannelConfig(machine_name="Máy 01", tiktok_channel="@test", status_bkt="BKT", niche="n", youtube_sources=[])
        ]

        msg = {
            "chat": {"id": 6748670298},
            "from": {"id": 6748670298},
            "text": "/update",
        }
        self.handler.process_message(msg)

        self.mock_syncer.sync.assert_called_with("https://docs.google.com/test")
        self.assertNotIn("https://bad.url", self.mock_fetcher._channel_cache)
        self.mock_fetcher._save_cache.assert_called_once()
        last_call_args = self.mock_notifier.send_message.call_args[0][0]
        self.assertIn("Đồng bộ Google Drive thành công", last_call_args)

    @patch("src.bot.command_handler.config")
    def test_handle_status_command(self, mock_config):
        """Kiểm tra xử lý lệnh /status báo cáo 22 máy."""
        mock_config.TELEGRAM_CHAT_ID = "6748670298"
        mock_config.CHECK_INTERVAL_SECONDS = 300
        self.mock_parser.get_channels.return_value = [
            ChannelConfig(machine_name="Máy 01", tiktok_channel="@bkt_1", status_bkt="BKT", niche="Crime", youtube_sources=["s1"]),
            ChannelConfig(machine_name="Máy 02", tiktok_channel="@kbkt_1", status_bkt="KBKT", niche="Tech", youtube_sources=["s2"]),
        ]
        self.mock_fetcher._channel_cache = {"s1": "UC1", "s2": "UC2", "dead": "__DEAD__"}
        self.mock_db.get_stats.return_value = {
            "total_tracked": 100,
            "total_sent": 20,
            "total_seeded": 80,
            "total_filtered": 5,
        }

        msg = {
            "chat": {"id": 6748670298},
            "from": {"id": 6748670298},
            "text": "📊 Xem Báo Cáo 22 Máy",
        }
        self.handler.process_message(msg)

        call_text = self.mock_notifier.send_message.call_args[0][0]
        self.assertIn("BÁO CÁO HỆ THỐNG TIKTOK BETA US", call_text)
        self.assertIn("2 kênh", call_text)
        self.assertIn("1 BKT", call_text)
        self.assertIn("100 video", call_text)

    @patch("src.bot.command_handler.config")
    def test_handle_help_command(self, mock_config):
        """Kiểm tra lệnh /help gửi kèm bàn phím điều khiển."""
        mock_config.TELEGRAM_CHAT_ID = "6748670298"
        msg = {
            "chat": {"id": 6748670298},
            "from": {"id": 6748670298},
            "text": "/help",
        }
        self.handler.process_message(msg)

        kwargs = self.mock_notifier.send_message.call_args[1]
        self.assertIn("reply_markup", kwargs)
        self.assertIn("keyboard", kwargs["reply_markup"])


if __name__ == "__main__":
    unittest.main()
