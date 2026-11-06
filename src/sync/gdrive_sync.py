"""
TikTok Beta US Automation Notifier - Google Drive / Google Sheets Synchronizer
==============================================================================
Tự động đồng bộ file cấu hình kênh từ Google Sheets về data/config_channels.xlsx.
Hỗ trợ link Google Sheets chia sẻ công khai mà không cần cài đặt API phức tạp.
"""

import re
import shutil
from pathlib import Path
from typing import Optional, Tuple
import requests
import pandas as pd

from config.settings import logger, config
from src.parser.excel_parser import ExcelConfigParser


class GoogleSheetSync:
    """Đồng bộ bảng tính từ Google Sheets về file Excel cấu hình nội bộ."""

    def __init__(self, target_excel_path: Optional[Path] = None):
        self.target_path = Path(target_excel_path or config.EXCEL_PATH)
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/124.0.0.0 Safari/537.36"
                )
            }
        )

    def extract_sheet_id(self, sheet_url_or_id: str) -> Optional[str]:
        """Bóc tách Sheet ID từ URL Google Sheets bất kỳ hoặc ID thuần."""
        clean = sheet_url_or_id.strip()

        # Dạng URL đầy đủ: /spreadsheets/d/{ID}/edit...
        match = re.search(r"/spreadsheets/d/([a-zA-Z0-9-_]+)", clean)
        if match:
            return match.group(1)

        # Dạng ID thuần (chuỗi dài hơn 20 ký tự gồm chữ, số, gạch nối)
        if re.match(r"^[a-zA-Z0-9-_]{20,}$", clean):
            return clean

        return None

    def sync(self, sheet_url_or_id: str) -> Tuple[bool, str, int]:
        """
        Tải Google Sheets về và lưu đè vào data/config_channels.xlsx.
        Có cơ chế backup file cũ và validate tính toàn vẹn dữ liệu trước khi áp dụng.
        Returns: (success, message, channels_count)
        """
        sheet_id = self.extract_sheet_id(sheet_url_or_id)
        if not sheet_id:
            return False, f"URL Google Sheets không hợp lệ: {sheet_url_or_id}", 0

        logger.info(f"Đang đồng bộ từ Google Sheets ID: {sheet_id}")

        # Thử tải định dạng XLSX trực tiếp
        export_xlsx_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=xlsx"
        export_csv_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"

        temp_file = self.target_path.with_suffix(".tmp.xlsx")
        backup_file = self.target_path.with_suffix(".bak.xlsx")

        download_success = False

        # 1. Ưu tiên tải trực tiếp file XLSX
        try:
            resp = self.session.get(export_xlsx_url, timeout=20)
            if resp.status_code == 200 and resp.content[:4] == b"PK\x03\x04":  # Header zip/xlsx chuẩn
                temp_file.parent.mkdir(parents=True, exist_ok=True)
                with open(temp_file, "wb") as f:
                    f.write(resp.content)
                download_success = True
                logger.info("Đã tải thành công định dạng XLSX từ Google Sheets.")
        except Exception as e:
            logger.warning(f"Không thể tải định dạng XLSX ({e}), thử fallback sang CSV...")

        # 2. Fallback sang định dạng CSV nếu XLSX không tải được
        if not download_success:
            try:
                resp = self.session.get(export_csv_url, timeout=20)
                if resp.status_code == 200:
                    import io
                    csv_df = pd.read_csv(io.StringIO(resp.text), dtype=str)
                    temp_file.parent.mkdir(parents=True, exist_ok=True)
                    csv_df.to_excel(temp_file, index=False, engine="openpyxl")
                    download_success = True
                    logger.info("Đã tải và chuyển đổi thành công định dạng CSV sang XLSX.")
                else:
                    return (
                        False,
                        f"Không thể truy cập Google Sheets (HTTP {resp.status_code}). "
                        f"Vui lòng đảm bảo bảng tính đã bật chia sẻ 'Bất kỳ ai có đường liên kết đều có thể xem'.",
                        0,
                    )
            except Exception as e:
                logger.exception(f"Lỗi khi tải CSV từ Google Sheets: {e}")
                return False, f"Lỗi kết nối tới Google Sheets: {e}", 0

        # 3. Validate dữ liệu bằng ExcelConfigParser trước khi ghi đè
        try:
            test_parser = ExcelConfigParser(excel_path=temp_file)
            channels = test_parser.parse(force_reload=True)

            if not channels:
                if temp_file.exists():
                    temp_file.unlink()
                return False, "File Google Sheets tải về không có dữ liệu kênh hợp lệ!", 0

            # 4. Tạo bản backup an toàn trước khi thay thế
            if self.target_path.exists():
                shutil.copy2(self.target_path, backup_file)

            # 5. Áp dụng file mới
            if self.target_path.exists():
                self.target_path.unlink()
            temp_file.rename(self.target_path)

            msg = f"Đồng bộ thành công! Đã nạp {len(channels)} kênh TikTok từ Google Sheets."
            logger.info(msg)
            return True, msg, len(channels)

        except Exception as val_err:
            if temp_file.exists():
                temp_file.unlink()
            error_msg = f"Lỗi cấu trúc dữ liệu Google Sheets không tương thích: {val_err}"
            logger.exception(error_msg)
            return False, error_msg, 0
