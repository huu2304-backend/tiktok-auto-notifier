"""
TikTok Beta US Automation Notifier - Settings & Logging Configuration
====================================================================
Quản lý cấu hình tập trung từ biến môi trường (.env) và thiết lập
hệ thống logging production hỗ trợ đa nền tảng (Windows/Linux).
"""

import os
import sys
import logging
from pathlib import Path
from dataclasses import dataclass
from dotenv import load_dotenv

# Xác định đường dẫn gốc dự án (tiktok-auto-notifier)
BASE_DIR = Path(__file__).resolve().parent.parent

# Tự động nạp file .env từ thư mục gốc
ENV_FILE = BASE_DIR / ".env"
if ENV_FILE.exists():
    load_dotenv(dotenv_path=ENV_FILE)
else:
    load_dotenv()


@dataclass(frozen=True)
class AppConfig:
    """Class cấu hình tĩnh cho toàn bộ ứng dụng."""

    # Đường dẫn thư mục & file chuẩn
    BASE_DIR: Path = BASE_DIR
    DATA_DIR: Path = BASE_DIR / "data"
    LOGS_DIR: Path = BASE_DIR / "logs"

    EXCEL_PATH: Path = (
        Path(os.getenv("CUSTOM_EXCEL_PATH"))
        if os.getenv("CUSTOM_EXCEL_PATH")
        else DATA_DIR / "config_channels.xlsx"
    )

    DB_PATH: Path = (
        Path(os.getenv("CUSTOM_DB_PATH"))
        if os.getenv("CUSTOM_DB_PATH")
        else DATA_DIR / "tracked_videos.db"
    )

    LOG_FILE: Path = LOGS_DIR / "app.log"

    # Telegram Bot
    TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    TELEGRAM_CHAT_ID: str = os.getenv("TELEGRAM_CHAT_ID", "").strip()
    TELEGRAM_MESSAGE_THREAD_ID: str = os.getenv("TELEGRAM_MESSAGE_THREAD_ID", "").strip()

    # Quét & Lọc Video
    CHECK_INTERVAL_SECONDS: int = int(os.getenv("CHECK_INTERVAL_SECONDS", "300"))
    MIN_VIDEO_DURATION_SECONDS: int = int(os.getenv("MIN_VIDEO_DURATION_SECONDS", "0"))  # 0: Chấp nhận mọi thời lượng (chỉ lọc Shorts)
    FILTER_OUT_SHORTS: bool = os.getenv("FILTER_OUT_SHORTS", "True").lower() in ("true", "1", "yes")
    FILTER_OUT_LIVESTREAMS: bool = os.getenv("FILTER_OUT_LIVESTREAMS", "True").lower() in ("true", "1", "yes")

    # Mạng & Timeout
    REQUEST_TIMEOUT: int = int(os.getenv("REQUEST_TIMEOUT", "15"))
    MAX_RETRIES: int = int(os.getenv("MAX_RETRIES", "3"))

    def is_telegram_ready(self) -> bool:
        """Kiểm tra bot token và chat id đã được điền hay chưa."""
        return bool(self.TELEGRAM_BOT_TOKEN and self.TELEGRAM_CHAT_ID)


config = AppConfig()


def setup_logging(log_level: int = logging.INFO) -> logging.Logger:
    """
    Khởi tạo hệ thống logging đa luồng (console + file).
    Đặc biệt xử lý mã hóa UTF-8 để không bị lỗi ký tự tiếng Việt / emoji trên Windows.
    """
    config.LOGS_DIR.mkdir(parents=True, exist_ok=True)
    config.DATA_DIR.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger("tiktok_notifier")
    logger.setLevel(log_level)

    # Tránh gắn duplicate handlers khi gọi nhiều lần
    if logger.hasHandlers():
        return logger

    # Định dạng log chuẩn Production
    formatter = logging.Formatter(
        fmt="[%(asctime)s] [%(levelname)-7s] [%(name)s:%(funcName)s:%(lineno)d] - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # 1. Console Handler (ép kiểu UTF-8 trên Windows)
    try:
        # sys.stdout có thể reconfigure trên Python 3.7+
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # 2. File Handler (ghi file app.log với encoding UTF-8)
    file_handler = logging.FileHandler(config.LOG_FILE, encoding="utf-8")
    file_handler.setLevel(log_level)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger


# Logger toàn cục sẵn sàng sử dụng
logger = setup_logging()
