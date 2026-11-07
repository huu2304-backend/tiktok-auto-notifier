"""
TikTok Beta US Automation Notifier - Smart TikTok US Hashtag Generator
======================================================================
Tự động sinh 2 - 3 thẻ Hashtag TikTok US (thị trường Mỹ) phù hợp chuẩn với
từng nội dung video cụ thể, bóc tách từ Tiêu đề (Title) và Ngách (Niche) của 22 máy.
Tối ưu hóa thuật toán đề xuất FYP (For You Page) & TikTok SEO Creator Rewards Program.
"""

import re
import html
from typing import List, Optional, Tuple, Dict, Set


# Bộ từ điển ánh xạ từ khóa (Keywords) sang danh sách Hashtag TikTok US chuẩn
# Phân loại theo 14 nhóm ngành đặc thù của 22 máy
NICHE_RULES = [
    {
        "id": "police_bodycam",
        "niche_patterns": [r"bodycam", r"police", r"tội phạm", r"pháp luật", r"law"],
        "title_keywords": {
            r"\b(bodycam|dashcam)\b": ["#bodycam", "#policeactivity"],
            r"\b(police|cop|cops|officer|sheriff)\b": ["#policeactivity", "#lawandorder"],
            r"\b(arrest|arrested|cuffed|handcuff)\b": ["#bodycam", "#arrested"],
            r"\b(chase|pursuit|flee|fleeing)\b": ["#policechase", "#bodycam"],
            r"\b(traffic stop|dui|drunk)\b": ["#trafficstop", "#bodycam"],
            r"\b(k9|dog)\b": ["#k9unit", "#policeactivity"],
            r"\b(swat|raid|hostage)\b": ["#swat", "#policeactivity"],
        },
        "default_tags": ["#bodycam", "#policeactivity", "#lawandorder"],
    },
    {
        "id": "military_survival",
        "niche_patterns": [r"quân đội", r"marine", r"sinh tồn", r"military", r"navy", r"strongman"],
        "title_keywords": {
            r"\b(marine|marines)\b": ["#usmarines", "#militaryfitness"],
            r"\b(navy|seal|seals|diver)\b": ["#navyseal", "#militarytok"],
            r"\b(soldier|army|military|bootcamp)\b": ["#militarytok", "#strengthchallenge"],
            r"\b(survive|survival|wilderness)\b": ["#survivalchallenge", "#wilderness"],
            r"\b(ultramarathon|marathon|endurance)\b": ["#ultramarathon", "#running"],
            r"\b(fake marine|imposter|veteran)\b": ["#military", "#usmarines"],
            r"\b(women vs|girl|girls)\b": ["#strengthchallenge", "#militaryfitness"],
        },
        "default_tags": ["#usmarines", "#militarytok", "#strengthchallenge"],
    },
    {
        "id": "gym_prank_strength",
        "niche_patterns": [r"thể hình", r"giả dạng", r"gym prank", r"thử tạ", r"strength"],
        "title_keywords": {
            r"\b(janitor|anatoly|cleaner)\b": ["#gymprank", "#anatoly"],
            r"\b(prank|pranks|pretend|fake)\b": ["#gymprank", "#gymtok"],
            r"\b(armwrestling|armwrestl)\b": ["#armwrestling", "#strength"],
            r"\b(bench press|benchpress|100kg|200kg|strict curl)\b": ["#gymtok", "#benchpress"],
            r"\b(bodybuilder|bodybuilding|muscle)\b": ["#bodybuilding", "#gymtok"],
            r"\b(resort|luxury gym)\b": ["#fitnessresort", "#gymtok"],
            r"\b(leg day|squat|deadlift)\b": ["#legday", "#gymtok"],
            r"\b(natty|steroid|dopamine)\b": ["#gymtok", "#fitnessmotivation"],
        },
        "default_tags": ["#gymtok", "#gymprank", "#fitnesschallenge"],
    },
    {
        "id": "calisthenics",
        "niche_patterns": [r"calisthenics", r"sức bền", r"street workout"],
        "title_keywords": {
            r"\b(pullup|pull up|pullups)\b": ["#pullups", "#calisthenics"],
            r"\b(pushup|push up|pushups)\b": ["#pushups", "#calisthenics"],
            r"\b(muscleup|muscle up)\b": ["#muscleup", "#streetworkout"],
            r"\b(handstand|planche|lever)\b": ["#calisthenics", "#streetworkout"],
            r"\b(record|kỷ lục|speed)\b": ["#calisthenics", "#worldrecord"],
        },
        "default_tags": ["#calisthenics", "#streetworkout", "#workoutmotivation"],
    },
    {
        "id": "heavy_recovery",
        "niche_patterns": [r"cứu hộ", r"xe tải", r"đầm lầy", r"tuyết lún", r"wrecker", r"recovery"],
        "title_keywords": {
            r"\b(mud|swamp|boggled|sink|sinking)\b": ["#mudrecovery", "#heavywrecker"],
            r"\b(snow|ice|frozen|winter)\b": ["#snowrecovery", "#heavywrecker"],
            r"\b(rollover|roll over|flipped|crash)\b": ["#heavywrecker", "#rollover"],
            r"\b(semi|semi truck|rig|big rig|18 wheeler)\b": ["#heavywrecker", "#trucktok"],
            r"\b(rotator|winch|tow|towing|wrecker)\b": ["#heavywrecker", "#towing"],
            r"\b(offroad|4x4|trail)\b": ["#offroadrecovery", "#mudbogging"],
        },
        "default_tags": ["#heavywrecker", "#mudrecovery", "#trucktok"],
    },
    {
        "id": "car_builds",
        "niche_patterns": [r"siêu xe", r"quái thú cơ khí", r"phế liệu", r"car build", r"fabrication", r"chế tạo xe"],
        "title_keywords": {
            r"\b(barn find|abandoned|rust|rusty)\b": ["#barnfind", "#carrestoration"],
            r"\b(restoration|restore|rebuild)\b": ["#carrestoration", "#carguy"],
            r"\b(turbo|engine|v8|swap|exhaust)\b": ["#carbuild", "#carguy"],
            r"\b(fabrication|weld|welding|metal)\b": ["#fabrication", "#carbuild"],
            r"\b(supercar|ferrari|lamborghini|porsche)\b": ["#supercar", "#carbuild"],
            r"\b(drift|burnout|race)\b": ["#driftcar", "#carguy"],
        },
        "default_tags": ["#carbuild", "#carguy", "#fabrication"],
    },
    {
        "id": "physics_science",
        "niche_patterns": [r"vật lý", r"hiện tượng", r"thí nghiệm", r"physics", r"science", r"vũ khí viễn tưởng"],
        "title_keywords": {
            r"\b(hydraulic|press|crush)\b": ["#hydraulicpress", "#oddlysatisfying"],
            r"\b(physics|gravity|quantum|speed of light)\b": ["#physicsfun", "#scienceexperiments"],
            r"\b(laser|plasma|beam)\b": ["#laser", "#creativeinventions"],
            r"\b(weapon|sword|gun|armor|shield)\b": ["#scifi", "#creativeinventions"],
            r"\b(experiment|experiments|tested)\b": ["#scienceexperiments", "#mindblown"],
            r"\b(diy|build|handmade|homemade)\b": ["#diyproject", "#engineering"],
        },
        "default_tags": ["#scienceexperiments", "#physicsfun", "#mindblown"],
    },
    {
        "id": "aviation_sim",
        "niche_patterns": [r"hàng không", r"aviation", r"plane crash", r"mô phỏng tai nạn"],
        "title_keywords": {
            r"\b(crash|crashed|disaster|mayday)\b": ["#planecrash", "#aviationdaily"],
            r"\b(emergency landing|gear up|engine failure)\b": ["#emergencylanding", "#aviation"],
            r"\b(boeing|airbus|737|777|747|a380|a320)\b": ["#aviationdaily", "#boeing"],
            r"\b(pilot|atc|cockpit|blackbox)\b": ["#cockpit", "#aviation"],
            r"\b(simulation|sim|msfs|xplane)\b": ["#flightsimulator", "#3danimation"],
        },
        "default_tags": ["#aviationdaily", "#planecrash", "#3danimation"],
    },
    {
        "id": "kaiju_monsters",
        "niche_patterns": [r"quái thú", r"khủng long", r"tiền sử", r"kaiju", r"dinosaur"],
        "title_keywords": {
            r"\b(t-rex|trex|tyrannosaurus)\b": ["#trexbattle", "#dinosaurs"],
            r"\b(spinosaurus|velociraptor|raptor|carnotaurus)\b": ["#dinosaurs", "#jurassicworld"],
            r"\b(godzilla|kong|king kong|kaiju)\b": ["#godzilla", "#monsterbattle"],
            r"\b(megalodon|shark|kraken|sea monster)\b": ["#megalodon", "#monsterbattle"],
            r"\b(battle|vs|fight|arena)\b": ["#monsterbattle", "#jurassic"],
        },
        "default_tags": ["#dinosaurs", "#jurassic", "#monsterbattle"],
    },
    {
        "id": "animation_storytime",
        "niche_patterns": [r"hoạt hình", r"kể chuyện", r"châm biếm", r"animation", r"storytime"],
        "title_keywords": {
            r"\b(storytime|story|stories)\b": ["#storytime", "#animationmeme"],
            r"\b(school|teacher|childhood|growing up)\b": ["#relatable", "#animationmeme"],
            r"\b(funny|humor|comedy|lol)\b": ["#cartoontok", "#funnyanimation"],
            r"\b(animated|cartoon|drawing)\b": ["#animation", "#cartoontok"],
        },
        "default_tags": ["#storytime", "#animationmeme", "#cartoontok"],
    },
    {
        "id": "steak_cooking",
        "niche_patterns": [r"thịt bò", r"ẩm thực", r"steak", r"bbq", r"chế biến"],
        "title_keywords": {
            r"\b(wagyu|a5|kobe)\b": ["#wagyu", "#steaktok"],
            r"\b(dry age|dry aged|dry-aged|dryage)\b": ["#dryaged", "#steaktok"],
            r"\b(steak|ribeye|tomahawk|filet)\b": ["#steaktok", "#meatlover"],
            r"\b(brisket|bbq|smoked|smoker|ribs)\b": ["#bbqtok", "#carnivore"],
            r"\b(butter|sear|crust|sous vide)\b": ["#steaktok", "#foodtok"],
        },
        "default_tags": ["#steaktok", "#bbqtok", "#meatlover"],
    },
    {
        "id": "parkour_stunts",
        "niche_patterns": [r"parkour", r"nhào lộn", r"mạo hiểm", r"rooftop"],
        "title_keywords": {
            r"\b(roof|rooftop|building|skyscraper|heights)\b": ["#roofclimbing", "#parkour"],
            r"\b(escape|security|guards|chase)\b": ["#parkour", "#adrenaline"],
            r"\b(flip|flips|backflip|jump|climb)\b": ["#freerunning", "#acrobatics"],
            r"\b(extreme|insane|dangerous)\b": ["#extreme", "#parkour"],
        },
        "default_tags": ["#parkour", "#freerunning", "#acrobatics"],
    },
    {
        "id": "viral_stunts_challenges",
        "niche_patterns": [r"thử thách", r"hộp kín", r"trốn tìm", r"24 giờ", r"stunt", r"extreme"],
        "title_keywords": {
            r"\b(24 hour|24 hours|24h)\b": ["#24hourschallenge", "#viralchallenge"],
            r"\b(trapped|box|locked in|escape)\b": ["#escapechallenge", "#viralstunt"],
            r"\b(hide and seek|hide & seek|secret room)\b": ["#hideandseek", "#secretroom"],
            r"\b(mrbeast|giant|million|dollar|\$)\b": ["#viralchallenge", "#mrbeast"],
            r"\b(survive|survived|impossible)\b": ["#viralchallenge", "#extremestunt"],
        },
        "default_tags": ["#viralchallenge", "#extremestunt", "#fyp"],
    },
    {
        "id": "lifestyle_vlog",
        "niche_patterns": [r"vlog", r"nữ sinh", r"nhiếp ảnh", r"lifestyle", r"makeover"],
        "title_keywords": {
            r"\b(room makeover|makeover|decor|bedroom)\b": ["#roommakeover", "#aesthetic"],
            r"\b(photo|photography|camera|portrait)\b": ["#streetphotography", "#viralphoto"],
            r"\b(teen|high school|college|routine)\b": ["#teenlifestyle", "#vlogus"],
            r"\b(haul|shopping|thrift|grwm)\b": ["#grwm", "#lifestyle"],
        },
        "default_tags": ["#roommakeover", "#teenlifestyle", "#vlogus"],
    },
]


def clean_text(text: Optional[str]) -> str:
    """Loại bỏ ký tự HTML và chuyển về chữ thường chuẩn."""
    if not text:
        return ""
    unescaped = html.unescape(str(text))
    return unescaped.lower().strip()


def extract_keywords_from_title(title: str, title_keywords_map: Dict[str, List[str]]) -> List[str]:
    """Tìm kiếm các hashtag phù hợp từ các biểu thức chính quy trong tiêu đề."""
    matched_tags: List[str] = []
    title_lower = title.lower()

    for pattern, tags in title_keywords_map.items():
        if re.search(pattern, title_lower, re.IGNORECASE):
            for t in tags:
                if t not in matched_tags:
                    matched_tags.append(t)
    return matched_tags


def generate_tiktok_hashtags(
    video_title: str,
    niche: str = "",
    machine_name: str = "",
    limit: int = 3,
) -> List[str]:
    """
    Sinh 2 - 3 thẻ Hashtag TikTok US chuẩn nhất dựa trên Tiêu đề và Ngách của máy.
    Trả về danh sách thẻ chuẩn (ví dụ: ['#gymprank', '#anatoly', '#gymtok']).
    """
    selected_tags: List[str] = []
    title_clean = clean_text(video_title)
    niche_clean = clean_text(niche)

    # 1. Tìm quy tắc ngách khớp nhất từ NICHE_RULES
    matched_rule = None
    for rule in NICHE_RULES:
        # Kiểm tra theo niche của cấu hình máy
        for pattern in rule["niche_patterns"]:
            if re.search(pattern, niche_clean, re.IGNORECASE):
                matched_rule = rule
                break
        if matched_rule:
            break

    # Nếu không tìm thấy qua niche, thử nhận diện qua tiêu đề video
    if not matched_rule:
        for rule in NICHE_RULES:
            matched = False
            for pattern in rule["title_keywords"].keys():
                if re.search(pattern, title_clean, re.IGNORECASE):
                    matched_rule = rule
                    matched = True
                    break
            if matched:
                break

    # 2. Trích xuất tag dựa trên từ khóa trong tiêu đề
    if matched_rule:
        title_tags = extract_keywords_from_title(title_clean, matched_rule["title_keywords"])
        for tag in title_tags:
            if tag not in selected_tags:
                selected_tags.append(tag)

        # 3. Bổ sung default tags từ ngách nếu chưa đủ
        for tag in matched_rule["default_tags"]:
            if len(selected_tags) >= limit:
                break
            if tag not in selected_tags:
                selected_tags.append(tag)

    # 4. Dự phòng toàn cục nếu vẫn chưa đủ 2-3 tag
    global_fallbacks = ["#tiktokusa", "#fyp", "#viralvideo"]
    for fb in global_fallbacks:
        if len(selected_tags) >= limit:
            break
        if fb not in selected_tags:
            selected_tags.append(fb)

    # Đảm bảo tối thiểu 2 tag và tối đa `limit` tag (mặc định 3)
    result = selected_tags[:limit]
    if len(result) < 2:
        result.append("#fyp")

    # Chuẩn hóa format viết thường và bắt đầu bằng dấu #
    formatted_result = []
    for t in result:
        clean_tag = t.strip()
        if not clean_tag.startswith("#"):
            clean_tag = f"#{clean_tag}"
        formatted_result.append(clean_tag.lower())

    return formatted_result


def format_hashtags_for_telegram(hashtags: List[str]) -> str:
    """
    Định dạng danh sách hashtag thành chuỗi HTML bọc trong thẻ <code>.
    Giúp người dùng trên điện thoại chỉ cần chạm 1 lần là sao chép được toàn bộ.
    Ví dụ: <code>#gymprank #anatoly #gymtok</code>
    """
    if not hashtags:
        return ""
    joined = " ".join(hashtags)
    return f"<code>{html.escape(joined)}</code>"
