"""
Test suite cho SQLite Database & Core Automation Engine
Kiểm tra tính Idempotent (chống trùng lặp), quét theo Máy và theo Kênh.
"""

import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from src.core.database import TrackingDatabase
from src.core.engine import AutomationEngine
from src.parser.excel_parser import ChannelConfig, ExcelConfigParser
from src.fetcher.youtube_rss import YouTubeVideo, YouTubeFetcher
from src.notifier.telegram_bot import TelegramNotifier


class TestEngineAndDatabase(unittest.TestCase):

    def setUp(self):
        import gc
        gc.collect()
        self.test_db_path = BASE_DIR / "data" / "test_tracked.db"
        if self.test_db_path.exists():
            try:
                self.test_db_path.unlink()
            except PermissionError:
                pass
        self.db = TrackingDatabase(db_path=self.test_db_path)

    def tearDown(self):
        import gc
        self.db = None
        gc.collect()
        if hasattr(self, "test_db_path") and self.test_db_path.exists():
            try:
                self.test_db_path.unlink()
            except PermissionError:
                pass

    def test_database_idempotency(self):
        """Kiểm tra SQLite lưu vết và chống bắn trùng video."""
        vid_id = "test_vid_999"
        tk_channel = "@daily_crime_us"

        # Ban đầu chưa có
        self.assertFalse(self.db.is_tracked(vid_id, tk_channel))

        # Lưu vết
        saved = self.db.mark_as_tracked(
            video_id=vid_id,
            tiktok_channel=tk_channel,
            machine_name="Máy 01",
            channel_id="UC123",
            video_title="Mystery Video 1",
            published_at="2026-11-06T12:00:00Z",
        )
        self.assertTrue(saved)
        self.assertEqual(self.db.get_tracked_count(), 1)

        # Lần sau kiểm tra phải trả về True (đã lưu)
        self.assertTrue(self.db.is_tracked(vid_id, tk_channel))

        # Kênh TikTok khác chưa lưu thì vẫn False
        self.assertFalse(self.db.is_tracked(vid_id, "@other_channel"))

    def test_engine_scan_cycle(self):
        """Kiểm tra chu kỳ quét của Engine và tính chống trùng lặp."""
        # Mock Parser trả về 2 kênh: 1 kênh Máy 01, 1 kênh Máy 02
        mock_parser = MagicMock(spec=ExcelConfigParser)
        mock_ch1 = ChannelConfig(
            machine_name="Máy 01",
            tiktok_channel="@crime_us",
            status_bkt="BKT",
            niche="Crime",
            youtube_sources=["https://youtube.com/@source1"],
        )
        mock_ch2 = ChannelConfig(
            machine_name="Máy 02",
            tiktok_channel="@tech_us",
            status_bkt="KBKT",
            niche="Tech",
            youtube_sources=["https://youtube.com/@source2"],
        )
        mock_parser.get_channels.return_value = [mock_ch1, mock_ch2]

        # Mock Fetcher trả về video
        mock_fetcher = MagicMock(spec=YouTubeFetcher)
        mock_video1 = YouTubeVideo(
            video_id="vid_101",
            channel_id="UC_SRC1",
            channel_title="Source 1",
            title="Video for Crime",
            link="https://youtu.be/vid_101",
            published_at="2026-11-06T10:00:00Z",
            duration_seconds=600,
        )
        mock_fetcher.fetch_channel_videos.return_value = [mock_video1]

        # Mock Notifier
        mock_notifier = MagicMock(spec=TelegramNotifier)
        mock_notifier.send_notification.return_value = True

        engine = AutomationEngine(
            parser=mock_parser,
            fetcher=mock_fetcher,
            notifier=mock_notifier,
            db=self.db,
        )

        # Lần quét 1: Phát hiện video mới cho cả 2 kênh đích
        count1 = engine.scan_once()
        self.assertEqual(count1, 2)
        self.assertEqual(mock_notifier.send_notification.call_count, 2)

        # Lần quét 2 (cùng video đó): Không gửi lại bất kỳ tin nào vì đã lưu vào DB
        count2 = engine.scan_once()
        self.assertEqual(count2, 0)
        self.assertEqual(mock_notifier.send_notification.call_count, 2)  # Không tăng thêm

    def test_seed_mode(self):
        """Kiểm tra chế độ Seed Baseline: Lưu vào DB mà không gửi tin nhắn Telegram."""
        mock_parser = MagicMock(spec=ExcelConfigParser)
        mock_ch = ChannelConfig(
            machine_name="Máy 01",
            tiktok_channel="@crime_us",
            status_bkt="BKT",
            niche="Crime",
            youtube_sources=["https://youtube.com/@source1"],
        )
        mock_parser.get_channels.return_value = [mock_ch]

        mock_fetcher = MagicMock(spec=YouTubeFetcher)
        mock_video = YouTubeVideo(
            video_id="seed_vid_01",
            channel_id="UC_SRC1",
            channel_title="Source 1",
            title="Seed Video",
            link="https://youtu.be/seed_vid_01",
            published_at="2026-11-06T10:00:00Z",
            duration_seconds=600,
        )
        mock_fetcher.fetch_channel_videos.return_value = [mock_video]

        mock_notifier = MagicMock(spec=TelegramNotifier)

        engine = AutomationEngine(
            parser=mock_parser,
            fetcher=mock_fetcher,
            notifier=mock_notifier,
            db=self.db,
        )

        # Chạy seed mode
        count = engine.scan_once(seed_mode=True)
        self.assertEqual(count, 1)
        # Không được gọi Telegram notifier!
        self.assertEqual(mock_notifier.send_notification.call_count, 0)
        # Đã lưu vào database
        self.assertTrue(self.db.is_tracked("seed_vid_01", "@crime_us"))

        stats = self.db.get_stats()
        self.assertEqual(stats["total_seeded"], 1)
        self.assertEqual(stats["total_sent"], 0)


if __name__ == "__main__":
    unittest.main()
