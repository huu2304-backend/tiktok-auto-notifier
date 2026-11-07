"""
TikTok Beta US Automation Notifier - Timezone & Time Formatting Utilities
========================================================================
Xử lý chuyển đổi thời gian sang múi giờ Việt Nam (Asia/Ho_Chi_Minh - GMT+7).
Cung cấp định dạng thời gian thực tế kèm thời gian tương đối (ví dụ: 15 phút trước).
"""

from datetime import datetime, timezone, timedelta
from typing import Optional

# Múi giờ Việt Nam: UTC+7
VIETNAM_TZ = timezone(timedelta(hours=7))


def parse_iso_datetime(dt_str: Optional[str]) -> Optional[datetime]:
    """Parse chuỗi datetime ISO 8601 linh hoạt."""
    if not dt_str:
        return None
    s = str(dt_str).strip()
    if s.endswith("Z") or s.endswith("z"):
        s = s[:-1] + "+00:00"
    try:
        return datetime.fromisoformat(s)
    except Exception:
        pass

    for fmt in (
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%d %H:%M:%S%z",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d",
    ):
        try:
            return datetime.strptime(s, fmt)
        except Exception:
            continue
    return None


def format_vietnam_time(dt_str: Optional[str], include_relative: bool = True) -> str:
    """
    Chuyển đổi chuỗi UTC ISO sang Giờ Việt Nam (GMT+7).
    Ví dụ: '21:30 07/11/2026 (45 phút trước)'
    """
    dt = parse_iso_datetime(dt_str)
    if not dt:
        return str(dt_str) if dt_str else "Không rõ"

    # Nếu dt là naive (không có timezone), mặc định là UTC
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)

    # Chuyển đổi sang múi giờ Việt Nam
    dt_vn = dt.astimezone(VIETNAM_TZ)
    vn_str = dt_vn.strftime("%H:%M %d/%m/%Y")

    if not include_relative:
        return f"{vn_str} (Giờ VN)"

    # Tính thời gian tương đối so với hiện tại
    now_vn = datetime.now(VIETNAM_TZ)
    diff = now_vn - dt_vn
    total_seconds = int(diff.total_seconds())

    if total_seconds < 0:
        relative_str = "Vừa xong"
    elif total_seconds < 60:
        relative_str = f"{total_seconds} giây trước"
    elif total_seconds < 3600:
        mins = max(1, total_seconds // 60)
        relative_str = f"{mins} phút trước"
    elif total_seconds < 86400:
        hours = total_seconds // 3600
        relative_str = f"{hours} giờ trước"
    elif total_seconds < 86400 * 30:
        days = total_seconds // 86400
        relative_str = f"{days} ngày trước"
    else:
        relative_str = "Hơn 1 tháng trước"

    return f"{vn_str} ({relative_str})"
