"""
TikTok Beta US Automation Notifier - YouTube RSS Fetcher
========================================================
Quét video mới từ YouTube RSS không giới hạn quota API.
Tự động phân giải @handle sang channel_id, phát hiện và loại bỏ Shorts,
lọc thời lượng video theo chuẩn TikTok Creator Rewards Program (Beta US).
"""

import re
import json
from pathlib import Path
from datetime import datetime, timezone
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Tuple
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
    thumbnail_url: str = ""
    description: str = ""

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
        self.session.headers.update({"User-Agent": self.USER_AGENT})
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
        """
        if not source_input:
            return None

        clean_src = source_input.strip()

        # 1. Nếu đã là dạng channel_id chuẩn (UC...)
        if re.match(r"^UC[\w-]{22}$", clean_src):
            return clean_src

        # 2. Kiểm tra trong cache
        if clean_src in self._channel_cache:
            return self._channel_cache[clean_src]

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
                logger.error(f"Không thể truy cập kênh {target_url} (HTTP {resp.status_code})")
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

            logger.warning(f"Không tìm thấy channel_id trong mã HTML của: {target_url}")
            return None

        except Exception as e:
            logger.exception(f"Lỗi khi phân giải channel_id cho {clean_src}: {e}")
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

    def get_video_duration(self, video_id: str) -> int:
        """
        Lấy thời lượng video (tính bằng giây) từ mã nguồn trang watch mà KHÔNG cần API Key.
        Tìm thẻ: <meta itemprop="duration" content="PT14M25S">
        """
        watch_url = f"https://www.youtube.com/watch?v={video_id}"
        try:
            resp = self.session.get(watch_url, timeout=config.REQUEST_TIMEOUT)
            if resp.status_code != 200:
                return 0

            match = re.search(r'<meta itemprop="duration" content="PT([^"]+)">', resp.text)
            if not match:
                return 0

            iso_duration = match.group(1)
            # Parse dạng: 1H2M3S hoặc 14M25S hoặc 45S
            h = m = s = 0
            h_match = re.search(r'(\d+)H', iso_duration)
            m_match = re.search(r'(\d+)M', iso_duration)
            s_match = re.search(r'(\d+)S', iso_duration)

            if h_match:
                h = int(h_match.group(1))
            if m_match:
                m = int(m_match.group(1))
            if s_match:
                s = int(s_match.group(1))

            total_seconds = h * 3600 + m * 60 + s
            return total_seconds

        except Exception as e:
            logger.warning(f"Lỗi khi lấy thời lượng video {video_id}: {e}")
            return 0

    def fetch_channel_videos(
        self,
        source_input: str,
        filter_shorts: Optional[bool] = None,
        min_duration: Optional[int] = None,
    ) -> List[YouTubeVideo]:
        """
        Quét các video mới nhất từ RSS Feed của 1 kênh YouTube.
        Tự động bóc tách metadata và áp dụng các bộ lọc chất lượng.
        """
        should_filter_shorts = filter_shorts if filter_shorts is not None else config.FILTER_OUT_SHORTS
        min_dur = min_duration if min_duration is not None else config.MIN_VIDEO_DURATION_SECONDS

        ch_id = self.resolve_channel_id(source_input)
        if not ch_id:
            logger.error(f"Bỏ qua quét nguồn [{source_input}] vì không lấy được channel_id.")
            return []

        rss_url = f"https://www.youtube.com/feeds/videos.xml?channel_id={ch_id}"
        logger.info(f"Đang quét RSS: {rss_url} (Nguồn: {source_input})")

        try:
            feed = feedparser.parse(rss_url)
        except Exception as e:
            logger.exception(f"Lỗi khi parse RSS feed từ {rss_url}: {e}")
            return []

        if feed.bozo:
            logger.warning(f"Cảnh báo khi đọc RSS feed {rss_url}: {feed.get('bozo_exception')}")

        channel_title = feed.feed.get("title", source_input)
        videos: List[YouTubeVideo] = []

        for entry in feed.entries:
            try:
                # Video ID thường nằm trong yt_videoid hoặc id dạng 'yt:video:xxxx'
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

                # Thumbnail
                thumbnail_url = ""
                media_thumb = entry.get("media_thumbnail")
                if media_thumb and isinstance(media_thumb, list) and len(media_thumb) > 0:
                    thumbnail_url = media_thumb[0].get("url", "")

                # Mô tả ngắn
                desc = str(entry.get("media_description", ""))

                # 1. Bộ lọc Shorts
                # Lọc nhanh qua tiêu đề / mô tả
                has_shorts_tag = "#shorts" in title.lower() or "#short" in title.lower() or "#shorts" in desc.lower()

                is_short = has_shorts_tag
                if should_filter_shorts:
                    if is_short:
                        logger.debug(f"Bỏ qua Shorts (tag): {title} ({video_id})")
                        continue

                    # Kiểm tra HEAD redirect
                    if self.is_youtube_short(video_id):
                        logger.debug(f"Bỏ qua Shorts (HEAD redirect): {title} ({video_id})")
                        continue

                # 2. Bộ lọc thời lượng (TikTok Beta US: >= 180s hoặc cấu hình)
                duration = 0
                if min_dur > 0:
                    duration = self.get_video_duration(video_id)
                    if 0 < duration < min_dur:
                        logger.debug(
                            f"Bỏ qua video quá ngắn ({duration}s < {min_dur}s): {title} ({video_id})"
                        )
                        continue

                video_obj = YouTubeVideo(
                    video_id=video_id,
                    channel_id=ch_id,
                    channel_title=channel_title,
                    title=title,
                    link=link,
                    published_at=published,
                    duration_seconds=duration,
                    is_short=is_short,
                    thumbnail_url=thumbnail_url,
                    description=desc,
                )

                videos.append(video_obj)

            except Exception as item_err:
                logger.warning(f"Lỗi khi xử lý video entry: {item_err}")
                continue

        logger.info(f"Hoàn thành quét nguồn [{channel_title}]: tìm thấy {len(videos)} video đạt chuẩn.")
        return videos
