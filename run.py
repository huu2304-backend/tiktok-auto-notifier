#!/usr/bin/env python3
"""
TikTok Beta US Automation Notifier - Production Runner CLI
==========================================================
Điểm khởi chạy chính của hệ thống.

Cách dùng:
  - Chạy quét liên tục (Scheduler):
      python run.py
      python run.py --interval 180

  - Quét 1 lần duy nhất rồi thoát:
      python run.py --scan-once

  - Quét riêng cho 1 Máy cụ thể:
      python run.py --scan-once --machine "Máy 01"

  - Quét riêng cho 1 Kênh TikTok cụ thể:
      python run.py --scan-once --channel "@daily_crime_us"

  - Chế độ giả lập (Dry-run không bắn tin):
      python run.py --scan-once --dry-run

  - Liệt kê danh sách kênh đã cấu hình từ Excel:
      python run.py --list-channels

  - Kiểm tra kết nối Telegram Bot:
      python run.py --test-telegram
"""

import sys
import argparse
from pathlib import Path

# Đảm bảo import được các module từ thư mục gốc
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

from config.settings import logger, config
from src.parser.excel_parser import ExcelConfigParser
from src.fetcher.youtube_rss import YouTubeFetcher
from src.notifier.telegram_bot import TelegramNotifier
from src.core.database import TrackingDatabase
from src.core.engine import AutomationEngine


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="TikTok Beta US Automation Notifier - Hệ thống tự động quét nguồn YouTube cho TikTok Beta",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "--scan-once",
        action="store_true",
        help="Chỉ quét 1 chu kỳ duy nhất rồi thoát (mặc định sẽ chạy lặp liên tục)",
    )

    parser.add_argument(
        "--machine",
        "-m",
        type=str,
        default=None,
        help="Lọc quét riêng theo Tên Máy (ví dụ: 'Máy 01', 'Máy 02')",
    )

    parser.add_argument(
        "--channel",
        "-c",
        type=str,
        default=None,
        help="Lọc quét riêng theo Tài khoản TikTok (ví dụ: '@daily_crime_us')",
    )

    parser.add_argument(
        "--interval",
        "-i",
        type=int,
        default=None,
        help=f"Thời gian nghỉ giữa các chu kỳ quét tính bằng giây (Mặc định: {config.CHECK_INTERVAL_SECONDS}s)",
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Chế độ giả lập: Quét và hiển thị log video mới, KHÔNG bắn tin Telegram và KHÔNG lưu DB",
    )

    parser.add_argument(
        "--list-channels",
        action="store_true",
        help="Đọc và in toàn bộ danh sách Máy, Kênh TikTok và Nguồn YouTube từ Excel rồi thoát",
    )

    parser.add_argument(
        "--test-telegram",
        action="store_true",
        help="Kiểm tra kết nối và tính hợp lệ của Telegram Bot Token & Chat ID",
    )

    return parser.parse_args()


def handle_list_channels():
    """In danh sách kênh cấu hình ra màn hình console."""
    parser = ExcelConfigParser()
    try:
        channels = parser.parse()
    except Exception as e:
        logger.error(f"Không thể đọc danh sách kênh: {e}")
        return

    print("\n" + "=" * 80)
    print("📋 DANH SÁCH CẤU HÌNH KÊNH TIKTOK BETA US (TỪ EXCEL)")
    print("=" * 80)

    for idx, c in enumerate(channels, 1):
        status_str = "✅ BKT" if c.is_bkt() else "⏳ KBKT"
        print(f"\n[{idx}] {c.machine_name.upper()} | {c.tiktok_channel} [{status_str}]")
        print(f"     • Cụm chủ đề : {c.niche}")
        print(f"     • Ghi chú     : {c.note or 'Không có'}")
        print(f"     • Nguồn YT ({len(c.youtube_sources)} nguồn):")
        for s_idx, src in enumerate(c.youtube_sources, 1):
            print(f"        {s_idx}. {src}")

    print("\n" + "=" * 80)
    print(f"Tổng số kênh TikTok: {len(channels)} | File Excel: {parser.excel_path.resolve()}\n")


def handle_test_telegram():
    """Kiểm tra token bot Telegram."""
    notifier = TelegramNotifier()
    success, msg = notifier.test_connection()
    if success:
        print(f"\n✅ {msg}\n")
    else:
        print(f"\n❌ {msg}\n")


def main():
    args = parse_arguments()

    # 1. Lệnh kiểm tra danh sách kênh
    if args.list_channels:
        handle_list_channels()
        return

    # 2. Lệnh kiểm tra bot Telegram
    if args.test_telegram:
        handle_test_telegram()
        return

    # 3. Khởi tạo Automation Engine
    engine = AutomationEngine()

    if args.dry_run:
        logger.info("⚠️ ĐANG CHẠY Ở CHẾ ĐỘ GIẢ LẬP (DRY-RUN): Không gửi tin nhắn thật.")

    # 4. Chế độ quét 1 lần
    if args.scan_once:
        logger.info("Chế độ: QUÉT 1 LẦN (Single Scan)")
        count = engine.scan_once(
            machine=args.machine,
            tiktok_channel=args.channel,
            dry_run=args.dry_run,
        )
        logger.info(f"Hoàn thành lệnh quét 1 lần. Phát hiện {count} video mới.")
        return

    # 5. Chế độ chạy liên tục (Scheduler)
    engine.run_scheduler(
        interval_seconds=args.interval,
        machine=args.machine,
        tiktok_channel=args.channel,
    )


if __name__ == "__main__":
    main()
