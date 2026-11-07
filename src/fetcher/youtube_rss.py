"""
TikTok Beta US Automation Notifier - YouTube RSS Fetcher
========================================================
Quét video mới từ YouTube RSS không giới hạn quota API.
Tự động phân giải @handle sang channel_id, phát hiện và loại bỏ Shorts,
lọc thời lượng video theo chuẩn TikTok Creator Rewards Program (Beta US).
"""

import re
import json
import html
from pathlib import Path
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Tuple, Any
import requests
import feedparser

from config.settings import logger, config


@dataclass
class YouTubeVideo:
    """Đối tượng lưu trữ thông tin video YouTube đã bóc tách."""

    video_id: str
    channel_id: str
    channel_title: str
    title: str
    link: str
    published_at: str
    published_dt: Optional[datetime] = None
    duration_seconds: int = 0
    is_short: bool = False
    is_live: bool = False
    thumbnail_url: str = ""
    description: str = ""

    def __post_init__(self):
        """Tự động phân giải published_dt nếu published_at có giá trị ISO hợp lệ."""
        if not self.published_dt and self.published_at:
            try:
                clean_iso = self.published_at.replace("Z", "+00:00")
                self.published_dt = datetime.fromisoformat(clean_iso)
                if self.published_dt.tzinfo is None:
                    self.published_dt = self.published_dt.replace(tzinfo=timezone.utc)
            except Exception:
                pass

    @property
    def duration_formatted(self) -> str:
        """Định dạng thời lượng dễ đọc: ví dụ '14 phút 25 giây'"""
        if self.duration_seconds <= 0:
            return "Chưa rõ"
        m, s = divmod(self.duration_seconds, 60)
        h, m = divmod(m, 60)
        if h > 0:
            return f"{h}h {m}m {s}s"
        return f"{m} phút {s} giây"

    @property
    def age_hours(self) -> float:
        """
        Tính tuổi của video tính theo giờ so với thời điểm hiện tại.
        Nếu video không rõ thời điểm đăng (published_dt is None), trả về 999999.0 giờ (coi như video cũ)
        để tuyệt đối không bao giờ thông báo nhầm các video cũ.
        """
        if not self.published_dt:
            return 999999.0
        now = datetime.now(timezone.utc)
        return max(0.0, (now - self.published_dt).total_seconds() / 3600.0)


def parse_relative_time_to_iso(rel_text: Optional[str]) -> Tuple[Optional[str], Optional[datetime]]:
    """
    Chuyển chuỗi thời gian tương đối sang chuỗi ISO 8601 UTC và đối tượng datetime timezone-aware.
    Hỗ trợ đầy đủ cả tiếng Anh (e.g. '18 min ago', '2 hours ago', '1mo ago', '3 days ago')
    và tiếng Việt (e.g. '18 phút trước', '2 giờ trước', '1 tháng trước', '3 ngày trước').
    Nếu chuỗi rỗng hoặc không nhận diện được, trả về (None, None) để đảm bảo an toàn tuyệt đối.
    """
    if not rel_text:
        return None, None

    s = str(rel_text).lower().replace("\xa0", " ").strip()
    now = datetime.now(timezone.utc)

    # 1. Hỗ trợ tiếng Anh: 18 min ago, 2 hours ago, 1mo ago, 3 days ago...
    m_en = re.search(r"(\d+)\s*(seconds?|sec|minutes?|min|hours?|hr|days?|weeks?|months?|mo|years?|yr)", s)
    if m_en:
        num = int(m_en.group(1))
        unit = m_en.group(2)
        if "sec" in unit:
            dt = now - timedelta(seconds=num)
        elif "min" in unit:
            dt = now - timedelta(minutes=num)
        elif "hour" in unit or "hr" in unit:
            dt = now - timedelta(hours=num)
        elif "day" in unit:
            dt = now - timedelta(days=num)
        elif "week" in unit:
            dt = now - timedelta(days=num * 7)
        elif "month" in unit or unit == "mo":
            dt = now - timedelta(days=num * 30)
        elif "year" in unit or "yr" in unit:
            dt = now - timedelta(days=num * 365)
        else:
            return None, None
        return dt.isoformat(), dt

    # 2. Hỗ trợ tiếng Việt: 18 phút trước, 2 giờ trước, 1 tháng trước...
    m_vi = re.search(r"(\d+)\s*(giây|phút|giờ|ngày|tuần|tháng|năm)", s)
    if m_vi:
        num = int(m_vi.group(1))
        unit = m_vi.group(2)
        if unit == "giây":
            dt = now - timedelta(seconds=num)
        elif unit == "phút":
            dt = now - timedelta(minutes=num)
        elif unit == "giờ":
            dt = now - timedelta(hours=num)
        elif unit == "ngày":
            dt = now - timedelta(days=num)
        elif unit == "tuần":
            dt = now - timedelta(days=num * 7)
        elif unit == "tháng":
            dt = now - timedelta(days=num * 30)
        elif unit == "năm":
            dt = now - timedelta(days=num * 365)
        else:
            return None, None
        return dt.isoformat(), dt

    return None, None


def parse_duration_str_to_seconds(dur_str: Optional[str]) -> int:
    """
    Chuyển chuỗi thời lượng YouTube như '27:15' hoặc '1:05:30' sang giây.
    """
    if not dur_str:
        return 0
    parts = str(dur_str).strip().split(":")
    try:
        if len(parts) == 2:
            return int(parts[0]) * 60 + int(parts[1])
        elif len(parts) == 3:
            return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
    except Exception:
        pass
    return 0


class YouTubeFetcher:
    """
    Fetcher chuyên dụng cho YouTube:
    - Giải mã Handle/URL -> channel_id (kèm file cache).
    - Quét RSS feed chuẩn.
    - Lọc bỏ Shorts và video ngắn dưới ngưỡng quy định.
    """

    USER_AGENT = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )

    def __init__(self, cache_file: Optional[Path] = None):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": self.USER_AGENT,
            "Accept-Language": "en-US,en;q=0.9",
        })
        self.cache_file = cache_file or (config.DATA_DIR / "channel_id_cache.json")
        self._channel_cache: Dict[str, str] = self._load_cache()

    def _load_cache(self) -> Dict[str, str]:
        """Nạp bộ nhớ đệm channel_id từ đĩa."""
        if self.cache_file.exists():
            try:
                with open(self.cache_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Không thể đọc file cache channel_id: {e}")
        return {}

    def _save_cache(self) -> None:
        """Lưu bộ nhớ đệm channel_id xuống đĩa."""
        try:
            self.cache_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.cache_file, "w", encoding="utf-8") as f:
                json.dump(self._channel_cache, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.warning(f"Không thể lưu cache channel_id: {e}")

    def resolve_channel_id(self, source_input: str) -> Optional[str]:
        """
        Phân giải đa dạng định dạng đầu vào (Handle, URL, Custom URL) thành channel_id (UC...).
        Có lưu cache để không bao giờ phải request phân giải lần thứ 2.
        Tự động bỏ qua và lưu cache nguồn hỏng/404 để không quét lại gây chậm hệ thống.
        """
        if not source_input:
            return None

        clean_src = source_input.strip()
        # Chuẩn hóa: loại bỏ đuôi /videos, /featured, etc. và dấu chấm/gạch chéo thừa
        clean_src = re.sub(
            r"/(videos|featured|community|about|live|streams)/?$", "", clean_src, flags=re.IGNORECASE
        ).rstrip("/. ")

        # 1. Nếu đã là dạng channel_id chuẩn (UC...)
        if re.match(r"^UC[\w-]{22}$", clean_src):
            return clean_src

        # 2. Kiểm tra trong cache (kể cả negative cache __DEAD__)
        if clean_src in self._channel_cache:
            val = self._channel_cache[clean_src]
            if val == "__DEAD__":
                logger.debug(f"Bỏ qua nguồn đã ghi nhận lỗi/không truy cập được: {clean_src}")
                return None
            return val

        # 3. Chuẩn bị URL để quét tìm channel_id
        if clean_src.startswith("http://") or clean_src.startswith("https://"):
            target_url = clean_src
        elif clean_src.startswith("@"):
            target_url = f"https://www.youtube.com/{clean_src}"
        else:
            target_url = f"https://www.youtube.com/@{clean_src}"

        # Nếu link có dạng /channel/UC... thì bóc trực tiếp
        direct_match = re.search(r"youtube\.com/channel/(UC[\w-]{22})", target_url)
        if direct_match:
            ch_id = direct_match.group(1)
            self._channel_cache[clean_src] = ch_id
            self._save_cache()
            return ch_id

        # 4. Gửi request để bóc tách từ HTML page của kênh
        try:
            logger.info(f"Đang phân giải channel_id cho nguồn: {clean_src} qua {target_url}")
            resp = self.session.get(target_url, timeout=config.REQUEST_TIMEOUT)
            if resp.status_code != 200:
                logger.info(f"Bỏ qua nguồn không truy cập được (HTTP {resp.status_code}): {target_url}")
                self._channel_cache[clean_src] = "__DEAD__"
                self._save_cache()
                return None

            html = resp.text

            # Các pattern phổ biến chứa channel_id trong mã nguồn YouTube
            patterns = [
                r'<meta itemprop="identifier" content="(UC[\w-]{22})">',
                r'<link rel="canonical" href="https://www.youtube.com/channel/(UC[\w-]{22})">',
                r'"externalId":"(UC[\w-]{22})"',
                r'"channelId":"(UC[\w-]{22})"',
            ]

            for pat in patterns:
                m = re.search(pat, html)
                if m:
                    ch_id = m.group(1)
                    self._channel_cache[clean_src] = ch_id
                    self._save_cache()
                    logger.info(f"Đã phân giải thành công: {clean_src} ➔ {ch_id}")
                    return ch_id

            logger.info(f"Bỏ qua nguồn (không tìm thấy channel_id trong mã HTML): {target_url}")
            self._channel_cache[clean_src] = "__DEAD__"
            self._save_cache()
            return None

        except Exception as e:
            logger.warning(f"Bỏ qua nguồn [{clean_src}] (lỗi kết nối hoặc sai định dạng: {e})")
            return None

    def is_youtube_short(self, video_id: str) -> bool:
        """
        Kiểm tra xem video có phải là YouTube Shorts hay không.
        Phương pháp tối ưu: Gửi HTTP HEAD tới URL https://www.youtube.com/shorts/{video_id}.
        - Nếu status=200 ➔ Là YouTube Shorts.
        - Nếu status=303 (redirect sang /watch?v=...) ➔ Là Video Dài bình thường.
        """
        shorts_url = f"https://www.youtube.com/shorts/{video_id}"
        try:
            # Không tự động follow redirect để bắt mã 303
            resp = self.session.head(shorts_url, allow_redirects=False, timeout=config.REQUEST_TIMEOUT)
            if resp.status_code == 200:
                return True
            if resp.status_code in (301, 302, 303, 307, 308):
                # Redirect sang /watch
                location = resp.headers.get("Location", "")
                return "/watch" not in location
            return False
        except Exception as e:
            logger.warning(f"Lỗi khi kiểm tra Shorts cho video {video_id}: {e}")
            return False

    def inspect_video_details(
        self, video_id: str, title: str = "", desc: str = ""
    ) -> Tuple[int, bool]:
        """
        Bóc tách thời lượng (giây) và kiểm tra video có phải là Livestream không.
        Returns: (duration_seconds, is_live)
        """
        # Kiểm tra nhanh qua tiêu đề và mô tả
        text_to_check = f"{title} {desc}".lower()
        is_live = bool(
            re.search(
                r"\b(livestream|live stream|đang phát trực tiếp|buổi phát trực tiếp)\b",
                text_to_check,
            )
        )

        watch_url = f"https://www.youtube.com/watch?v={video_id}"
        try:
            resp = self.session.get(watch_url, timeout=config.REQUEST_TIMEOUT)
            if resp.status_code != 200:
                return 0, is_live

            html = resp.text

            # Các dấu hiệu nhận diện Livestream trong HTML của YouTube
            live_indicators = [
                '"isLiveBroadcast":true',
                '"isLiveContent":true',
                '"liveBroadcastDetails"',
                '"isLive":true',
                '"status":"LIVE_STREAM_OFFLINE"',
                '<meta itemprop="isLiveBroadcast" content="True">',
                '<meta itemprop="isLiveBroadcast" content="true">',
            ]
            if any(ind in html for ind in live_indicators):
                is_live = True

            # Bóc tách duration từ <meta itemprop="duration" content="PT14M25S">
            duration = 0
            match = re.search(r'<meta itemprop="duration" content="PT([^"]+)">', html)
            if match:
                iso_duration = match.group(1)
                h = m = s = 0
                h_match = re.search(r"(\d+)H", iso_duration)
                m_match = re.search(r"(\d+)M", iso_duration)
                s_match = re.search(r"(\d+)S", iso_duration)

                if h_match:
                    h = int(h_match.group(1))
                if m_match:
                    m = int(m_match.group(1))
                if s_match:
                    s = int(s_match.group(1))

                duration = h * 3600 + m * 60 + s

            return duration, is_live

        except Exception as e:
            logger.warning(f"Lỗi khi kiểm tra thông tin video {video_id}: {e}")
            return 0, is_live

    def get_video_duration(self, video_id: str) -> int:
        """
        Lấy thời lượng video (tính bằng giây) từ mã nguồn trang watch mà KHÔNG cần API Key.
        Tìm thẻ: <meta itemprop="duration" content="PT14M25S">
        """
        duration, _ = self.inspect_video_details(video_id)
        return duration

    def fetch_raw_rss_entries(self, source_input: str) -> List[YouTubeVideo]:
        """
        Quét nhanh danh sách video từ RSS Feed mà KHÔNG gửi thêm HTTP HEAD/GET kiểm tra chi tiết.
        Rất thích hợp cho Seed Mode hoặc bước lọc sơ bộ trước khi tra cứu chi tiết.
        """
        ch_id = self.resolve_channel_id(source_input)
        if not ch_id:
            logger.debug(f"Bỏ qua quét nguồn [{source_input}] vì không có channel_id.")
            return []

        rss_url = f"https://www.youtube.com/feeds/videos.xml?channel_id={ch_id}"
        logger.info(f"Đang quét RSS: {rss_url} (Nguồn: {source_input})")

        try:
            feed = feedparser.parse(rss_url)
        except Exception as e:
            logger.warning(f"Lỗi khi parse RSS feed từ {rss_url}: {e}")
            return []

        if feed.bozo:
            logger.debug(f"Cảnh báo khi đọc RSS feed {rss_url}: {feed.get('bozo_exception')}")

        channel_title = feed.feed.get("title", source_input)
        videos: List[YouTubeVideo] = []

        for entry in feed.entries:
            try:
                video_id = entry.get("yt_videoid")
                if not video_id:
                    entry_id = entry.get("id", "")
                    if "yt:video:" in entry_id:
                        video_id = entry_id.split(":")[-1]
                    elif "v=" in entry.get("link", ""):
                        video_id = entry.get("link").split("v=")[-1].split("&")[0]

                if not video_id:
                    continue

                title = entry.get("title", "").strip()
                link = entry.get("link", f"https://www.youtube.com/watch?v={video_id}")
                published = entry.get("published", "")
                published_dt = None
                pub_parsed = entry.get("published_parsed")
                if pub_parsed:
                    try:
                        published_dt = datetime(*pub_parsed[:6], tzinfo=timezone.utc)
                    except Exception:
                        pass

                thumbnail_url = ""
                media_thumb = entry.get("media_thumbnail")
                if media_thumb and isinstance(media_thumb, list) and len(media_thumb) > 0:
                    thumbnail_url = media_thumb[0].get("url", "")

                desc = str(entry.get("media_description", ""))
                has_shorts_tag = "#shorts" in title.lower() or "#short" in title.lower() or "#shorts" in desc.lower()

                video_obj = YouTubeVideo(
                    video_id=video_id,
                    channel_id=ch_id,
                    channel_title=channel_title,
                    title=title,
                    link=link,
                    published_at=published,
                    published_dt=published_dt,
                    duration_seconds=0,
                    is_short=has_shorts_tag,
                    is_live=False,
                    thumbnail_url=thumbnail_url,
                    description=desc,
                )
                videos.append(video_obj)

            except Exception as item_err:
                logger.warning(f"Lỗi khi xử lý video entry: {item_err}")
                continue

        return videos

    def enrich_video_details(self, video: YouTubeVideo) -> YouTubeVideo:
        """
        Bổ sung chi tiết kiểm tra Shorts (HTTP HEAD) và thời lượng + Livestream (HTTP GET).
        CHỈ gọi phương thức này đối với video MỚI chưa từng được lưu trong cơ sở dữ liệu.
        """
        if not video.is_short:
            if video.duration_seconds > 180:
                video.is_short = False
            else:
                video.is_short = self.is_youtube_short(video.video_id)

        if video.duration_seconds <= 0:
            duration, is_live = self.inspect_video_details(
                video.video_id, title=video.title, desc=video.description
            )
            video.duration_seconds = duration
            video.is_live = is_live
        return video

    def build_channel_videos_url(self, source_input: str) -> str:
        """Tạo URL chuẩn trỏ đến tab /videos của kênh YouTube."""
        s = source_input.strip()
        if s.startswith("http://") or s.startswith("https://"):
            clean = re.sub(r"/(videos|featured|community|about|live|streams)/?$", "", s, flags=re.IGNORECASE).rstrip("/. ")
            return f"{clean}/videos"
        elif s.startswith("@"):
            return f"https://www.youtube.com/{s}/videos"
        elif re.match(r"^UC[\w-]{22}$", s):
            return f"https://www.youtube.com/channel/{s}/videos"
        else:
            return f"https://www.youtube.com/@{s}/videos"

    def fetch_channel_tab_videos(self, source_input: str) -> List[YouTubeVideo]:
        """
        Quét trực tiếp tab /videos của kênh YouTube (Realtime 0-second lag).
        Bóc tách cấu trúc ytInitialData (lockupViewModel và videoRenderer).
        """
        url = self.build_channel_videos_url(source_input)
        try:
            resp = self.session.get(
                url,
                headers={"Accept-Language": "en-US,en;q=0.9"},
                timeout=config.REQUEST_TIMEOUT,
            )
            if resp.status_code != 200:
                logger.debug(f"Không thể truy cập tab /videos của {source_input} (HTTP {resp.status_code})")
                return []
            html_text = resp.text
        except Exception as e:
            logger.debug(f"Lỗi khi request tab /videos ({url}): {e}")
            return []

        # Bóc tách ytInitialData
        m = re.search(r"var ytInitialData\s*=\s*({.+?});</script>", html_text, flags=re.DOTALL)
        if not m:
            m = re.search(r"ytInitialData\s*=\s*({.+?});", html_text, flags=re.DOTALL)
        if not m:
            return []

        try:
            data = json.loads(m.group(1))
        except Exception:
            return []

        # Phân giải channel_id và title nếu có
        ch_id = self.resolve_channel_id(source_input) or ""
        channel_title = ""
        m_title = re.search(r'<meta property="og:title" content="([^"]+)">', html_text)
        if m_title:
            channel_title = html.unescape(m_title.group(1))

        # Tìm các lockupViewModel và videoRenderer
        items: List[Tuple[str, Dict[str, Any]]] = []
        def find_renderers(obj):
            if isinstance(obj, dict):
                if "lockupViewModel" in obj:
                    items.append(("lockup", obj["lockupViewModel"]))
                elif "videoRenderer" in obj:
                    items.append(("videoRenderer", obj["videoRenderer"]))
                for v in obj.values():
                    find_renderers(v)
            elif isinstance(obj, list):
                for i in obj:
                    find_renderers(i)

        find_renderers(data)

        videos: List[YouTubeVideo] = []
        seen_ids = set()

        for kind, item in items:
            try:
                if kind == "lockup":
                    vid = item.get("contentId")
                    if not vid or len(vid) != 11 or vid in seen_ids:
                        continue
                    seen_ids.add(vid)

                    metadata = item.get("metadata", {}).get("lockupMetadataViewModel", {})
                    title = metadata.get("title", {}).get("content", "").strip()
                    if not title:
                        continue

                    # Duration
                    duration_sec = 0
                    overlays = item.get("contentImage", {}).get("thumbnailViewModel", {}).get("overlays", [])
                    for o in overlays:
                        badges = o.get("thumbnailBottomOverlayViewModel", {}).get("badges", [])
                        for b in badges:
                            text = b.get("thumbnailBadgeViewModel", {}).get("text", "")
                            if ":" in text:
                                duration_sec = parse_duration_str_to_seconds(text)

                    # Thumbnail
                    thumb_url = f"https://img.youtube.com/vi/{vid}/hqdefault.jpg"
                    sources = item.get("contentImage", {}).get("thumbnailViewModel", {}).get("image", {}).get("sources", [])
                    if sources:
                        thumb_url = sources[-1].get("url", thumb_url)

                    # Published time (Tìm chuỗi thời gian tương đối đa ngôn ngữ)
                    pub_text = ""
                    meta_rows = metadata.get("metadata", {}).get("contentMetadataViewModel", {}).get("metadataRows", [])
                    for r_row in meta_rows:
                        for p in r_row.get("metadataParts", []):
                            t = p.get("text", {}).get("content", "")
                            acc = p.get("accessibilityLabel", "")
                            for c in [t, acc]:
                                if c and any(kw in c.lower() for kw in ["ago", "trước", "hour", "min", "sec", "day", "week", "month", "mo", "year", "phút", "giờ", "ngày", "tuần", "tháng"]):
                                    pub_text = c
                                    break
                            if pub_text:
                                break
                        if pub_text:
                            break

                    pub_iso, pub_dt = parse_relative_time_to_iso(pub_text)
                    has_shorts_tag = "#shorts" in title.lower() or "#short" in title.lower()

                    videos.append(YouTubeVideo(
                        video_id=vid,
                        channel_id=ch_id,
                        channel_title=channel_title or source_input,
                        title=title,
                        link=f"https://www.youtube.com/watch?v={vid}",
                        published_at=pub_iso or "",
                        published_dt=pub_dt,
                        duration_seconds=duration_sec,
                        is_short=has_shorts_tag,
                        is_live=False,
                        thumbnail_url=thumb_url,
                        description="",
                    ))

                elif kind == "videoRenderer":
                    vid = item.get("videoId")
                    if not vid or len(vid) != 11 or vid in seen_ids:
                        continue
                    seen_ids.add(vid)

                    title_obj = item.get("title", {})
                    title = ""
                    if "runs" in title_obj and title_obj["runs"]:
                        title = title_obj["runs"][0].get("text", "")
                    elif "simpleText" in title_obj:
                        title = title_obj.get("simpleText", "")
                    if not title:
                        continue

                    len_text = item.get("lengthText", {}).get("simpleText", "")
                    duration_sec = parse_duration_str_to_seconds(len_text)

                    pub_text = item.get("publishedTimeText", {}).get("simpleText", "")
                    if not pub_text:
                        pub_text = item.get("publishedTimeText", {}).get("accessibilityLabel", "")
                    pub_iso, pub_dt = parse_relative_time_to_iso(pub_text)

                    thumb_url = f"https://img.youtube.com/vi/{vid}/hqdefault.jpg"
                    thumbs = item.get("thumbnail", {}).get("thumbnails", [])
                    if thumbs:
                        thumb_url = thumbs[-1].get("url", thumb_url)

                    has_shorts_tag = "#shorts" in title.lower() or "#short" in title.lower()

                    videos.append(YouTubeVideo(
                        video_id=vid,
                        channel_id=ch_id,
                        channel_title=channel_title or source_input,
                        title=title.strip(),
                        link=f"https://www.youtube.com/watch?v={vid}",
                        published_at=pub_iso or "",
                        published_dt=pub_dt,
                        duration_seconds=duration_sec,
                        is_short=has_shorts_tag,
                        is_live=False,
                        thumbnail_url=thumb_url,
                        description="",
                    ))
            except Exception as e:
                logger.debug(f"Lỗi khi parse item từ tab /videos: {e}")
                continue

        logger.debug(f"Đã trích xuất {len(videos)} video từ tab /videos của {source_input}")
        return videos

    def fetch_dual_videos(self, source_input: str) -> List[YouTubeVideo]:
        """
        Quét kép thông minh (Realtime Dual-Fetcher):
        1. Quét trực tiếp Tab /videos (Thời gian thực 0-second lag).
        2. Quét luồng RSS XML.
        3. Hợp nhất danh sách và khử trùng lặp theo video_id.
        """
        all_videos: Dict[str, YouTubeVideo] = {}

        # 1. Quét Tab /videos (Thời gian thực)
        try:
            tab_videos = self.fetch_channel_tab_videos(source_input)
            for v in tab_videos:
                all_videos[v.video_id] = v
        except Exception as e:
            logger.debug(f"Quét tab /videos thất bại cho {source_input}: {e}")

        # 2. Quét luồng RSS XML (Dự phòng)
        try:
            rss_videos = self.fetch_raw_rss_entries(source_input)
            for v in rss_videos:
                if v.video_id not in all_videos:
                    all_videos[v.video_id] = v
                else:
                    # Nếu RSS có published_at ISO chuẩn hơn (từ Atom feed), ưu tiên cập nhật
                    if v.published_dt:
                        all_videos[v.video_id].published_at = v.published_at
                        all_videos[v.video_id].published_dt = v.published_dt
                    if v.channel_title and all_videos[v.video_id].channel_title == source_input:
                        all_videos[v.video_id].channel_title = v.channel_title
                    if v.channel_id and not all_videos[v.video_id].channel_id:
                        all_videos[v.video_id].channel_id = v.channel_id
        except Exception as e:
            logger.debug(f"Quét RSS thất bại cho {source_input}: {e}")

        return list(all_videos.values())

    def fetch_channel_videos(
        self,
        source_input: str,
        filter_shorts: Optional[bool] = None,
        min_duration: Optional[int] = None,
        filter_livestreams: Optional[bool] = None,
    ) -> List[YouTubeVideo]:
        """
        Quét các video mới nhất từ cơ chế Quét Kép (Dual-Fetcher) của 1 kênh YouTube.
        Tự động bóc tách metadata và áp dụng các bộ lọc chất lượng.
        """
        should_filter_shorts = filter_shorts if filter_shorts is not None else config.FILTER_OUT_SHORTS
        should_filter_live = filter_livestreams if filter_livestreams is not None else config.FILTER_OUT_LIVESTREAMS
        min_dur = min_duration if min_duration is not None else config.MIN_VIDEO_DURATION_SECONDS

        raw_videos = self.fetch_dual_videos(source_input)
        videos: List[YouTubeVideo] = []

        for vid in raw_videos:
            if should_filter_shorts and vid.is_short:
                continue

            vid = self.enrich_video_details(vid)

            if should_filter_shorts and vid.is_short:
                continue
            if should_filter_live and vid.is_live:
                continue
            if min_dur > 0 and 0 < vid.duration_seconds < min_dur:
                continue

            videos.append(vid)

        logger.info(f"Hoàn thành quét nguồn: tìm thấy {len(videos)} video đạt chuẩn.")
        return videos
