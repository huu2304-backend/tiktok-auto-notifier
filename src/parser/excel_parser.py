"""
TikTok Beta US Automation Notifier - Dynamic Excel Parser
=========================================================
Đọc cấu hình động từ file Excel (data/config_channels.xlsx).
Tự động nhận diện số lượng cột Nguồn YouTube (Nguồn 1 đến Nguồn N)
mà không cần sửa code khi thêm/bớt cột hay thiết bị.
"""

import re
import unicodedata
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
import pandas as pd

from config.settings import logger, config


def remove_accents(input_str: str) -> str:
    """Loại bỏ dấu tiếng Việt (bao gồm cả đ/Đ) để so khớp cột chính xác tuyệt đối."""
    if not input_str:
        return ""
    # Chuyển đổi đ/Đ thành d/D trước khi normalize NFD
    s = str(input_str).replace("đ", "d").replace("Đ", "d")
    nfkd_form = unicodedata.normalize('NFD', s)
    return "".join([c for c in nfkd_form if not unicodedata.combining(c)]).lower()


@dataclass
class ChannelConfig:
    """Đại diện cho cấu hình của 1 kênh TikTok trên 1 máy cụ thể."""

    machine_name: str
    tiktok_channel: str
    status_bkt: str
    niche: str
    youtube_sources: List[str] = field(default_factory=list)
    note: str = ""
    row_index: int = 0

    @property
    def display_tag(self) -> str:
        """Định danh nhanh dạng [Máy 01 | @channel]"""
        return f"[{self.machine_name} | {self.tiktok_channel}]"

    def is_bkt(self) -> bool:
        """Kiểm tra kênh đã Bật Kiếm Tiền hay chưa."""
        clean = remove_accents(self.status_bkt)
        return "bkt" in clean and "kbkt" not in clean


class ExcelConfigParser:
    """
    Parser động đọc file Excel cấu hình kênh và nguồn YouTube.
    Thiết kế mở rộng cao: linh hoạt nhận diện cột, hỗ trợ N nguồn.
    """

    # Danh sách các pattern nhận diện tên cột chuẩn (sau khi đã loại bỏ dấu tiếng Việt)
    MACHINE_COL_PATTERNS = [r"^may", r"^ten\s*may", r"^ma\s*may", r"^device", r"^machine"]
    TIKTOK_COL_PATTERNS = [r"^tai\s*khoan(\s*tiktok)?", r"^kenh(\s*tiktok)?", r"^tiktok", r"^channel"]
    STATUS_COL_PATTERNS = [r"^tinh\s*trang", r"^bkt", r"^dieu\s*kien", r"^status"]
    NICHE_COL_PATTERNS = [r"^cum\s*chu\s*de", r"^chu\s*de", r"^niche", r"^topic", r"^category"]
    SOURCE_COL_PATTERNS = [r"^nguon", r"^source", r"^yt", r"^youtube"]
    NOTE_COL_PATTERNS = [r"^ghi\s*chu", r"^note"]

    def __init__(self, excel_path: Optional[Path] = None):
        self.excel_path = Path(excel_path or config.EXCEL_PATH)
        self._cached_configs: List[ChannelConfig] = []

    def _match_column(self, col_name: str, patterns: List[str]) -> bool:
        """Kiểm tra tên cột có khớp với danh sách regex patterns không."""
        clean_name = remove_accents(str(col_name).strip())
        return any(re.search(pat, clean_name) for pat in patterns)

    def _clean_str(self, val: Any, default: str = "") -> str:
        """Làm sạch chuỗi ký tự từ ô Excel."""
        if pd.isna(val) or val is None:
            return default
        return str(val).strip()

    def parse(self, force_reload: bool = False) -> List[ChannelConfig]:
        """
        Đọc và parse toàn bộ file Excel cấu hình.
        Tự động gom tất cả các cột Nguồn 1 -> Nguồn N vào list youtube_sources.
        """
        if self._cached_configs and not force_reload:
            return self._cached_configs

        if not self.excel_path.exists():
            error_msg = f"Không tìm thấy file cấu hình Excel tại: {self.excel_path}"
            logger.error(error_msg)
            raise FileNotFoundError(error_msg)

        logger.info(f"Đang đọc file cấu hình: {self.excel_path.resolve()}")

        try:
            # Đọc toàn bộ sheet đầu tiên
            df = pd.read_excel(self.excel_path, sheet_name=0, dtype=str)
        except Exception as e:
            logger.exception(f"Lỗi khi đọc file Excel ({self.excel_path}): {e}")
            raise

        if df.empty:
            logger.warning("File Excel cấu hình không có dữ liệu (rỗng)!")
            return []

        # 1. Phân loại động các cột
        col_machine: Optional[str] = None
        col_tiktok: Optional[str] = None
        col_status: Optional[str] = None
        col_niche: Optional[str] = None
        col_note: Optional[str] = None
        source_cols: List[str] = []

        for col in df.columns:
            col_str = str(col).strip()
            if self._match_column(col_str, self.MACHINE_COL_PATTERNS) and not col_machine:
                col_machine = col
            elif self._match_column(col_str, self.TIKTOK_COL_PATTERNS) and not col_tiktok:
                col_tiktok = col
            elif self._match_column(col_str, self.STATUS_COL_PATTERNS) and not col_status:
                col_status = col
            elif self._match_column(col_str, self.NICHE_COL_PATTERNS) and not col_niche:
                col_niche = col
            elif self._match_column(col_str, self.NOTE_COL_PATTERNS) and not col_note:
                col_note = col
            elif self._match_column(col_str, self.SOURCE_COL_PATTERNS):
                source_cols.append(col)

        # 2. Kiểm tra các cột bắt buộc tối thiểu
        if not col_machine or not col_tiktok:
            raise ValueError(
                f"File Excel thiếu cột bắt buộc! Đã tìm thấy: Machine={col_machine}, TikTok={col_tiktok}. "
                f"Vui lòng đảm bảo có cột 'Tên Máy' và 'Tài khoản TikTok'."
            )

        logger.info(
            f"Nhận diện cấu trúc Excel thành công: "
            f"Máy=[{col_machine}], TikTok=[{col_tiktok}], "
            f"BKT=[{col_status or 'N/A'}], Chủ đề=[{col_niche or 'N/A'}], "
            f"Số cột Nguồn YouTube phát hiện: {len(source_cols)} cột {source_cols}"
        )

        configs: List[ChannelConfig] = []

        # 3. Quét từng dòng dữ liệu
        for idx, row in df.iterrows():
            machine_val = self._clean_str(row.get(col_machine))
            tiktok_val = self._clean_str(row.get(col_tiktok))

            # Bỏ qua dòng trống nếu cả máy và tiktok channel đều rỗng
            if not machine_val and not tiktok_val:
                continue

            status_val = self._clean_str(row.get(col_status)) if col_status else "Chưa rõ"
            niche_val = self._clean_str(row.get(col_niche)) if col_niche else "Tổng hợp"
            note_val = self._clean_str(row.get(col_note)) if col_note else ""

            # Gom tất cả các nguồn YouTube trên dòng này (bỏ qua rỗng)
            sources: List[str] = []
            for s_col in source_cols:
                raw_source = self._clean_str(row.get(s_col))
                if raw_source and raw_source not in sources:
                    sources.append(raw_source)

            config_item = ChannelConfig(
                machine_name=machine_val or "Máy Không Tên",
                tiktok_channel=tiktok_val or "Kênh Chưa Đặt Tên",
                status_bkt=status_val,
                niche=niche_val,
                youtube_sources=sources,
                note=note_val,
                row_index=int(idx) + 2,  # Số dòng trong Excel (1-based + 1 header)
            )

            configs.append(config_item)

        self._cached_configs = configs
        logger.info(f"Đã nạp thành công {len(configs)} cấu hình kênh TikTok từ Excel.")
        return configs

    def get_channels(
        self,
        machine: Optional[str] = None,
        tiktok_channel: Optional[str] = None,
        force_reload: bool = False,
    ) -> List[ChannelConfig]:
        """
        Lấy danh sách kênh, hỗ trợ lọc theo Tên Máy hoặc Tên Kênh TikTok.
        Phục vụ trực tiếp usecase 'quét kênh 1' hoặc 'quét máy 1'.
        """
        all_configs = self.parse(force_reload=force_reload)
        filtered = all_configs

        if machine:
            target_machine = machine.strip().lower()
            filtered = [c for c in filtered if target_machine in c.machine_name.lower()]

        if tiktok_channel:
            target_channel = tiktok_channel.strip().lower().lstrip("@")
            filtered = [
                c for c in filtered if target_channel in c.tiktok_channel.lower().lstrip("@")
            ]

        return filtered

    def get_unique_machines(self) -> List[str]:
        """Lấy danh sách duy nhất các Tên Máy đang có trong cấu hình."""
        configs = self.parse()
        seen = set()
        machines = []
        for c in configs:
            if c.machine_name not in seen:
                seen.add(c.machine_name)
                machines.append(c.machine_name)
        return machines

    def get_sources_mapping(self) -> Dict[str, List[ChannelConfig]]:
        """
        Gom nhóm nguồn YouTube: Mỗi nguồn YouTube trỏ về danh sách các kênh TikTok cần nhận tin.
        Kiến trúc tối ưu: 1 nguồn YouTube chỉ cần fetch RSS 1 lần, sau đó notify cho tất cả
        các kênh TikTok / Máy dùng chung nguồn đó.
        """
        configs = self.parse()
        mapping: Dict[str, List[ChannelConfig]] = {}
        for c in configs:
            for source in c.youtube_sources:
                mapping.setdefault(source, []).append(c)
        return mapping
