# TikTok Beta US Automation Notifier 🚀

Hệ thống tự động hóa cấp độ sản xuất (Production-Ready) giám sát mạng lưới nguồn YouTube và bắn thông báo thời gian thực về Telegram cho từng kênh TikTok Creator Rewards Program (Beta US) trên các dàn máy vận hành.

---

## 🌟 Tính Năng Nổi Bật

1. **Thiết kế Động 100% (Zero Hardcoding):** Toàn bộ thông tin Máy, Kênh TikTok, Tình trạng BKT, Chủ đề và danh sách Nguồn YouTube (Nguồn 1 -> Nguồn N) được cấu hình qua file `data/config_channels.xlsx`. Thêm bớt máy hay đổi nguồn không cần đụng vào code.
2. **Định Danh Ngữ Cảnh Hoàn Chỉnh (Device & Channel Attribution):** Thông báo Telegram hiển thị chính xác video mới thuộc về **Máy nào**, phục vụ **Kênh TikTok nào**, tình trạng BKT ra sao để người vận hành lấy video làm ngay.
3. **Quét Chọn Lọc (Granular / On-Demand Scanning):** Hỗ trợ quét toàn bộ mạng lưới hoặc quét riêng từng Máy / từng Kênh TikTok theo nhu cầu.
4. **Không Giới Hạn Quota YouTube API:** Sử dụng YouTube RSS kết hợp cơ chế kiểm tra redirect và metadata, không phụ thuộc vào 10,000 quota/ngày của YouTube Data API v3.
5. **Bộ Lọc Shorts Chuẩn Xác:** Tự động phát hiện và loại bỏ YouTube Shorts, chỉ lấy video dài (>3 phút hoặc cấu hình tùy chỉnh) đạt chuẩn kiếm tiền TikTok Beta US.
6. **Chống Trùng Lặp Tuyệt Đối (Idempotent SQLite Cache):** Lưu vết `video_id` đã thông báo trong `data/tracked_videos.db`.
7. **Tương Tác 2 Chiều Qua Telegram (Interactive Chat Control):** Hỗ trợ Slash commands (`/videos`, `/update`, `/status`, `/help`) và Bàn phím bấm cố định (Reply Keyboard) cho phép điều khiển quét tức thì và nạp lại Google Sheets trực tiếp từ điện thoại.
8. **Bảo Mật Whitelist:** Khóa quyền điều khiển, chỉ cho phép Chat ID được cấu hình trong `TELEGRAM_CHAT_ID` ra lệnh.

---

## 📁 Cấu Trúc Thư Mục

```text
tiktok-auto-notifier/
│
├── .env.example              # Mẫu biến môi trường (Telegram Bot Token, Chat ID...)
├── .gitignore                # Bỏ qua file cache, log, .env, db
├── README.md                 # Tài liệu hướng dẫn sử dụng
├── requirements.txt          # Danh sách thư viện Python
├── run.py                    # File khởi chạy hệ thống chính (CLI runner)
│
├── config/
│   ├── __init__.py
│   └── settings.py           # Quản lý cấu hình tập trung & Logging UTF-8
│
├── data/
│   ├── config_channels.xlsx  # File Excel cấu hình kênh (Máy, Kênh TikTok, Nguồn...)
│   └── tracked_videos.db     # SQLite database lưu cache video_id đã thông báo
│
├── src/
│   ├── __init__.py
│   ├── parser/
│   │   ├── __init__.py
│   │   └── excel_parser.py   # Bộ đọc Excel động (hỗ trợ N nguồn không giới hạn)
│   ├── fetcher/
│   │   ├── __init__.py
│   │   └── youtube_rss.py    # Quét RSS YouTube & giải mã channel/video
│   ├── notifier/
│   │   ├── __init__.py
│   │   └── telegram_bot.py   # Bắn thông báo Telegram rich format
│   └── core/
│       ├── __init__.py
│       └── engine.py         # Điều phối chu kỳ quét & chống trùng lặp
│
└── logs/
    └── app.log               # Nhật ký hoạt động hệ thống
```

---

## ⚙️ Cài Đặt & Khởi Chạy Nhanh

### 1. Cài đặt môi trường
Yêu cầu Python 3.10+ (Khuyên dùng Python 3.12 với `uv` hoặc `venv`):
```bash
# Tạo môi trường ảo
python -m venv .venv

# Kích hoạt (Windows PowerShell)
.venv\Scripts\Activate.ps1

# Cài đặt thư viện
pip install -r requirements.txt
```

### 2. Thiết lập cấu hình (.env)
Sao chép `.env.example` thành `.env` và điền thông tin Telegram:
```ini
TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrSTUvwxYZ
TELEGRAM_CHAT_ID=-1001234567890
CHECK_INTERVAL_SECONDS=300
MIN_VIDEO_DURATION_SECONDS=180
```

### 3. Cấu hình danh sách kênh trong Excel
Mở file `data/config_channels.xlsx` để cập nhật danh sách Máy, Kênh TikTok và các cột `Nguồn 1`, `Nguồn 2`, ... `Nguồn N`.

### 4. Chạy kiểm thử Parser
```bash
python tests/test_excel_parser.py
```
