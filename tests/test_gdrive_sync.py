"""
Test suite cho Google Drive Synchronizer
Kiểm tra bóc tách Sheet ID và quy trình backup/sync.
"""

import sys
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from src.sync.gdrive_sync import GoogleSheetSync


class TestGoogleSheetSync(unittest.TestCase):

    def setUp(self):
        self.test_excel = BASE_DIR / "data" / "test_sync_channels.xlsx"
        self.syncer = GoogleSheetSync(target_excel_path=self.test_excel)

    def tearDown(self):
        if self.test_excel.exists():
            self.test_excel.unlink()
        bak = self.test_excel.with_suffix(".bak.xlsx")
        if bak.exists():
            bak.unlink()
        tmp = self.test_excel.with_suffix(".tmp.xlsx")
        if tmp.exists():
            tmp.unlink()

    def test_extract_sheet_id(self):
        """Kiểm tra trích xuất ID từ nhiều định dạng URL Google Sheets."""
        # Dạng URL đầy đủ
        url1 = "https://docs.google.com/spreadsheets/d/1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms/edit?usp=sharing"
        self.assertEqual(self.syncer.extract_sheet_id(url1), "1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms")

        # Dạng URL export
        url2 = "https://docs.google.com/spreadsheets/d/1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms/export?format=csv"
        self.assertEqual(self.syncer.extract_sheet_id(url2), "1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms")

        # Dạng ID thuần
        id_raw = "1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms"
        self.assertEqual(self.syncer.extract_sheet_id(id_raw), id_raw)

        # URL không hợp lệ
        self.assertIsNone(self.syncer.extract_sheet_id("https://google.com/invalid"))

    @patch("src.sync.gdrive_sync.requests.Session.get")
    def test_sync_csv_fallback(self, mock_get):
        """Kiểm tra sync qua định dạng CSV khi tải về thành công."""
        # Giả lập phản hồi CSV có cấu trúc chuẩn
        sample_csv = (
            "Tên Máy,Tài Khoản TikTok,Tình Trạng,Cụm Chủ Đề,Nguồn 1\n"
            "Máy 01 - test,user_test,BKT,Niche 1,https://youtube.com/@source1\n"
        )
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.content = b"Not XLSX"
        mock_resp.text = sample_csv
        mock_get.return_value = mock_resp

        success, msg, count = self.syncer.sync("1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms")
        self.assertTrue(success)
        self.assertEqual(count, 1)
        self.assertTrue(self.test_excel.exists())


if __name__ == "__main__":
    unittest.main()
