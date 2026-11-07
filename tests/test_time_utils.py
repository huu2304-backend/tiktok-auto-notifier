"""
Test suite cho Timezone & Time Formatting Utilities
Kiểm tra parse ISO 8601 và chuyển đổi sang Giờ Việt Nam (GMT+7).
"""

import sys
import unittest
from datetime import datetime, timezone, timedelta
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from src.utils.time_utils import (
    parse_iso_datetime,
    format_vietnam_time,
    VIETNAM_TZ,
)


class TestTimeUtils(unittest.TestCase):

    def test_parse_iso_datetime(self):
        """Kiểm tra parse datetime với nhiều định dạng ISO."""
        # ISO with Z
        dt = parse_iso_datetime("2026-11-07T12:00:00Z")
        self.assertIsNotNone(dt)
        self.assertEqual(dt.tzinfo, timezone.utc)
        self.assertEqual(dt.hour, 12)

        # ISO with offset
        dt2 = parse_iso_datetime("2026-11-07T19:00:00+07:00")
        self.assertIsNotNone(dt2)
        self.assertEqual(dt2.hour, 19)

        # None hoặc chuỗi rỗng
        self.assertIsNone(parse_iso_datetime(None))
        self.assertIsNone(parse_iso_datetime(""))
        self.assertIsNone(parse_iso_datetime("invalid-date-string"))

    def test_format_vietnam_time(self):
        """Kiểm tra chuyển đổi UTC sang múi giờ Việt Nam (UTC+7)."""
        # UTC 18:00 ngày 06/11 -> Giờ VN 01:00 ngày 07/11
        res = format_vietnam_time("2026-11-06T18:00:00Z", include_relative=False)
        self.assertEqual(res, "01:00 07/11/2026 (Giờ VN)")

        # Định dạng kèm thời gian tương đối
        now_vn = datetime.now(VIETNAM_TZ)
        recent_iso = (now_vn - timedelta(minutes=15)).astimezone(timezone.utc).isoformat()
        res_rel = format_vietnam_time(recent_iso, include_relative=True)
        self.assertIn("15 phút trước", res_rel)

    def test_format_vietnam_time_fallback(self):
        """Kiểm tra fallback an toàn khi truyền dữ liệu sai."""
        self.assertEqual(format_vietnam_time(None), "Không rõ")
        self.assertEqual(format_vietnam_time("not-a-date"), "not-a-date")


if __name__ == "__main__":
    unittest.main()
