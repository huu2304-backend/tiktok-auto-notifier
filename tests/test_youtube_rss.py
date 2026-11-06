"""
Test suite cho YouTube RSS Fetcher
Kiểm tra khả năng phân giải channel_id, đọc RSS và lọc Shorts.
"""

import sys
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from src.fetcher.youtube_rss import YouTubeFetcher, YouTubeVideo


class TestYouTubeFetcher(unittest.TestCase):

    def setUp(self):
        # Dùng file cache tạm trong scratch/tests
        self.test_cache = BASE_DIR / "data" / "test_channel_cache.json"
        self.fetcher = YouTubeFetcher(cache_file=self.test_cache)

    def tearDown(self):
        if self.test_cache.exists():
            self.test_cache.unlink()

    def test_direct_channel_id(self):
        """Nếu truyền sẵn UC... thì trả về ngay không cần request mạng."""
        sample_id = "UC-lHJZR3Gqxm24_Vd_AJ5Yw"
        res = self.fetcher.resolve_channel_id(sample_id)
        self.assertEqual(res, sample_id)

    def test_cache_mechanism(self):
        """Kiểm tra cơ chế lưu và nạp cache."""
        self.fetcher._channel_cache["@test_channel"] = "UC1234567890123456789012"
        self.fetcher._save_cache()

        # Tạo fetcher mới nạp cùng file cache
        new_fetcher = YouTubeFetcher(cache_file=self.test_cache)
        resolved = new_fetcher.resolve_channel_id("@test_channel")
        self.assertEqual(resolved, "UC1234567890123456789012")

    @patch("src.fetcher.youtube_rss.requests.Session.head")
    def test_shorts_detection(self, mock_head):
        """Kiểm tra logic phân biệt Shorts qua mã HTTP status code."""
        # 1. Video Shorts: YouTube trả về HTTP 200
        mock_head.return_value.status_code = 200
        self.assertTrue(self.fetcher.is_youtube_short("short_vid_id"))

        # 2. Video Thường: YouTube trả về 303 Redirect sang /watch
        mock_head.return_value.status_code = 303
        mock_head.return_value.headers = {"Location": "https://www.youtube.com/watch?v=normal_vid_id"}
        self.assertFalse(self.fetcher.is_youtube_short("normal_vid_id"))

    @patch("src.fetcher.youtube_rss.feedparser.parse")
    @patch.object(YouTubeFetcher, "resolve_channel_id")
    def test_fetch_channel_videos(self, mock_resolve, mock_parse):
        """Kiểm tra bóc tách RSS feed và lọc video."""
        mock_resolve.return_value = "UC1234567890123456789012"

        # Mock RSS entry
        mock_feed = MagicMock()
        mock_feed.bozo = False
        mock_feed.feed = {"title": "Test Channel"}
        mock_feed.entries = [
            {
                "yt_videoid": "vid_01",
                "title": "Full Mystery Documentary 2026",
                "link": "https://www.youtube.com/watch?v=vid_01",
                "published": "2026-11-06T12:00:00Z",
                "media_thumbnail": [{"url": "https://img.youtube.com/vi/vid_01/0.jpg"}],
                "media_description": "A long video for TikTok Beta",
            },
            {
                "yt_videoid": "vid_02",
                "title": "Funny moments #shorts",
                "link": "https://www.youtube.com/watch?v=vid_02",
                "published": "2026-11-06T14:00:00Z",
                "media_thumbnail": [],
                "media_description": "Shorts video",
            },
        ]
        mock_parse.return_value = mock_feed

        # Mock duration cho video dài
        with patch.object(self.fetcher, "get_video_duration", return_value=600):
            with patch.object(self.fetcher, "is_youtube_short", return_value=False):
                videos = self.fetcher.fetch_channel_videos("@test_channel", filter_shorts=True, min_duration=180)

        # Chỉ vid_01 vượt qua, vid_02 bị loại vì có tag #shorts
        self.assertEqual(len(videos), 1)
        self.assertEqual(videos[0].video_id, "vid_01")
        self.assertEqual(videos[0].title, "Full Mystery Documentary 2026")
        self.assertEqual(videos[0].duration_formatted, "10 phút 0 giây")


if __name__ == "__main__":
    unittest.main()
