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
from typing import Optional

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

    parser.add_argument(
        "--sync-gdrive",
        nargs="?",
        const="",
        type=str,
        default=None,
        help="Đồng bộ file cấu hình kênh từ Google Sheets về máy (có thể truyền URL hoặc lấy từ GOOGLE_SHEET_URL trong .env)",
    )

    parser.add_argument(
        "--seed",
        action="store_true",
        help="Chế độ khởi tạo mốc cơ sở (Seed): Quét và lưu vết toàn bộ video hiện tại vào database mà KHÔNG gửi thông báo Telegram (chống spam tin cũ)",
    )

    parser.add_argument(
        "--status",
        action="store_true",
        help="Hiển thị bảng báo cáo sức khỏe và thống kê tổng quan hệ thống",
    )

    parser.add_argument(
        "--clear-cache",
        action="store_true",
        help="Xóa bộ nhớ đệm channel_id và danh sách nguồn lỗi (để phân giải lại từ đầu sau khi sửa link)",
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


def handle_sync_gdrive(url_arg: Optional[str] = None):
    """Đồng bộ cấu hình từ Google Sheets."""
    from src.sync.gdrive_sync import GoogleSheetSync

    target_url = (url_arg or config.GOOGLE_SHEET_URL).strip()
    if not target_url:
        print("\n❌ Chưa có URL Google Sheets! Vui lòng truyền URL sau lệnh hoặc điền GOOGLE_SHEET_URL trong file .env.")
        print("   Ví dụ: python run.py --sync-gdrive https://docs.google.com/spreadsheets/d/...\n")
        return

    syncer = GoogleSheetSync()
    success, msg, count = syncer.sync(target_url)
    if success:
        print(f"\n✅ {msg}\n")
    else:
        print(f"\n❌ {msg}\n")


def handle_status():
    """In báo cáo tình trạng hệ thống và mạng lưới kênh."""
    parser = ExcelConfigParser()
    db = TrackingDatabase()
    fetcher = YouTubeFetcher()
    notifier = TelegramNotifier()

    try:
        channels = parser.parse()
    except Exception as e:
        print(f"\n❌ Lỗi đọc cấu hình: {e}\n")
        return

    bkt_count = sum(1 for c in channels if c.is_bkt())
    kbkt_count = len(channels) - bkt_count
    all_sources = set([s for c in channels for s in c.youtube_sources])

    dead_sources = [s for s, ch_id in fetcher._channel_cache.items() if ch_id == "__DEAD__"]
    valid_sources = [s for s, ch_id in fetcher._channel_cache.items() if ch_id and ch_id != "__DEAD__"]

    db_stats = db.get_stats()
    tele_ok, tele_msg = notifier.test_connection()

    print("\n" + "=" * 80)
    print("📊 BÁO CÁO TÌNH TRẠNG HỆ THỐNG TIKTOK BETA US AUTOMATION")
    print("=" * 80)
    print(f"🖥️  Tổng số Máy quản lý          : {len(channels)} máy")
    print(f"📱  Tổng số Kênh TikTok         : {len(channels)} kênh ({bkt_count} BKT, {kbkt_count} KBKT)")
    print(f"📺  Tổng số Nguồn YouTube       : {len(all_sources)} nguồn duy nhất")
    print(f"   • Đã phân giải hợp lệ        : {len(valid_sources)} nguồn")
    print(f"   • Bị lỗi/404 (đã tự bỏ qua)  : {len(dead_sources)} nguồn")
    if dead_sources:
        for ds in dead_sources[:5]:
            print(f"      - {ds}")
        if len(dead_sources) > 5:
            print(f"      ... và {len(dead_sources) - 5} nguồn khác")
    print("--------------------------------------------------------------------------------")
    print(f"💾  Dữ liệu lưu vết (SQLite DB) : {db_stats.get('total_tracked', 0)} video")
    print(f"   • Đã gửi thông báo Telegram  : {db_stats.get('total_sent', 0)} video")
    print(f"   • Video mốc cơ sở (Seed/Cũ)  : {db_stats.get('total_seeded', 0)} video")
    print("--------------------------------------------------------------------------------")
    print(f"🤖  Trạng thái Telegram Bot      : {'✅ Hoạt động' if tele_ok else '❌ Chưa kết nối'} ({tele_msg})")
    print("=" * 80 + "\n")


def handle_clear_cache():
    """Xóa file cache channel_id."""
    cache_path = config.DATA_DIR / "channel_id_cache.json"
    if cache_path.exists():
        try:
            cache_path.unlink()
            print(f"\n✅ Đã xóa sạch file cache tại: {cache_path}")
            print("   Hệ thống sẽ phân giải lại toàn bộ link khi quét lần tiếp theo.\n")
        except Exception as e:
            print(f"\n❌ Lỗi khi xóa cache: {e}\n")
    else:
        print("\nℹ️ Không có file cache nào cần xóa.\n")


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

    # 3. Lệnh đồng bộ Google Sheets
    if args.sync_gdrive is not None:
        handle_sync_gdrive(args.sync_gdrive)
        return

    # 4. Lệnh xem trạng thái hệ thống
    if args.status:
        handle_status()
        return

    # 5. Lệnh xóa cache
    if args.clear_cache:
        handle_clear_cache()
        return

    # 6. Khởi tạo Automation Engine
    engine = AutomationEngine()

    if args.dry_run:
        logger.info("⚠️ ĐANG CHẠY Ở CHẾ ĐỘ GIẢ LẬP (DRY-RUN): Không gửi tin nhắn thật.")

    # 7. Chế độ Seed Baseline (Khởi tạo mốc cơ sở - Không spam tin cũ)
    if args.seed:
        logger.info("🌱 Đang thực hiện KHỞI TẠO MỐC DỮ LIỆU BAN ĐẦU (Seed Baseline)...")
        count = engine.scan_once(
            machine=args.machine,
            tiktok_channel=args.channel,
            dry_run=args.dry_run,
            seed_mode=True,
        )
        print("\n" + "=" * 80)
        print("🌱 HOÀN TẤT KHỞI TẠO MỐC DỮ LIỆU BAN ĐẦU (SEED BASELINE)")
        print("=" * 80)
        print(f"• Đã lưu vết {count} video hiện tại vào cơ sở dữ liệu (KHÔNG gửi tin nhắn).")
        print("• Từ thời điểm này, chỉ video MỚI XUẤT XƯỞNG mới được thông báo về Telegram.")
        print("=" * 80 + "\n")
        return

    # 8. Chế độ quét 1 lần
    if args.scan_once:
        logger.info("Chế độ: QUÉT 1 LẦN (Single Scan)")
        count = engine.scan_once(
            machine=args.machine,
            tiktok_channel=args.channel,
            dry_run=args.dry_run,
        )
        logger.info(f"Hoàn thành lệnh quét 1 lần. Phát hiện {count} video mới.")
        return

    # 9. Chế độ chạy liên tục (Scheduler)
    engine.run_scheduler(
        interval_seconds=args.interval,
        machine=args.machine,
        tiktok_channel=args.channel,
    )


if __name__ == "__main__":
    main()
