"""
TikTok Beta US Automation Notifier - SQLite Storage & Idempotency
=================================================================
Lưu trữ và kiểm soát cache video_id đã thông báo (data/tracked_videos.db).
Đảm bảo tính bất biến (Idempotent): Không bao giờ gửi thông báo trùng lặp.
"""

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional, List, Tuple, Generator, Dict, Any

from config.settings import logger, config


class TrackingDatabase:
    """Quản lý cơ sở dữ liệu SQLite lưu vết các video đã gửi thông báo."""

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = Path(db_path or config.DB_PATH)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    @contextmanager
    def get_connection(self) -> Generator[sqlite3.Connection, None, None]:
        """Tạo kết nối SQLite và đảm bảo đóng kết nối ngay sau khi hoàn thành."""
        conn = sqlite3.connect(self.db_path, timeout=10.0)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def _init_db(self) -> None:
        """Khởi tạo bảng tracked_videos và các index nếu chưa có."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS tracked_videos (
                        video_id TEXT NOT NULL,
                        tiktok_channel TEXT NOT NULL,
                        machine_name TEXT,
                        channel_id TEXT,
                        video_title TEXT,
                        published_at TEXT,
                        notified_at TEXT NOT NULL,
                        status TEXT DEFAULT 'SENT',
                        PRIMARY KEY (video_id, tiktok_channel)
                    );
                    """
                )
                cursor.execute(
                    """
                    CREATE INDEX IF NOT EXISTS idx_video_id 
                    ON tracked_videos (video_id);
                    """
                )
                cursor.execute(
                    """
                    CREATE INDEX IF NOT EXISTS idx_tiktok_channel 
                    ON tracked_videos (tiktok_channel);
                    """
                )
                conn.commit()
                logger.debug(f"Đã kiểm tra/khởi tạo SQLite DB tại: {self.db_path}")
        except Exception as e:
            logger.exception(f"Lỗi khởi tạo SQLite DB ({self.db_path}): {e}")
            raise

    def is_tracked(self, video_id: str, tiktok_channel: str) -> bool:
        """
        Kiểm tra video đã từng được thông báo cho kênh TikTok này chưa.
        Trả về True nếu đã thông báo rồi (cần bỏ qua), False nếu là video mới.
        """
        query = """
            SELECT 1 FROM tracked_videos 
            WHERE video_id = ? AND LOWER(tiktok_channel) = LOWER(?)
            LIMIT 1;
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, (video_id, tiktok_channel.strip()))
                return cursor.fetchone() is not None
        except Exception as e:
            logger.warning(f"Lỗi kiểm tra tracked cho video {video_id} - {tiktok_channel}: {e}")
            return False

    def mark_as_tracked(
        self,
        video_id: str,
        tiktok_channel: str,
        machine_name: str,
        channel_id: str,
        video_title: str,
        published_at: str,
        status: str = "SENT",
    ) -> bool:
        """
        Lưu vết video đã gửi thông báo thành công vào SQLite.
        """
        query = """
            INSERT OR REPLACE INTO tracked_videos 
            (video_id, tiktok_channel, machine_name, channel_id, video_title, published_at, notified_at, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?);
        """
        now_iso = datetime.now(timezone.utc).isoformat()
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    query,
                    (
                        video_id,
                        tiktok_channel.strip(),
                        machine_name,
                        channel_id,
                        video_title,
                        published_at,
                        now_iso,
                        status,
                    ),
                )
                conn.commit()
                return True
        except Exception as e:
            logger.exception(f"Lỗi khi lưu tracked video ({video_id} - {tiktok_channel}): {e}")
            return False

    def get_tracked_count(self) -> int:
        """Đếm tổng số bản ghi đã lưu."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM tracked_videos;")
                row = cursor.fetchone()
                return row[0] if row else 0
        except Exception as e:
            logger.warning(f"Lỗi đếm số lượng bản ghi DB: {e}")
            return 0

    def get_stats(self) -> Dict[str, Any]:
        """Lấy các chỉ số thống kê từ SQLite database."""
        stats = {
            "total_tracked": 0,
            "total_sent": 0,
            "total_seeded": 0,
            "total_channels": 0,
        }
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM tracked_videos;")
                row = cursor.fetchone()
                if row:
                    stats["total_tracked"] = row[0]

                cursor.execute("SELECT COUNT(*) FROM tracked_videos WHERE status = 'SENT';")
                row = cursor.fetchone()
                if row:
                    stats["total_sent"] = row[0]

                cursor.execute("SELECT COUNT(*) FROM tracked_videos WHERE status IN ('SEEDED', 'OLD_VIDEO');")
                row = cursor.fetchone()
                if row:
                    stats["total_seeded"] = row[0]

                cursor.execute("SELECT COUNT(DISTINCT tiktok_channel) FROM tracked_videos;")
                row = cursor.fetchone()
                if row:
                    stats["total_channels"] = row[0]
        except Exception as e:
            logger.warning(f"Lỗi lấy thống kê DB: {e}")
        return stats
