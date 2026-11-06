"""
Script tạo file Excel mẫu data/config_channels.xlsx
Chuẩn hóa các cột và định dạng bảng cho TikTok Beta US Automation Notifier.
"""

from pathlib import Path
import pandas as pd
from openpyxl.styles import PatternFill, Font, Alignment, Border, Side

BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_FILE = BASE_DIR / "data" / "config_channels.xlsx"

data = [
    {
        "Tên Máy": "Máy 01",
        "Tài Khoản TikTok": "@daily_crime_us",
        "Tình Trạng": "BKT",
        "Cụm Chủ Đề": "True Crime / Vụ Án",
        "Nguồn 1 (YouTube)": "https://www.youtube.com/@MrBallen",
        "Nguồn 2 (YouTube)": "https://www.youtube.com/@ThatChapter",
        "Nguồn 3 (YouTube)": "https://www.youtube.com/@CoffeehouseCrime",
        "Nguồn 4 (YouTube)": "https://www.youtube.com/@ExploreWithUs",
        "Ghi Chú": "Ưu tiên video dài >10p để tóm tắt 3p TikTok",
    },
    {
        "Tên Máy": "Máy 01",
        "Tài Khoản TikTok": "@us_mystery_tales",
        "Tình Trạng": "BKT",
        "Cụm Chủ Đề": "Bí Ẩn / Giả Thuyết",
        "Nguồn 1 (YouTube)": "https://www.youtube.com/@TheInfographicsShow",
        "Nguồn 2 (YouTube)": "https://www.youtube.com/@SimpleHistory",
        "Nguồn 3 (YouTube)": "https://www.youtube.com/@LEMMiNO",
        "Nguồn 4 (YouTube)": "",
        "Ghi Chú": "Dựng hình ảnh AI + Voice lồng tiếng US",
    },
    {
        "Tên Máy": "Máy 02",
        "Tài Khoản TikTok": "@tech_insider_beta",
        "Tình Trạng": "KBKT (Đang kéo 10K)",
        "Cụm Chủ Đề": "Công Nghệ / AI",
        "Nguồn 1 (YouTube)": "https://www.youtube.com/@mkbhd",
        "Nguồn 2 (YouTube)": "https://www.youtube.com/@Fireship",
        "Nguồn 3 (YouTube)": "https://www.youtube.com/@ColdFusion",
        "Nguồn 4 (YouTube)": "https://www.youtube.com/@Veritasium",
        "Ghi Chú": "Đang test khung giờ vàng US 18h-21h",
    },
    {
        "Tên Máy": "Máy 03",
        "Tài Khoản TikTok": "@wildlife_oddities",
        "Tình Trạng": "BKT",
        "Cụm Chủ Đề": "Động Vật Kỳ Lạ",
        "Nguồn 1 (YouTube)": "https://www.youtube.com/@BBC",
        "Nguồn 2 (YouTube)": "https://www.youtube.com/@NatGeo",
        "Nguồn 3 (YouTube)": "",
        "Nguồn 4 (YouTube)": "",
        "Ghi Chú": "Kênh BKT RPM cao ($0.8 - $1.2)",
    },
]

df = pd.DataFrame(data)

# Đảm bảo thư mục data tồn tại
OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

# Ghi ra Excel với openpyxl và định dạng đẹp
with pd.ExcelWriter(OUTPUT_FILE, engine="openpyxl") as writer:
    df.to_excel(writer, index=False, sheet_name="Config Channels")
    worksheet = writer.sheets["Config Channels"]

    # Header styling
    header_fill = PatternFill(start_color="1F4E79", end_color="1F4E79", fill_type="solid")
    header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
    header_align = Alignment(horizontal="center", vertical="center", wrap_text=True)

    thin_border = Border(
        left=Side(style="thin", color="D9D9D9"),
        right=Side(style="thin", color="D9D9D9"),
        top=Side(style="thin", color="D9D9D9"),
        bottom=Side(style="thin", color="D9D9D9"),
    )

    for col_idx, col in enumerate(df.columns, 1):
        cell = worksheet.cell(row=1, column=col_idx)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = header_align

        # Tự động căn chỉnh độ rộng cột
        max_len = max(len(str(val)) for val in df[col].dropna()) if not df[col].dropna().empty else 10
        header_len = len(str(col))
        col_letter = cell.column_letter
        worksheet.column_dimensions[col_letter].width = max(max_len, header_len) + 4

    # Body styling
    for row in worksheet.iter_rows(min_row=2, max_row=len(df) + 1, min_col=1, max_col=len(df.columns)):
        for cell in row:
            cell.font = Font(name="Calibri", size=10)
            cell.border = thin_border
            if cell.column in (1, 3):  # Máy, Tình trạng
                cell.alignment = Alignment(horizontal="center", vertical="center")
            else:
                cell.alignment = Alignment(vertical="center")

    worksheet.row_dimensions[1].height = 28

print(f"✅ Đã tạo file Excel cấu hình mẫu thành công tại: {OUTPUT_FILE}")
