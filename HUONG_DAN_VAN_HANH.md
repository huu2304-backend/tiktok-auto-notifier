# 📖 HƯỚNG DẪN VẬN HÀNH DỰ ÁN TIKTOK AUTO NOTIFIER

> **Tài liệu lưu trữ nhanh**: Nếu sau này bạn quên cách dùng hoặc cần sửa đổi bất kỳ thứ gì, chỉ cần mở file này xem lại hoặc gửi cho AI để được hỗ trợ ngay lập tức!

---

## 🚀 1. Các File Phím Tắt (.bat) Cho Người Dùng Windows

Trong thư mục gốc dự án, bạn có 6 file `.bat` để thao tác nhanh bằng 1 cú click đúp:

| Tên File | Chức Năng | Khi Nào Sử Dụng? |
| :--- | :--- | :--- |
| **`Khoi_Tao_Moc_Du_Lieu.bat`** | **Khởi tạo mốc cơ sở (Seed Baseline)** | **Bấm 1 lần đầu tiên** để lưu vết các video cũ vào DB mà **KHÔNG** gửi thông báo spam về Telegram. |
| **`Chay_He_Thong.bat`** | **Khởi động tự động quét liên tục 24/7** | Bấm để hệ thống chạy ngầm tự động quét video mới (mỗi 5 phút) kèm bộ nhận lệnh chat Telegram. |
| **`Chay_Telegram_Bot.bat`** | **Chạy riêng bộ lắng nghe lệnh Telegram Bot** | Bấm khi chỉ muốn bật bot tương tác điều khiển từ xa bằng điện thoại. |
| **`Dang_Ky_Nut_Telegram.bat`** | **Đăng ký Menu & Bàn phím điều khiển Telegram** | Bấm 1 lần để bot nạp Slash commands (/videos, /update, /status) và gửi bàn phím chat. |
| **`Cap_Nhat_Tu_Drive.bat`** | Đồng bộ toàn bộ kênh từ Google Sheets về máy | Bấm mỗi khi bạn vừa **thêm kênh, đổi link YouTube, hoặc chỉnh sửa trên Google Sheet**. |
| **`Bao_Cao_Tinh_Trang.bat`** | Báo cáo sức khỏe & thống kê mạng lưới | Xem tổng quan 22 máy, số nguồn YouTube hoạt động/lỗi 404, số video đã lưu trong database. |
| **`Kiem_Tra_Danh_Sach.bat`** | Xem danh sách 22 máy & nguồn YouTube hiện tại | Kiểm tra lại toàn bộ dữ liệu máy và các link nguồn đang gán cho từng máy. |
| **`Cai_Dat_Telegram.bat`** | Trợ lý kết nối Telegram tự động | Dùng khi muốn đổi bot mới hoặc kết nối nhóm chat khác. |

---

## 🔄 2. Hướng Dẫn Cập Nhật Link Google Sheets (Khi Đổi File Khác)

Nếu sau này bạn tạo một file Google Sheet mới và muốn đổi link:

1. Mở file [`.env`](.env) bằng Notepad.
2. Tìm đến dòng `GOOGLE_SHEET_URL=` và dán link mới vào:
   ```ini
   GOOGLE_SHEET_URL=https://docs.google.com/spreadsheets/d/your_new_id/edit?gid=123456#gid=123456
   ```
3. Lưu file `.env` lại.
4. Click đúp chuột vào file **`Cap_Nhat_Tu_Drive.bat`** ➔ Hệ thống sẽ tự kéo file mới về máy ngay lập tức!

> **⚠️ Lưu ý:** File Google Sheet mới luôn phải được bật quyền: **"Bất kỳ ai có đường liên kết đều có thể xem" (Viewer)**.

---

## 📱 3. Hướng Dẫn Cấu Hình Telegram Bot Nhận Thông Báo

1. Mở file [`.env`](.env) bằng Notepad.
2. Điền Token và Chat ID của bạn:
   ```ini
   TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrSTUvwxYZ
   TELEGRAM_CHAT_ID=-1001234567890
   ```
3. Chạy file **`Chay_He_Thong.bat`** để bắt đầu nhận thông báo khi có video mới ra.

---

## 🤖 4. Điều Khiển Hệ Thống Trực Tiếp Từ Điện Thoại Qua Telegram

Bạn không cần mở máy tính lên để gõ lệnh, chỉ cần mở khung chat Telegram với Bot là có thể điều khiển toàn bộ 22 máy:

### 🔘 Bàn Phím Điều Khiển Tương Tác Nhanh (Reply Keyboard)
Ngay dưới ô nhập tin nhắn của Telegram có sẵn 4 nút bấm tiện lợi:
1. **`[ 🚀 Quét Video Mới ]`** (hoặc gõ `/videos`):
   - Kích hoạt chu kỳ quét tức thì toàn bộ 22 máy & 102 nguồn YouTube.
   - Nếu có video mới, bot sẽ bắn ngay thẻ ảnh thông báo về chat và tổng kết số lượng video.
2. **`[ 🔄 Cập Nhật Google Drive ]`** (hoặc gõ `/update`):
   - Tự động tải lại Google Sheets và nạp lại cấu hình kênh mới nhất mà không cần chạm vào máy tính.
3. **`[ 📊 Xem Báo Cáo 22 Máy ]`** (hoặc gõ `/status`):
   - Xem ngay số lượng kênh BKT/KBKT, số nguồn YouTube hoạt động, tổng số video đã lưu trong database.
4. **`[ 💡 Hướng Dẫn ]`** (hoặc gõ `/help`):
   - Xem bảng hướng dẫn các lệnh và kích hoạt lại bàn phím điều khiển nếu bị ẩn.

> **🛡️ Cơ Chế Bảo Mật Whitelist:** Hệ thống chỉ chấp nhận lệnh từ chính `TELEGRAM_CHAT_ID` của bạn (`6748670298`). Bất kỳ ai khác nhắn tin cho bot đều sẽ bị từ chối truy cập!

---

## 🛠️ 5. Bảng Tra Cứu Lệnh Nhanh (Dành Cho Dòng Lệnh PowerShell)

```powershell
# Chuyển vào thư mục dự án
cd C:\Users\PC\.gemini\antigravity\scratch\tiktok-auto-notifier

# 1. Đồng bộ từ Google Drive
.\.venv\Scripts\python.exe run.py --sync-gdrive

# 2. Khởi tạo mốc cơ sở (Seed Baseline - Không spam tin cũ)
.\.venv\Scripts\python.exe run.py --seed

# 3. Báo cáo tình trạng hệ thống
.\.venv\Scripts\python.exe run.py --status

# 4. Xem danh sách máy & nguồn YouTube
.\.venv\Scripts\python.exe run.py --list-channels

# 5. Quét thử nghiệm giả lập (Dry-run không bắn tin thật)
.\.venv\Scripts\python.exe run.py --scan-once --dry-run

# 6. Quét riêng cho 1 máy cụ thể (ví dụ: máy của amandfrq0mk)
.\.venv\Scripts\python.exe run.py --scan-once --machine "amandfrq0mk"

# 7. Chạy quét thật liên tục 24/7 (mỗi 5 phút quét 1 lần)
.\.venv\Scripts\python.exe run.py

# 8. Xóa cache phân giải kênh nếu cần phân giải lại toàn bộ link
.\.venv\Scripts\python.exe run.py --clear-cache

# 9. Đăng ký Slash Commands và gửi bàn phím tương tác lên Telegram
.\.venv\Scripts\python.exe run.py --setup-bot-commands

# 10. Chạy riêng bộ lắng nghe Telegram Bot tương tác
.\.venv\Scripts\python.exe run.py --bot
```
