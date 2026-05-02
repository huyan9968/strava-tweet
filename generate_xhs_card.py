from PIL import Image, ImageDraw, ImageFont
import os
import random
import math

# ── Witty captions ────────────────────────────────────────────────────────────

CAPTIONS = {
    'tiny': [
        "今天就意思意思，别在意",
        "出门就是赢家，管它几公里",
        "三公里以内，我叫它「热身」",
        "三公里，聊胜于没",
        "今天的任务：出门。完成！",
        "小试牛刀，下次再说",
        "我在「认真热身」，请尊重",
    ],
    'short': [
        "四公里换一杯奶茶，血赚！",
        "跑完了，今晚加餐有底气了",
        "不多不少，刚好把自己跑废",
        "五公里以内，我还是人",
        "跑量在增，体重未知",
        "只有装备是专业的，其他全是弱",
        "有氧0分，出门100分",
    ],
    'medium': [
        "阿姨，我不想跑步了！",
        "腿已经不认识我了",
        "跑完才发现，自己可能有点傻",
        "散步数据，虚报里程",
        "跑步使人快乐，但我不快乐",
        "心率高得一塌糊涂，可能鞋子的锅",
        "汗水换来的，只有更多汗水",
        "比蜗牛还慢，但我在动",
    ],
    'long': [
        "别人跑步有红包，凭啥我没有！",
        "十公里，今晚睡觉腿自己动",
        "有病！为什么要跑这么远！",
        "身体废了，但打卡必须有",
        "十公里，腿的葬礼已预约",
        "除了打卡啥都干不成了",
        "HR 爆表，猝死边缘徘徊",
    ],
    'insane': [
        "医生说要锻炼，没说要要命！",
        "这人有问题（指我自己）",
        "半马在逃，我在追，全完了",
        "只有装备是专业的，其他一塌糊涂",
        "半马选手，脑子不太好",
        "跑了这么远，今天能吃两碗饭",
    ],
}

FAST_CAPTIONS = [
    "今天在飞，这不是跑步这是逃命！",
    "配速炸裂，腿不是我的了！",
    "这配速，我自己都不敢相信",
]

SLOW_CAPTIONS = [
    "散步plus，别拆穿我",
    "慢跑派，享受生活慢慢来",
    "配速嘛，慢就慢点，心态最重要",
]


def get_witty_caption(distance_km, pace_sec_per_km=None):
    if pace_sec_per_km and pace_sec_per_km < 270:   # < 4:30/km
        return random.choice(FAST_CAPTIONS)
    if pace_sec_per_km and pace_sec_per_km > 420:   # > 7:00/km
        return random.choice(SLOW_CAPTIONS)
    if distance_km < 3:
        return random.choice(CAPTIONS['tiny'])
    elif distance_km < 5:
        return random.choice(CAPTIONS['short'])
    elif distance_km < 10:
        return random.choice(CAPTIONS['medium'])
    elif distance_km < 15:
        return random.choice(CAPTIONS['long'])
    else:
        return random.choice(CAPTIONS['insane'])


# ── Font helper ───────────────────────────────────────────────────────────────

def find_font(size, bold=False):
    candidates = [
        '/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc' if bold
            else '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',
        '/usr/share/fonts/noto-cjk/NotoSansCJK-Regular.ttc',
        '/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc',
        '/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc',
        '/System/Library/Fonts/PingFang.ttc',
        '/System/Library/Fonts/STHeiti Medium.ttc',
    ]
    for path in candidates:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                continue
    return ImageFont.load_default()


# ── Formatters ────────────────────────────────────────────────────────────────

def fmt_duration(sec):
    h = sec // 3600
    m = (sec % 3600) // 60
    s = sec % 60
    if h > 0:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m}'{s:02d}\""


def fmt_pace(speed_ms):
    if not speed_ms or speed_ms == 0:
        return "--"
    sec = 1000 / speed_ms
    return f"{int(sec // 60)}'{int(sec % 60):02d}\"/km"


# ── Background drawing ────────────────────────────────────────────────────────

def draw_night_bg(img):
    """Dark navy-to-black gradient with subtle speed lines."""
    draw = ImageDraw.Draw(img)
    W, H = img.size

    # Vertical gradient
    for y in range(H):
        t = y / H
        r = int(8  * (1 - t) + 2  * t)
        g = int(12 * (1 - t) + 4  * t)
        b = int(35 * (1 - t) + 10 * t)
        draw.line([(0, y), (W, y)], fill=(r, g, b))

    # Horizontal speed lines (decorative)
    for i in range(60):
        y   = 200 + i * 18
        x0  = int(W * 0.05 * math.sin(i * 0.7))
        ln  = int(W * (0.15 + 0.25 * ((i * 17) % 10) / 10))
        lum = 25 + (i * 11) % 20
        draw.line([(x0, y), (x0 + ln, y)], fill=(lum, lum + 15, lum + 40), width=1)


def draw_city_silhouette(draw, W, H):
    """Simple pixel city at the very bottom."""
    # (x_start, width, height)
    BLOCKS = [
        (0,   75, 220), (80,  60, 165), (145, 80, 290), (230, 55, 195),
        (290, 90, 325), (385, 60, 240), (450, 75, 265), (530, 55, 185),
        (590, 85, 305), (680, 60, 215), (745, 80, 275), (830, 50, 172),
        (885, 90, 310), (980, 60, 205), (1045,35, 250),
    ]
    FILL = (5, 7, 16)
    WIN  = (255, 215, 80)

    for bx, bw, bh in BLOCKS:
        top = H - bh
        draw.rectangle([bx, top, bx + bw, H], fill=FILL)
        # Windows — deterministic grid, some lit up
        for wy in range(top + 18, H - 22, 28):
            for wx in range(bx + 10, bx + bw - 10, 18):
                if (wx * 7 + wy * 3) % 5 != 0:
                    draw.rectangle([wx, wy, wx + 8, wy + 12], fill=WIN)


def draw_glow(draw, cx, cy, radius, color):
    """Paint a radial glow dot."""
    for r in range(radius, 0, -4):
        alpha = int(80 * (1 - r / radius))
        c = tuple(min(255, v + alpha) for v in color[:3])
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=c)


# ── Main card ─────────────────────────────────────────────────────────────────

def create_xhs_card(distance_km, duration_sec, speed_ms,
                    heart_rate=None, calories=None, date_str=None,
                    output_path='/tmp/xhs_card.png'):

    W, H = 1080, 1350

    # ── Step 1: RGB background ────────────────────────
    img  = Image.new('RGB', (W, H), (8, 12, 35))
    draw_night_bg(img)
    draw = ImageDraw.Draw(img)

    # Decorative glow spots (top-right and bottom-left, subtle)
    draw_glow(draw, W - 80, 120, 100, (20, 45, 160))
    draw_glow(draw, 60,     H - 280, 80, (60, 20, 140))

    # City silhouette
    draw_city_silhouette(draw, W, H)

    # ── Step 2: RGBA compositing for glass card ───────
    img  = img.convert('RGBA')
    card = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    cd   = ImageDraw.Draw(card)

    CX, CY, CW, CH = 60, 60, W - 120, 680
    cd.rounded_rectangle(
        [CX, CY, CX + CW, CY + CH],
        radius=28,
        fill=(8, 18, 55, 195),
    )
    cd.rounded_rectangle(
        [CX, CY, CX + CW, CY + CH],
        radius=28,
        outline=(70, 120, 255, 140),
        width=2,
    )
    img  = Image.alpha_composite(img, card)
    draw = ImageDraw.Draw(img)

    # ── Step 3: Stats content inside card ─────────────
    f_date    = find_font(30)
    f_huge    = find_font(230, bold=True)
    f_km      = find_font(54)
    f_val     = find_font(68, bold=True)
    f_lbl     = find_font(34)
    f_cal     = find_font(38, bold=True)
    f_caption = find_font(80, bold=True)
    f_tag     = find_font(30)
    f_foot    = find_font(28)

    BLUE_LIGHT = (150, 180, 255)
    WHITE      = (255, 255, 255)
    ORANGE     = (255, 170,  50)
    YELLOW     = (255, 215,  50)
    MUTED      = (70,  90, 130)

    # Date top-left
    if date_str:
        draw.text((CX + 30, CY + 22), date_str, font=f_date, fill=BLUE_LIGHT)

    # Divider under date
    draw.rectangle([CX + 30, CY + 62, CX + CW - 30, CY + 64], fill=(50, 70, 140))

    # Huge distance number
    dist_str = f"{distance_km:.1f}"
    bb  = draw.textbbox((0, 0), dist_str, font=f_huge)
    dw  = bb[2] - bb[0]
    draw.text((W // 2 - dw // 2, CY + 68), dist_str, font=f_huge, fill=WHITE)

    # KM unit
    bb2 = draw.textbbox((0, 0), "KM", font=f_km)
    draw.text((W // 2 - (bb2[2] - bb2[0]) // 2, CY + 300), "KM", font=f_km, fill=BLUE_LIGHT)

    # Three secondary stats
    pace_sec = (1000 / speed_ms) if speed_ms else None
    stats = [
        ("时  长", fmt_duration(duration_sec)),
        ("配  速", fmt_pace(speed_ms)),
        ("心  率", f"{int(heart_rate)} bpm" if heart_rate else "--"),
    ]
    col_w = CW // 3
    stat_y = CY + 395

    for i, (lbl, val) in enumerate(stats):
        cx = CX + i * col_w + col_w // 2

        lb = draw.textbbox((0, 0), lbl, font=f_lbl)
        draw.text((cx - (lb[2] - lb[0]) // 2, stat_y), lbl, font=f_lbl, fill=BLUE_LIGHT)

        vb = draw.textbbox((0, 0), val, font=f_val)
        draw.text((cx - (vb[2] - vb[0]) // 2, stat_y + 46), val, font=f_val, fill=WHITE)

        if i < 2:
            draw.rectangle(
                [CX + (i + 1) * col_w - 1, stat_y, CX + (i + 1) * col_w + 1, stat_y + 130],
                fill=(50, 70, 140),
            )

    # Calories strip at bottom of card
    if calories:
        cal_text = f"本次消耗  {int(calories)} 大卡"
        cb  = draw.textbbox((0, 0), cal_text, font=f_cal)
        draw.text((W // 2 - (cb[2] - cb[0]) // 2, CY + CH - 72),
                  cal_text, font=f_cal, fill=ORANGE)

    # ── Step 4: Big humorous caption ──────────────────
    caption = get_witty_caption(distance_km, pace_sec)
    cap_y   = CY + CH + 55

    # Auto-shrink font to fit within card width
    cap_font = f_caption
    cap_size = 80
    while cap_size > 40:
        cb = draw.textbbox((0, 0), caption, font=cap_font)
        if (cb[2] - cb[0]) <= W - 80:
            break
        cap_size -= 4
        cap_font = find_font(cap_size, bold=True)

    cb = draw.textbbox((0, 0), caption, font=cap_font)
    cw = cb[2] - cb[0]
    cx = W // 2 - cw // 2

    # Shadow
    draw.text((cx + 4, cap_y + 4), caption, font=cap_font, fill=(160, 50, 0))
    # Main
    draw.text((cx, cap_y), caption, font=cap_font, fill=YELLOW)

    # ── Step 5: Hashtags ──────────────────────────────
    tags = "#跑步  #运动打卡  #跑步打卡  #今日份运动"
    tb   = draw.textbbox((0, 0), tags, font=f_tag)
    draw.text((W // 2 - (tb[2] - tb[0]) // 2, cap_y + 100), tags, font=f_tag, fill=MUTED)

    # ── Step 6: Footer ────────────────────────────────
    draw.text((W // 2, H - 55), "via Strava", font=f_foot, fill=(45, 60, 90), anchor='ma')

    # ── Save ──────────────────────────────────────────
    img.convert('RGB').save(output_path, quality=95)
    return output_path


# ── XHS text caption ──────────────────────────────────────────────────────────

def get_xhs_text_caption(distance_km, duration_sec, speed_ms,
                          heart_rate=None, calories=None):
    pace_sec = (1000 / speed_ms) if speed_ms else None
    witty    = get_witty_caption(distance_km, pace_sec)
    hr_str   = f"{int(heart_rate)} bpm" if heart_rate else "未记录"
    cal_str  = f"{int(calories)} 大卡" if calories else "未记录"

    return f"""{witty} !!

今日跑步数据 ↓
📍 距离：{distance_km:.1f} 公里
⏱️ 时长：{fmt_duration(duration_sec)}
🏃 配速：{fmt_pace(speed_ms)}
❤️ 心率：{hr_str}
🔥 消耗：{cal_str}

#跑步 #运动打卡 #跑步打卡 #健身打卡 #晨跑 #夜跑"""
