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

from src.fetcher.youtube_rss import (
    YouTubeFetcher,
    YouTubeVideo,
    parse_relative_time_to_iso,
    parse_duration_str_to_seconds,
)


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

        # Mock inspect_video_details cho video dài
        with patch.object(self.fetcher, "inspect_video_details", return_value=(600, False)):
            with patch.object(self.fetcher, "is_youtube_short", return_value=False):
                with patch.object(self.fetcher, "fetch_channel_tab_videos", return_value=[]):
                    videos = self.fetcher.fetch_channel_videos("@test_channel", filter_shorts=True, min_duration=180)

        # Chỉ vid_01 vượt qua, vid_02 bị loại vì có tag #shorts
        self.assertEqual(len(videos), 1)
        self.assertEqual(videos[0].video_id, "vid_01")
        self.assertEqual(videos[0].title, "Full Mystery Documentary 2026")
        self.assertEqual(videos[0].duration_formatted, "10 phút 0 giây")

    @patch("src.fetcher.youtube_rss.feedparser.parse")
    @patch.object(YouTubeFetcher, "resolve_channel_id")
    def test_filter_livestream(self, mock_resolve, mock_parse):
        """Kiểm tra loại bỏ video livestream."""
        mock_resolve.return_value = "UC1234567890123456789012"
        mock_feed = MagicMock()
        mock_feed.bozo = False
        mock_feed.feed = {"title": "Test Channel"}
        mock_feed.entries = [
            {
                "yt_videoid": "live_01",
                "title": "Chém gió cuối tuần [LIVESTREAM]",
                "link": "https://www.youtube.com/watch?v=live_01",
                "published": "2026-11-06T12:00:00Z",
                "media_thumbnail": [],
                "media_description": "Đang phát trực tiếp",
            },
            {
                "yt_videoid": "vid_02",
                "title": "Video Dài Thật Sự",
                "link": "https://www.youtube.com/watch?v=vid_02",
                "published": "2026-11-06T13:00:00Z",
                "media_thumbnail": [],
                "media_description": "Video biên tập",
            },
        ]
        mock_parse.return_value = mock_feed

        with patch.object(self.fetcher, "is_youtube_short", return_value=False):
            with patch.object(self.fetcher, "fetch_channel_tab_videos", return_value=[]):
                # vid_02 trả về không phải live, live_01 trả về is_live=True
                def mock_inspect(vid_id, title="", desc=""):
                    if vid_id == "live_01":
                        return 0, True
                    return 450, False

                with patch.object(self.fetcher, "inspect_video_details", side_effect=mock_inspect):
                    videos = self.fetcher.fetch_channel_videos("@test_channel", filter_livestreams=True)

        self.assertEqual(len(videos), 1)
        self.assertEqual(videos[0].video_id, "vid_02")
        self.assertFalse(videos[0].is_live)

    @patch("src.fetcher.youtube_rss.requests.Session.get")
    def test_dead_channel_negative_cache(self, mock_get):
        """Kiểm tra nguồn 404 được lưu vào negative cache (__DEAD__) và bỏ qua ở lần sau."""
        mock_get.return_value.status_code = 404

        # Lần 1: gọi resolve_channel_id, gặp 404
        res1 = self.fetcher.resolve_channel_id("@dead_channel")
        self.assertIsNone(res1)
        self.assertEqual(self.fetcher._channel_cache.get("@dead_channel"), "__DEAD__")
        self.assertEqual(mock_get.call_count, 1)

        # Lần 2: gọi lại, phải lấy từ negative cache và KHÔNG gọi thêm request mạng nào
        res2 = self.fetcher.resolve_channel_id("@dead_channel")
        self.assertIsNone(res2)
        self.assertEqual(mock_get.call_count, 1)

    def test_parse_relative_time_to_iso(self):
        """Kiểm tra quy đổi các mốc thời gian tương đối sang ISO 8601 hỗ trợ cả Anh và Việt."""
        iso_min, dt_min = parse_relative_time_to_iso("18 min ago")
        self.assertIsNotNone(dt_min)
        self.assertIn("T", iso_min)

        iso_hr, dt_hr = parse_relative_time_to_iso("2 hours ago")
        self.assertIsNotNone(dt_hr)

        iso_day, dt_day = parse_relative_time_to_iso("3 days ago")
        self.assertIsNotNone(dt_day)

        iso_mo, dt_mo = parse_relative_time_to_iso("1mo ago")
        self.assertIsNotNone(dt_mo)

        # Tiếng Việt
        iso_vi_min, dt_vi_min = parse_relative_time_to_iso("30 phút trước")
        self.assertIsNotNone(dt_vi_min)

        iso_vi_hr, dt_vi_hr = parse_relative_time_to_iso("2 giờ trước")
        self.assertIsNotNone(dt_vi_hr)

        # Chuỗi rỗng hoặc không xác định phải trả về None để không bắn tin cũ
        iso_empty, dt_empty = parse_relative_time_to_iso("")
        self.assertIsNone(iso_empty)
        self.assertIsNone(dt_empty)

        # Kiểm tra age_hours với published_dt=None
        dummy_vid = YouTubeVideo(
            video_id="dummy123",
            channel_id="UC123",
            channel_title="Dummy",
            title="Old Video Without Date",
            link="https://www.youtube.com/watch?v=dummy123",
            published_at="",
            published_dt=None,
        )
        self.assertGreater(dummy_vid.age_hours, 24.0)

    def test_parse_duration_str_to_seconds(self):
        """Kiểm tra parse thời lượng định dạng MM:SS hoặc HH:MM:SS."""
        self.assertEqual(parse_duration_str_to_seconds("27:15"), 1635)
        self.assertEqual(parse_duration_str_to_seconds("1:05:30"), 3930)
        self.assertEqual(parse_duration_str_to_seconds("0:45"), 45)
        self.assertEqual(parse_duration_str_to_seconds(""), 0)

    def test_build_channel_videos_url(self):
        """Kiểm tra chuẩn hóa URL tab /videos từ nhiều định dạng đầu vào."""
        self.assertEqual(
            self.fetcher.build_channel_videos_url("https://www.youtube.com/@NickDiGiovanni"),
            "https://www.youtube.com/@NickDiGiovanni/videos",
        )
        self.assertEqual(
            self.fetcher.build_channel_videos_url("https://www.youtube.com/@NickDiGiovanni/videos"),
            "https://www.youtube.com/@NickDiGiovanni/videos",
        )
        self.assertEqual(
            self.fetcher.build_channel_videos_url("@MrBallen"),
            "https://www.youtube.com/@MrBallen/videos",
        )
        self.assertEqual(
            self.fetcher.build_channel_videos_url("UC1234567890123456789012"),
            "https://www.youtube.com/channel/UC1234567890123456789012/videos",
        )

    @patch("src.fetcher.youtube_rss.requests.Session.get")
    def test_fetch_channel_tab_videos_lockup(self, mock_get):
        """Kiểm tra bóc tách cấu trúc lockupViewModel từ tab /videos."""
        mock_html = """
        <html><head><meta property="og:title" content="Nick DiGiovanni"></head>
        <body>
        <script>
        var ytInitialData = {
            "contents": {
                "twoColumnBrowseResultsRenderer": {
                    "tabs": [{
                        "tabRenderer": {
                            "content": {
                                "richGridRenderer": {
                                    "contents": [{
                                        "richItemRenderer": {
                                            "content": {
                                                "lockupViewModel": {
                                                    "contentId": "9ZqdgmaO6gM",
                                                    "metadata": {
                                                        "lockupMetadataViewModel": {
                                                            "title": {"content": "$1 vs $10,000 Cooking Challenge"},
                                                            "metadata": {
                                                                "contentMetadataViewModel": {
                                                                    "metadataRows": [{
                                                                        "metadataParts": [{"text": {"content": "20 min ago"}}]
                                                                    }]
                                                                }
                                                            }
                                                        }
                                                    },
                                                    "contentImage": {
                                                        "thumbnailViewModel": {
                                                            "overlays": [{
                                                                "thumbnailBottomOverlayViewModel": {
                                                                    "badges": [{"thumbnailBadgeViewModel": {"text": "27:15"}}]
                                                                }
                                                            }]
                                                        }
                                                    }
                                                }
                                            }
                                        }
                                    }]
                                }
                            }
                        }
                    }]
                }
            }
        };
        </script>
        </body></html>
        """
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.text = mock_html
        mock_get.return_value = mock_resp

        with patch.object(self.fetcher, "resolve_channel_id", return_value="UCMyOj6fhvKFMjxUCp3b_3gA"):
            videos = self.fetcher.fetch_channel_tab_videos("https://www.youtube.com/@NickDiGiovanni")

        self.assertEqual(len(videos), 1)
        self.assertEqual(videos[0].video_id, "9ZqdgmaO6gM")
        self.assertEqual(videos[0].title, "$1 vs $10,000 Cooking Challenge")
        self.assertEqual(videos[0].duration_seconds, 1635)
        self.assertEqual(videos[0].channel_id, "UCMyOj6fhvKFMjxUCp3b_3gA")

    def test_fetch_dual_videos_merges_properly(self):
        """Kiểm tra cơ chế Quét Kép gộp dữ liệu từ cả Tab /videos và RSS mà không trùng lặp."""
        v_tab = YouTubeVideo(
            video_id="vid_tab_01",
            channel_id="UC123",
            channel_title="Test",
            title="Brand New Realtime Video",
            link="https://youtube.com/watch?v=vid_tab_01",
            published_at="2026-11-08T00:00:00Z",
            duration_seconds=500,
        )
        v_rss = YouTubeVideo(
            video_id="vid_rss_02",
            channel_id="UC123",
            channel_title="Test",
            title="Older RSS Video",
            link="https://youtube.com/watch?v=vid_rss_02",
            published_at="2026-11-07T12:00:00Z",
            duration_seconds=600,
        )

        with patch.object(self.fetcher, "fetch_channel_tab_videos", return_value=[v_tab]):
            with patch.object(self.fetcher, "fetch_raw_rss_entries", return_value=[v_rss]):
                dual = self.fetcher.fetch_dual_videos("@test")

        self.assertEqual(len(dual), 2)
        ids = [v.video_id for v in dual]
        self.assertIn("vid_tab_01", ids)
        self.assertIn("vid_rss_02", ids)


if __name__ == "__main__":
    unittest.main()
