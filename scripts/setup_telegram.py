"""
TikTok Beta US Automation Notifier - Trợ Lý Cài Đặt Telegram Tự Động
=====================================================================
Hướng dẫn từng bước lấy Bot Token từ @BotFather, tự động phát hiện Chat ID
khi bạn gửi tin nhắn, lưu thẳng vào file .env và bắn tin nhắn test thử nghiệm.
"""

import os
import sys
import time
import requests
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
ENV_FILE = BASE_DIR / ".env"


def update_env_file(token: str, chat_id: str, thread_id: str = "") -> None:
    """Cập nhật hoặc ghi đè TELEGRAM_BOT_TOKEN và TELEGRAM_CHAT_ID trong file .env."""
    lines = []
    if ENV_FILE.exists():
        with open(ENV_FILE, "r", encoding="utf-8") as f:
            lines = f.readlines()

    token_found = False
    chat_found = False
    thread_found = False
    new_lines = []

    for line in lines:
        if line.startswith("TELEGRAM_BOT_TOKEN="):
            new_lines.append(f"TELEGRAM_BOT_TOKEN={token}\n")
            token_found = True
        elif line.startswith("TELEGRAM_CHAT_ID="):
            new_lines.append(f"TELEGRAM_CHAT_ID={chat_id}\n")
            chat_found = True
        elif line.startswith("TELEGRAM_MESSAGE_THREAD_ID="):
            new_lines.append(f"TELEGRAM_MESSAGE_THREAD_ID={thread_id}\n")
            thread_found = True
        else:
            new_lines.append(line)

    if not token_found:
        new_lines.append(f"TELEGRAM_BOT_TOKEN={token}\n")
    if not chat_found:
        new_lines.append(f"TELEGRAM_CHAT_ID={chat_id}\n")
    if not thread_found and thread_id:
        new_lines.append(f"TELEGRAM_MESSAGE_THREAD_ID={thread_id}\n")

    with open(ENV_FILE, "w", encoding="utf-8") as f:
        f.writelines(new_lines)


def main():
    print("\n" + "=" * 70)
    print("🤖 TRỢ LÝ THIẾT LẬP KẾT NỐI TELEGRAM BOT TỰ ĐỘNG 🤖")
    print("=" * 70)

    print("\n📌 BƯỚC 1: LẤY BOT TOKEN TỪ @BotFather (Mất 30 giây)")
    print("  1. Mở ứng dụng Telegram trên điện thoại hoặc máy tính.")
    print("  2. Tìm kiếm: @BotFather (chọn tài khoản có tích xanh chính chủ).")
    print("  3. Nhấn START và gửi lệnh: /newbot")
    print("  4. Nhập Tên hiển thị cho Bot (Ví dụ: TikTok Beta US Notifier)")
    print("  5. Nhập Username cho Bot (phải kết thúc bằng chữ 'bot', VD: my_tiktok_beta_bot)")
    print("  6. @BotFather sẽ gửi cho bạn đoạn mã Token có dạng:")
    print("     7812345678:AAHjklQweRtyUiOp1234567890\n")

    token = input("👉 Hãy DÁN (Paste) mã Bot Token vào đây rồi nhấn Enter: ").strip()

    if not token:
        print("\n❌ Bạn chưa nhập Token! Chương trình dừng lại.")
        return

    # 1. Kiểm tra Token với Telegram API
    print("\nĐang kiểm tra tính hợp lệ của Bot Token...")
    try:
        resp = requests.get(f"https://api.telegram.org/bot{token}/getMe", timeout=15)
        data = resp.json()
        if not data.get("ok"):
            print(f"\n❌ Token không hợp lệ! Lỗi từ Telegram: {data.get('description')}")
            return
        bot_user = data["result"]["username"]
        bot_first_name = data["result"].get("first_name", "")
        print(f"✅ Token chuẩn xác! Đã kết nối với Bot: {bot_first_name} (@{bot_user})")
    except Exception as e:
        print(f"\n❌ Lỗi kết nối mạng tới Telegram API: {e}")
        return

    # 2. Hướng dẫn lấy Chat ID tự động
    print("\n" + "-" * 70)
    print("📌 BƯỚC 2: TỰ ĐỘNG PHÁT HIỆN CHAT ID CỦA BẠN")
    print(f"  👉 Bây giờ bạn mở Telegram, tìm bot @{bot_user}")
    print(f"  👉 Bấm nút START (hoặc gửi bất kỳ tin nhắn nào như 'xin chao' cho bot)")
    print("-" * 70)
    print("⏳ Đang chờ tin nhắn từ bạn (Hệ thống tự động phát hiện trong 60s)...")

    # Xóa các update cũ để chỉ bắt tin nhắn mới
    try:
        requests.get(f"https://api.telegram.org/bot{token}/getUpdates?offset=-1", timeout=10)
    except Exception:
        pass

    chat_id = None
    user_name = ""
    thread_id = ""

    for second in range(1, 61):
        try:
            up_resp = requests.get(f"https://api.telegram.org/bot{token}/getUpdates", timeout=10)
            up_data = up_resp.json()
            if up_data.get("ok") and up_data.get("result"):
                # Lấy tin nhắn mới nhất
                last_msg = up_data["result"][-1]
                msg_obj = last_msg.get("message") or last_msg.get("channel_post")
                if msg_obj and "chat" in msg_obj:
                    chat_id = str(msg_obj["chat"]["id"])
                    user_name = (
                        msg_obj["chat"].get("first_name")
                        or msg_obj["chat"].get("title")
                        or msg_obj.get("from", {}).get("first_name", "Bạn")
                    )
                    # Nếu là tin nhắn trong Topic của Group Forum
                    if "message_thread_id" in msg_obj:
                        thread_id = str(msg_obj["message_thread_id"])
                    break
        except Exception:
            pass

        time.sleep(1)
        if second % 5 == 0:
            print(f"   ...vẫn đang lắng nghe ({second}/60s)")

    if not chat_id:
        print("\n❌ Hết thời gian chờ mà chưa nhận được tin nhắn!")
        print(f"   Vui lòng đảm bảo bạn đã mở @{bot_user} trên Telegram và bấm START.")
        print("   Sau đó bạn có thể chạy lại file này bất kỳ lúc nào để thử lại.")
        return

    print(f"\n🎉 PHÁT HIỆN THÀNH CÔNG!")
    print(f"   • Người dùng / Nhóm: {user_name}")
    print(f"   • Chat ID: {chat_id}")
    if thread_id:
        print(f"   • Topic Thread ID: {thread_id}")

    # 3. Ghi vào file .env
    update_env_file(token, chat_id, thread_id)
    print(f"\n💾 Đã lưu cấu hình tự động vào file: {ENV_FILE.resolve()}")

    # 4. Bắn tin nhắn thử nghiệm chào mừng
    print("🚀 Đang gửi tin nhắn kiểm tra tới điện thoại của bạn...")
    test_msg = (
        "🎉 <b>[KẾT NỐI THÀNH CÔNG!]</b> 🎉\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"Xin chào <b>{user_name}</b>,\n"
        "Hệ thống <b>TikTok Beta US Automation Notifier</b> đã kết nối thành công với Telegram của bạn!\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "✅ Quản lý mạng lưới: <b>22 Thiết bị / Kênh TikTok</b>\n"
        "✅ Tự động loại bỏ Shorts & Livestream\n"
        "✅ Quét nguồn YouTube không giới hạn quota API\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "👉 Khi có video mới từ các kênh YouTube đối thủ, bot sẽ lập tức báo ngay tại đây!"
    )

    payload = {
        "chat_id": chat_id,
        "text": test_msg,
        "parse_mode": "HTML",
    }
    if thread_id:
        payload["message_thread_id"] = thread_id

    try:
        send_resp = requests.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            data=payload,
            timeout=15,
        )
        if send_resp.json().get("ok"):
            print("✅ TIN NHẮN ĐÃ ĐƯỢC GỬI ĐẾN ĐIỆN THOẠI CỦA BẠN!")
            print("   Hãy mở Telegram lên để xem thông báo nhé!")
        else:
            print(f"⚠️ Gửi tin nhắn test thất bại: {send_resp.json().get('description')}")
    except Exception as e:
        print(f"⚠️ Lỗi khi gửi tin nhắn test: {e}")

    print("\n" + "=" * 70)
    print("🎉 HOÀN TẤT THIẾT LẬP! Bây giờ bạn chỉ cần bấm file 'Chay_He_Thong.bat' là xong!")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
