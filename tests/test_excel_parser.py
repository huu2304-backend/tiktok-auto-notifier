"""
Test suite cho Dynamic Excel Parser
Kiểm tra khả năng nhận diện cột động, lọc theo Máy và lọc theo Kênh TikTok.
"""

import sys
from pathlib import Path

# Thêm thư mục gốc dự án vào PYTHONPATH
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from src.parser.excel_parser import ExcelConfigParser, ChannelConfig


def test_parser():
    parser = ExcelConfigParser()
    configs = parser.parse()

    print(f"Tổng số cấu hình kênh nạp được: {len(configs)}")
    assert len(configs) >= 4, "Phải đọc được ít nhất 4 kênh mẫu!"

    # In chi tiết từng cấu hình
    for c in configs:
        print(f"\n--- {c.display_tag} ---")
        print(f"  • Máy: {c.machine_name}")
        print(f"  • Kênh TikTok: {c.tiktok_channel}")
        print(f"  • Tình trạng: {c.status_bkt} (BKT={c.is_bkt()})")
        print(f"  • Chủ đề: {c.niche}")
        print(f"  • Số nguồn YouTube: {len(c.youtube_sources)}")
        for idx, src in enumerate(c.youtube_sources, 1):
            print(f"     [Nguồn {idx}]: {src}")

    # Test lọc theo máy: "Máy 01"
    may_01_channels = parser.get_channels(machine="Máy 01")
    print(f"\n[Test Lọc Máy 01] Số kênh thuộc Máy 01: {len(may_01_channels)}")
    assert len(may_01_channels) == 2, "Máy 01 phải có chính xác 2 kênh!"

    # Test lọc theo kênh: "tech_insider"
    tech_channels = parser.get_channels(tiktok_channel="tech_insider")
    print(f"[Test Lọc Kênh TikTok] Kết quả: {len(tech_channels)} kênh ({tech_channels[0].tiktok_channel})")
    assert len(tech_channels) == 1

    # Test Gom nhóm nguồn (Mapping)
    source_map = parser.get_sources_mapping()
    print(f"\n[Test Source Mapping] Tổng số nguồn YouTube độc nhất: {len(source_map)}")

    print("\n✅ TẤT CẢ CÁC BÀI TEST PARSER ĐỀU VƯỢT QUA XUẤT SẮC!")


if __name__ == "__main__":
    test_parser()
