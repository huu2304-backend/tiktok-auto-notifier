"""
Test suite cho Dynamic Excel Parser
Kiểm tra khả năng nhận diện cột động, lọc theo Máy và làm sạch link YouTube.
"""

import sys
import unittest
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from src.parser.excel_parser import ExcelConfigParser, ChannelConfig


class TestExcelParser(unittest.TestCase):

    def setUp(self):
        self.parser = ExcelConfigParser()

    def test_clean_youtube_url(self):
        """Kiểm tra làm sạch và lọc các đường dẫn YouTube."""
        clean = self.parser.clean_youtube_url

        # 1. Link có đuôi /videos, /featured, /live
        self.assertEqual(
            clean("https://www.youtube.com/@larrywheels/videos"),
            "https://www.youtube.com/@larrywheels",
        )
        self.assertEqual(
            clean("https://www.youtube.com/@JesseJamesWest/featured"),
            "https://www.youtube.com/@JesseJamesWest",
        )

        # 2. Link có dấu chấm thừa ở cuối
        self.assertEqual(
            clean("https://www.youtube.com/@MattChoi."),
            "https://www.youtube.com/@MattChoi",
        )

        # 3. Chuỗi rác, ghi chú bỏ qua
        self.assertIsNone(clean("chưa có"))
        self.assertIsNone(clean("đang tìm"))
        self.assertIsNone(clean("N/A"))
        self.assertIsNone(clean("none"))
        self.assertIsNone(clean(""))
        self.assertIsNone(clean(None))

        # 4. Handle chuẩn
        self.assertEqual(clean("@AustenAlexander"), "@AustenAlexander")

        # 5. Direct channel id
        self.assertEqual(
            clean("UCgkzrMGEbZemPI4hkz0Z9Bw"),
            "UCgkzrMGEbZemPI4hkz0Z9Bw",
        )

    def test_parser_loads_channels(self):
        """Kiểm tra nạp dữ liệu từ file Excel hiện tại."""
        configs = self.parser.parse()
        self.assertGreaterEqual(len(configs), 4, "Phải đọc được ít nhất 4 kênh!")

        for c in configs:
            self.assertTrue(c.machine_name)
            self.assertTrue(c.tiktok_channel)
            self.assertIsInstance(c.youtube_sources, list)


if __name__ == "__main__":
    unittest.main()
