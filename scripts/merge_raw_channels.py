"""
Script merge dữ liệu 22 kênh thực tế vào data/config_channels.xlsx
Chuẩn hóa Tên Máy dạng: 'Máy X - {tên tài khoản}'
Làm sạch nguồn YouTube và tổ chức Nguồn 1 -> Nguồn 10.
"""

import re
from pathlib import Path
import pandas as pd
from openpyxl.styles import PatternFill, Font, Alignment, Border, Side

BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_FILE = BASE_DIR / "data" / "config_channels.xlsx"

raw_csv_data = """STT (giờ VN),Máy,Tài khoản của bạn,Link TikTok,Điều kiện,Chủ đề (Key Chuẩn hóa),Trạng thái,Nguồn 1,Nguồn 2,Nguồn 3,Nguồn 4,Nguồn 5,,,,,,,,,,,
sang,máy 7,amandfrq0mk,https://www.tiktok.com/@amandfrq0mk,BKT,"Thử thách Thể lực Quân đội, Leo núi & Strongman (Strength Challenges)",Đã đăng,https://www.youtube.com/@AustenAlexander,https://www.youtube.com/@jujimufu,https://www.youtube.com/@MagnusMidtbo,https://www.youtube.com/@MitchellHooper,https://www.youtube.com/@larrywheels,,,,,,,,,,,
sangs,Máy 14,susanpaptjd,https://www.tiktok.com/@susanpaptjd,BKT,Thử thách Thể hình & Giả dạng Người lạ Thử tạ (Gym Pranks & Strength),Đã đăng,https://www.youtube.com/@vladimirfitness,https://www.youtube.com/@WillTennyson,https://www.youtube.com/@LeonidasArkona,https://www.youtube.com/@Anatolyfitness,https://www.youtube.com/@HoustonJones,,,,,,,,,,,
sáng,máy 12,shannalambert19721,https://www.tiktok.com/@shannalambert19721,KBKT,Thử thách Biến đổi Hình thể 30 Ngày & Đọ sức Bạn bè (Fitness Challenges),Đã đăng,https://www.youtube.com/@Browney,https://www.youtube.com/@JesseJamesWest,https://www.youtube.com/@BrandonWilliamyt,https://www.youtube.com/@BuffDudes,https://www.youtube.com/@MattDoesFitness,,,,,,,,,,,
sáng,máy 10,maureenholloway2000,https://www.tiktok.com/@maureenholloway2000,KBKT,Calisthenics Đường phố & Kỷ lục Tốc độ/Sức bền (Calisthenics & Endurance),Đã đăng,https://www.youtube.com/@SirNattyOfficial/videos,https://www.youtube.com/@ChrisHeria,https://www.youtube.com/@MattChoi./videos,https://www.youtube.com/@IanBarseagle,https://www.youtube.com/@GaggiYatarov,,,,,,,,,,,
22:30:00,Máy 14,danieinypi1,https://www.tiktok.com/@danieinypi1,BKT,Thử thách Sinh tồn Hộp Kín & Trò chơi Giải thưởng Lớn (Extreme Box & High-Stakes),Chưa đăng,https://www.youtube.com/@Unspeakable,https://www.youtube.com/@CollinsKey,https://www.youtube.com/@DobreBrothers,https://www.youtube.com/@BriannaYT,https://www.youtube.com/@FaZeRug,https://www.youtube.com/@Sambucha/videos,,,,,https://www.youtube.com/@brushkovv/videos,,,,,https://www.youtube.com/@tyler.vitelli/videos
sáng,máy 5,user7081373104577,https://www.tiktok.com/@user7081373104577,KBKT,Thí nghiệm & Thử thách Đồ chơi Khổng lồ (Crazy DIY Backyard Stunts),Đã đăng,https://www.youtube.com/@CarterSharer,https://www.youtube.com/@MatthewBeem,https://www.youtube.com/@PrestonYT,https://www.youtube.com/@DanteColle,https://www.youtube.com/@GuavaJuice,,,,,,,,,,,
toi,máy 1,zeacyehsq69,https://www.tiktok.com/@zeacyehsq69,KBKT,"Thử thách Đột nhập, 24 Giờ & Trải nghiệm Xã hội (Viral Stunts & 24h Challenges)",Chưa đăng,https://www.youtube.com/@AdamPlanetary,https://www.youtube.com/@airrack,https://www.youtube.com/@ThatWasEpic11,https://www.youtube.com/@RyanTrahan,https://www.youtube.com/@BigDawsTv/videos,,,,,,,,,,,
sang,máy 13,user7628070204638,https://www.tiktok.com/@user7628070204638,KBKT,Thử thách Trốn tìm Căn phòng Bí mật & Gameshow Nhóm bạn (Hide & Seek & Group Stunts),Đã đăng,https://www.youtube.com/@StokesTwins/videos,https://www.youtube.com/@Sidemen,https://www.youtube.com/@BetaSquad,https://www.youtube.com/@NikoOmilana,https://www.youtube.com/@BrentRivera,,,,,,,,,,,
22:30:00,Máy 14(P),anthofacfm7,https://www.tiktok.com/@anthofacfm7,BKT,Cứu hộ Xe tải Hạng nặng & Kéo xe Địa hình Tuyết lún (Heavy Duty Offroad Recovery),Chưa đăng,https://www.youtube.com/@MattsOffRoadRecovery,https://www.youtube.com/@FabRats,https://www.youtube.com/@RoryIrishOffroad,https://www.youtube.com/@TrailMater,https://www.youtube.com/@MoriartyOffroad,,,,,,,,,,,
22:25 (Ohio - EST),máy 12,jillmtevige,https://www.tiktok.com/@jillmtevige,BKT,Cứu hộ Xe Địa hình Đầm lầy & Trục vớt Xe Tai nạn (Heavy Wrecker & Mud Recovery),Chưa đăng,https://www.youtube.com/@CaseyLaDelle/videos,https://www.youtube.com/@RonPratt,https://www.youtube.com/@HeavyDSparks,https://www.youtube.com/@WestenChamplin,https://www.youtube.com/@TowTruckDustin,,,,,,,,,,,
tối,máy 4,user85370113117682,https://www.tiktok.com/@user85370113117682,KBKT,Chế tạo Quái thú Cơ khí & Phục hồi Siêu xe Phế liệu (Insane Car Builds & Fabrication),Chưa đăng,https://www.youtube.com/@GrindHardPlumbingCo,https://www.youtube.com/@whistlindiesel,https://www.youtube.com/@Tavarish,https://www.youtube.com/@CleetusM,https://www.youtube.com/@RichRebuilds,,,,,,,,,,,
sang,máy 11,denisebrewer19773,https://www.tiktok.com/@denisebrewer19773,KBKT,Giải mã Hiện tượng Vật lý Kỳ lạ & Thí nghiệm Đời thực (Mind-Blowing Physics & Science),Chưa đăng,https://www.youtube.com/@Veritasium,https://www.youtube.com/@SteveMould/videos,https://www.youtube.com/@simonegiertz/videos,https://www.youtube.com/@TheKingofRandom/videos,https://www.youtube.com/@MarkRober,,,,,,,,,,,
toi,máy 11(thử nghiệm),arvisojulianxc,https://www.tiktok.com/@arvisojulianxc,KBKT,Chế tạo Vũ khí Viễn tưởng & Kỹ thuật Cơ khí Siêu phàm (Sci-Fi Engineering),Chưa đăng,https://www.youtube.com/@hacksmith,https://www.youtube.com/@Nerdforge,https://www.youtube.com/@PeterSripol,https://www.youtube.com/@Integza,https://www.youtube.com/@WilliamOsman,https://www.youtube.com/@PracticalEngineeringChannel/videos,,,https://www.youtube.com/@CrunchLabs/videos,https://www.youtube.com/@RealEngineering/videos,https://www.youtube.com/@tested/videos,,,https://www.youtube.com/@hafu/videos,,
sang,máy 1,guyredus0dx,https://www.tiktok.com/@guyredus0dx,BKT,[3D] Mô phỏng Tai nạn Hàng không & Giải mã Kỹ thuật (3D Aviation & Engineering Sim),Đã đăng,https://www.youtube.com/@Flight_RouteXplorer/videos,https://www.youtube.com/@renderedmedia-i9e/videos,https://www.youtube.com/channel/UCHIsmXnoH_kl26fxeG6Q2GA,https://www.youtube.com/@TALEYE/videos,https://www.youtube.com/@JaredOwen,,,,,,,,,,,
22:30:00,máy 15,anthonysizex,https://www.tiktok.com/@anthonysizex,KBKT,[3D] Mô phỏng Khoa học Đấu Quái thú & Khủng long Tiền sử (Kaiju & Prehistoric Battles),Chưa đăng,https://www.youtube.com/@GojiCenter,https://www.youtube.com/@ExtinctZoo,https://www.youtube.com/@DeadSound,https://www.youtube.com/@DinosaursAnimated,https://www.youtube.com/@MonsterBattlesSim,,,,,,,,,,,
sang,máy 6,beverlypar0,https://www.tiktok.com/@beverlypar0,BKT,[2D] Hoạt hình Kể chuyện Hài hước & Ký ức Tuổi thơ Mỹ (2D Storytime Animation),Chưa đăng,https://www.youtube.com/@theodd1sout/videos,https://www.youtube.com/@JaidenAnimations,https://www.youtube.com/@LetMeExplainStudios,https://www.youtube.com/@SomeThingElseYT,https://www.youtube.com/@Tabbes,,,,,,,,,,,
tói,máy 6(thử nghiệm),user5450959543827,https://www.tiktok.com/@user5450959543827,KBKT,[2D] Hoạt hình Châm biếm Tình huống Đời thường (Relatable 2D Comedy Animation),Chưa đăng,https://www.youtube.com/@tyler.vitelli,,https://www.youtube.com/@Domics,https://www.youtube.com/@nutshellanimations,https://www.youtube.com/@IceCreamSandwich,,,,,,,,,,,
20:30:00,máy 5,cecelialewis,https://www.tiktok.com/@cecelialewis,KBKT,Nhiếp ảnh 10 Giây & Thử thách Nhào lộn Đường phố (Fast Photo & Acro Challenges),Đã đăng,https://www.youtube.com/@jordanmatter,https://www.youtube.com/@SofieDossi,https://www.youtube.com/@AnnaMcNulty,https://www.youtube.com/@SalishMatterVlogs,https://www.youtube.com/@HudsonMatter,,,,,,,,,,,
toi,máy 13,user8143027240637,https://www.tiktok.com/@user8143027240637,KBKT,Nhào lộn Parkour & Thử thách Mạo hiểm Nhà cao tầng (Extreme Parkour & Stunts),Chưa đăng,https://www.youtube.com/@drewdirksen,https://www.youtube.com/@Storror,https://www.youtube.com/@NickPro,https://www.youtube.com/@TylerBlanchard,https://www.youtube.com/@BobReese,,,,,,,,,,,
toi,máy 13,josephineburgess05,https://www.tiktok.com/@josephineburgess05,KBKT,Vlog Trải nghiệm & Thử thách Nữ sinh Mỹ (Teen Lifestyle & Room Makeovers),Chưa đăng,https://www.youtube.com/@pierson,https://www.youtube.com/@KatieSigmond,https://www.youtube.com/@Tarayummy,https://www.youtube.com/@BrookeMonk,https://www.youtube.com/@AvaniGregg,,,,,,,,,,,
sang,máy 15,kprcqwldt5126,https://www.tiktok.com/@kprcqwldt5126,KBKT,Thực thi Pháp luật & Phân tích Tội phạm Qua Bodycam (Bodycam & Police Encounters),Đã đăng,https://www.youtube.com/@CodeBlueCam,https://www.youtube.com/@EWUCrimeStorytime,https://www.youtube.com/@MidwestSafety,https://www.youtube.com/@PoliceActivity,https://www.youtube.com/@AuditTheAudit,,,,,,,,,,,
toi,máy 10,tewkesboner1961,https://www.tiktok.com/@tewkesboner1961,KBKT,Thử thách Chế biến Thịt Bò Cao cấp & Thực nghiệm Ẩm thực (Steak Experiments & Cooking),Chưa đăng,https://www.youtube.com/@NickDiGiovanni,https://www.youtube.com/@JoshuaWeissman,https://www.youtube.com/@MaxtheMeatGuy,https://www.youtube.com/@GugaFoods,https://www.youtube.com/@MrMakeItHappen/videos,,,,,,,,,,,"""

import io
import csv

f = io.StringIO(raw_csv_data.strip())
reader = csv.reader(f)
header = next(reader)

clean_rows = []
max_sources = 0

for line in reader:
    if not line or len(line) < 6:
        continue

    stt_time = line[0].strip()
    raw_machine = line[1].strip()
    account = line[2].strip()
    tiktok_link = line[3].strip()
    condition = line[4].strip()  # BKT / KBKT
    niche = line[5].strip()
    status_post = line[6].strip() if len(line) > 6 else ""

    # Chuẩn hóa tên máy dạng: "Máy X - {account}"
    # Ví dụ: "máy 7" -> "Máy 7", "máy 11(thử nghiệm)" -> "Máy 11 (Thử nghiệm)"
    m_name = raw_machine
    if m_name.lower().startswith("máy "):
        num_part = m_name[4:].strip()
        m_name = f"Máy {num_part}"
    else:
        m_name = m_name.capitalize()

    formatted_machine = f"{m_name} - {account}"

    # Tài khoản TikTok chuẩn có @
    formatted_tiktok = f"@{account.lstrip('@')}"

    # Thu thập tất cả các nguồn YouTube còn lại trên dòng (loại bỏ ô rỗng)
    sources = []
    for cell in line[7:]:
        cell_str = cell.strip()
        if not cell_str:
            continue
        # Làm sạch link youtube: bỏ /videos ở đuôi
        cleaned_url = re.sub(r"/videos/?$", "", cell_str)
        if cleaned_url and cleaned_url not in sources:
            sources.append(cleaned_url)

    if len(sources) > max_sources:
        max_sources = len(sources)

    clean_rows.append(
        {
            "formatted_machine": formatted_machine,
            "formatted_tiktok": formatted_tiktok,
            "condition": condition,
            "niche": niche,
            "sources": sources,
            "status_post": status_post,
        }
    )

print(f"Tổng số dòng phân tích được: {len(clean_rows)}")
print(f"Số lượng nguồn YouTube nhiều nhất của 1 kênh: {max_sources}")

# Xây dựng bảng dữ liệu DataFrame
table_data = []
for r in clean_rows:
    row_dict = {
        "Tên Máy": r["formatted_machine"],
        "Tài Khoản TikTok": r["formatted_tiktok"],
        "Tình Trạng": r["condition"],
        "Cụm Chủ Đề": r["niche"],
    }
    # Điền từ Nguồn 1 -> Nguồn max_sources
    for i in range(1, max_sources + 1):
        col_name = f"Nguồn {i}"
        row_dict[col_name] = r["sources"][i - 1] if i <= len(r["sources"]) else ""

    row_dict["Ghi Chú"] = f"Trạng thái: {r['status_post']}" if r["status_post"] else ""
    table_data.append(row_dict)

df = pd.DataFrame(table_data)

# Đảm bảo thư mục data tồn tại
OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

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

        # Auto width
        max_len = max(len(str(val)) for val in df[col].dropna()) if not df[col].dropna().empty else 10
        header_len = len(str(col))
        col_letter = cell.column_letter
        worksheet.column_dimensions[col_letter].width = min(max(max_len, header_len) + 4, 45)

    # Body styling
    for row in worksheet.iter_rows(min_row=2, max_row=len(df) + 1, min_col=1, max_col=len(df.columns)):
        for cell in row:
            cell.font = Font(name="Calibri", size=10)
            cell.border = thin_border
            if cell.column in (1, 2, 3):  # Máy, TikTok, Tình trạng
                cell.alignment = Alignment(vertical="center")
            else:
                cell.alignment = Alignment(vertical="center")

    worksheet.row_dimensions[1].height = 28

print(f"✅ Đã merge thành công 22 kênh vào: {OUTPUT_FILE}")
