"""
Test suite cho TikTok US Hashtag Generator
Kiểm tra độ chính xác, độ phủ 14 ngách của 22 máy và định dạng 1-tap copy HTML.
"""

import sys
import unittest
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from src.utils.hashtag_generator import (
    generate_tiktok_hashtags,
    format_hashtags_for_telegram,
    clean_text,
)


class TestHashtagGenerator(unittest.TestCase):

    def test_gym_prank_anatoly(self):
        """Kiểm tra video giả dạng lao công Anatoly / Gym Prank."""
        title = "JANITOR vs THE BIGGEST GUY IN THE GYM. Anatoly Didn't Expect THAT"
        niche = "Thử thách Thể hình & Giả dạng Người lạ Thử tạ (Gym Pranks & Strength)"
        tags = generate_tiktok_hashtags(title, niche)

        self.assertGreaterEqual(len(tags), 2)
        self.assertLessEqual(len(tags), 3)
        self.assertIn("#gymprank", tags)
        self.assertIn("#anatoly", tags)

    def test_military_us_marines(self):
        """Kiểm tra video Thủy quân lục chiến US Marines."""
        title = "Can You Spot the FAKE Marine? Military Challenge"
        niche = "Thử thách Thể lực Quân đội, Leo núi & Strongman (Strength Challenges)"
        tags = generate_tiktok_hashtags(title, niche)

        self.assertGreaterEqual(len(tags), 2)
        self.assertLessEqual(len(tags), 3)
        self.assertIn("#usmarines", tags)

    def test_navy_seal_diver(self):
        """Kiểm tra video lính thủy đánh bộ Navy Diver."""
        title = "This is Why You Don't Mess with a US Navy Diver!"
        niche = "Thử thách Thể lực Quân đội"
        tags = generate_tiktok_hashtags(title, niche)

        self.assertTrue(any(t in tags for t in ["#navyseal", "#militarytok", "#navydiver"]))

    def test_police_bodycam(self):
        """Kiểm tra video Cảnh sát thực thi pháp luật & Bodycam."""
        title = "Fleeing Suspect Arrested After High Speed Pursuit"
        niche = "Thực thi Pháp luật & Phân tích Tội phạm Qua Bodycam (Bodycam & Police Encounters)"
        tags = generate_tiktok_hashtags(title, niche)

        self.assertIn("#bodycam", tags)
        self.assertTrue(any(t in tags for t in ["#policeactivity", "#policechase", "#arrested"]))

    def test_plane_crash_simulation(self):
        """Kiểm tra video mô phỏng tai nạn hàng không 3D."""
        title = "Boeing 737 Emergency Landing After Complete Engine Failure"
        niche = "[3D] Mô phỏng Tai nạn Hàng không & Giải mã Kỹ thuật (3D Aviation & Engineering Sim)"
        tags = generate_tiktok_hashtags(title, niche)

        self.assertTrue(any(t in tags for t in ["#aviation", "#aviationdaily", "#emergencylanding", "#boeing"]))

    def test_car_restoration(self):
        """Kiểm tra video chế tạo & phục hồi siêu xe phế liệu."""
        title = "Restoring an Abandoned Twin Turbo Supercar After 10 Years"
        niche = "Chế tạo Quái thú Cơ khí & Phục hồi Siêu xe Phế liệu (Insane Car Builds & Fabrication)"
        tags = generate_tiktok_hashtags(title, niche)

        self.assertIn("#carbuild", tags)
        self.assertTrue(any(t in tags for t in ["#carguy", "#carrestoration"]))

    def test_steak_wagyu(self):
        """Kiểm tra video ẩm thực Steak Wagyu."""
        title = "I Cooked an A5 Wagyu Ribeye Steak with Bone Marrow Butter"
        niche = "Thử thách Chế biến Thịt Bò Cao cấp & Thực nghiệm Ẩm thực (Steak Experiments & Cooking)"
        tags = generate_tiktok_hashtags(title, niche)

        self.assertIn("#wagyu", tags)
        self.assertIn("#steaktok", tags)

    def test_dinosaur_kaiju_battle(self):
        """Kiểm tra video quái thú khủng long tiền sử."""
        title = "T-Rex vs Spinosaurus Death Match"
        niche = "[3D] Mô phỏng Khoa học Đấu Quái thú & Khủng long Tiền sử (Kaiju & Prehistoric Battles)"
        tags = generate_tiktok_hashtags(title, niche)

        self.assertTrue(any(t in tags for t in ["#trexbattle", "#dinosaurs", "#monsterbattle"]))

    def test_calisthenics_pullup(self):
        """Kiểm tra video Calisthenics đường phố."""
        title = "Impossible 50 Pullups in 60 Seconds Record"
        niche = "Calisthenics Đường phố & Kỷ lục Tốc độ/Sức bền (Calisthenics & Endurance)"
        tags = generate_tiktok_hashtags(title, niche)

        self.assertIn("#pullups", tags)
        self.assertIn("#calisthenics", tags)

    def test_heavy_wrecker_mud(self):
        """Kiểm tra video cứu hộ xe tải nặng trong đầm lầy."""
        title = "Heavy Rotator Wrecker Recovers Semi Truck Sunk in Deep Mud"
        niche = "Cứu hộ Xe Địa hình Đầm lầy & Trục vớt Xe Tai nạn (Heavy Wrecker & Mud Recovery)"
        tags = generate_tiktok_hashtags(title, niche)

        self.assertIn("#mudrecovery", tags)
        self.assertIn("#heavywrecker", tags)

    def test_format_hashtags_for_telegram(self):
        """Kiểm tra định dạng 1-tap copy bọc thẻ code."""
        tags = ["#gymprank", "#anatoly", "#gymtok"]
        html_str = format_hashtags_for_telegram(tags)
        self.assertEqual(html_str, "<code>#gymprank #anatoly #gymtok</code>")

        # Rỗng
        self.assertEqual(format_hashtags_for_telegram([]), "")

    def test_tag_integrity(self):
        """Đảm bảo mọi hashtag sinh ra đều đúng chuẩn TikTok (# và viết thường)."""
        tags = generate_tiktok_hashtags("Some Random Video Title Without Keywords", "Unknown Niche")
        self.assertGreaterEqual(len(tags), 2)
        self.assertLessEqual(len(tags), 3)
        for t in tags:
            self.assertTrue(t.startswith("#"))
            self.assertEqual(t, t.lower())


if __name__ == "__main__":
    unittest.main()
