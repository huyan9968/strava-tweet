from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageFilter, ImageOps
import os, random, math, urllib.request, sys

# ── Nature background photos (Unsplash, stable URLs) ──────────────────────────
BG_PHOTOS = [
    'https://images.unsplash.com/photo-1441974231531-c6227db76b6e?w=1080&q=90',
    'https://images.unsplash.com/photo-1476611338391-6f395a0dd82e?w=1080&q=90',
    'https://images.unsplash.com/photo-1465188162913-8fb5709d6d57?w=1080&q=90',
    'https://images.unsplash.com/photo-1518173946687-a4c8892bbd9f?w=1080&q=90',
    'https://images.unsplash.com/photo-1502082553048-f009c37129b9?w=1080&q=90',
]

# ── Witty captions ────────────────────────────────────────────────────────────
CAPTIONS = {
    'tiny':   ["今天就意思意思，别在意", "出门就是赢家，管它几公里",
               "三公里，聊胜于没", "今天的任务：出门。完成！",
               "小试牛刀，下次再说", "我在「认真热身」，请尊重"],
    'short':  ["四公里换一杯奶茶，血赚！", "跑完了，今晚加餐有底气了",
               "不多不少，刚好把自己跑废", "五公里以内，我还是人",
               "只有装备是专业的，其他全是弱", "有氧0分，出门100分"],
    'medium': ["阿姨，我不想跑步了！", "腿已经不认识我了",
               "跑完才发现，自己可能有点傻", "散步数据，虚报里程",
               "跑步使人快乐，但我不快乐", "心率高得一塌糊涂，可能鞋子的锅",
               "汗水换来的，只有更多汗水", "比蜗牛还慢，但我在动"],
    'long':   ["别人跑步有红包，凭啥我没有！", "十公里，今晚睡觉腿自己动",
               "有病！为什么要跑这么远！", "身体废了，但打卡必须有",
               "十公里，腿的葬礼已预约", "除了打卡啥都干不成了",
               "HR 爆表，猝死边缘徘徊"],
    'insane': ["医生说要锻炼，没说要要命！", "这人有问题（指我自己）",
               "半马在逃，我在追，全完了", "只有装备是专业的，其他一塌糊涂",
               "半马选手，脑子不太好", "跑了这么远，今天能吃两碗饭"],
}
FAST_CAPTIONS = ["今天在飞，这不是跑步这是逃命！", "配速炸裂，腿不是我的了！",
                 "这配速，我自己都不敢相信"]
SLOW_CAPTIONS = ["散步plus，别拆穿我", "慢跑派，享受生活慢慢来",
                 "配速嘛，慢就慢点，心态最重要"]

# Side-comment pool — small annotations scattered around
SIDE_COMMENTS = [
    "只有装备是专业的", "伪跑鞋在逃", "心跳爆表", "比蜗牛还慢",
    "汗臭味爆汗怪", "有氧0分", "纯靠意志力", "腿：我不认识你",
    "重如铅软脚虾", "每步都是信仰", "跑量骗自己", "上坡要人命",
]


def get_witty_caption(distance_km, pace_sec=None):
    if pace_sec and pace_sec < 270:
        return random.choice(FAST_CAPTIONS)
    if pace_sec and pace_sec > 420:
        return random.choice(SLOW_CAPTIONS)
    if distance_km < 3:   pool = CAPTIONS['tiny']
    elif distance_km < 5: pool = CAPTIONS['short']
    elif distance_km < 10:pool = CAPTIONS['medium']
    elif distance_km < 15:pool = CAPTIONS['long']
    else:                  pool = CAPTIONS['insane']
    return random.choice(pool)


# ── Fonts ─────────────────────────────────────────────────────────────────────
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
    for p in candidates:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                continue
    return ImageFont.load_default()


# ── Formatters ────────────────────────────────────────────────────────────────
def fmt_duration(sec):
    h = sec // 3600; m = (sec % 3600) // 60; s = sec % 60
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m}'{s:02d}\""

def fmt_pace(speed_ms):
    if not speed_ms: return "--"
    sec = 1000 / speed_ms
    return f"{int(sec//60)}'{int(sec%60):02d}\"/km"


# ── Background ────────────────────────────────────────────────────────────────
def load_nature_bg(W, H, cache_path='/tmp/nature_bg_cached.jpg'):
    try:
        url = random.choice(BG_PHOTOS)
        urllib.request.urlretrieve(url, cache_path)
        bg = Image.open(cache_path).convert('RGB')
    except Exception as e:
        print(f"背景下载失败，使用纯色背景: {e}", file=sys.stderr)
        bg = Image.new('RGB', (W, H), (80, 120, 60))

    # Resize + crop to fill target size
    bg_ratio  = bg.width / bg.height
    tgt_ratio = W / H
    if bg_ratio > tgt_ratio:
        new_h = H; new_w = int(H * bg_ratio)
    else:
        new_w = W; new_h = int(W / bg_ratio)
    bg = bg.resize((new_w, new_h), Image.LANCZOS)
    left = (new_w - W) // 2; top = (new_h - H) // 2
    bg = bg.crop((left, top, left + W, top + H))

    # Cartoon filter: saturate + posterize + smooth
    bg = ImageEnhance.Color(bg).enhance(1.8)
    bg = ImageEnhance.Contrast(bg).enhance(1.15)
    bg = ImageOps.posterize(bg, 5)
    bg = bg.filter(ImageFilter.SMOOTH)
    return bg


# ── Rotated annotation ────────────────────────────────────────────────────────
def paste_rotated(base, text, cx, cy, angle, font, fg, bg_fill=None, strike=False):
    """Draw text rotated at `angle` degrees, centered at (cx, cy)."""
    tmp_size = 1200
    tmp = Image.new('RGBA', (tmp_size, tmp_size), (0, 0, 0, 0))
    td  = ImageDraw.Draw(tmp)

    bb  = td.textbbox((0, 0), text, font=font)
    tw, th = bb[2]-bb[0], bb[3]-bb[1]
    tx, ty = (tmp_size-tw)//2, (tmp_size-th)//2

    if bg_fill:
        pad = 12
        td.rounded_rectangle([tx-pad, ty-pad, tx+tw+pad, ty+th+pad],
                              radius=10, fill=bg_fill)
    td.text((tx, ty), text, font=font, fill=fg)
    if strike:
        mid_y = ty + th // 2
        td.line([(tx-4, mid_y), (tx+tw+4, mid_y)], fill=fg, width=4)

    tmp = tmp.rotate(angle, resample=Image.BICUBIC)
    ox  = cx - tmp_size // 2
    oy  = cy - tmp_size // 2
    base.alpha_composite(tmp, (ox, oy))


# ── Arrow decoration ──────────────────────────────────────────────────────────
def draw_arrow(draw, x1, y1, x2, y2, color, width=3):
    draw.line([(x1, y1), (x2, y2)], fill=color, width=width)
    angle = math.atan2(y2-y1, x2-x1)
    for a in [angle + 2.5, angle - 2.5]:
        draw.line([(x2, y2), (x2 - 18*math.cos(a), y2 - 18*math.sin(a))],
                  fill=color, width=width)


# ── Main card ─────────────────────────────────────────────────────────────────
def create_xhs_card(distance_km, duration_sec, speed_ms,
                    heart_rate=None, calories=None, date_str=None,
                    output_path='/tmp/xhs_card.png'):
    W, H = 1080, 1350

    # Background
    bg   = load_nature_bg(W, H)
    base = bg.convert('RGBA')

    # Light white fog overlay — keeps text readable
    fog  = Image.new('RGBA', (W, H), (255, 255, 255, 55))
    base = Image.alpha_composite(base, fog)

    # Drawing layer
    draw = ImageDraw.Draw(base)

    # ── Fonts ─────────────────────────────────────────
    f_huge    = find_font(200, bold=True)
    f_km      = find_font(52,  bold=True)
    f_ann     = find_font(44,  bold=True)   # annotations
    f_side    = find_font(32)               # small side comments
    f_caption = find_font(82,  bold=True)
    f_tag     = find_font(30)
    f_date    = find_font(34)

    pace_sec = (1000 / speed_ms) if speed_ms else None

    # ── Date stamp ────────────────────────────────────
    if date_str:
        draw.text((50, 44), date_str, font=f_date, fill=(255, 255, 255),
                  stroke_width=3, stroke_fill=(0, 0, 0))

    # ── Big distance (center-top, slight tilt) ────────
    dist_str = f"{distance_km:.1f}"
    bb = draw.textbbox((0,0), dist_str, font=f_huge)
    dw, dh = bb[2]-bb[0], bb[3]-bb[1]
    paste_rotated(base, dist_str, W//2, 320, -3, f_huge,
                  fg=(255,255,255), bg_fill=None)
    # "KM" under it
    paste_rotated(base, "KM", W//2+dw//2-30, 430, -3, f_km,
                  fg=(255, 230, 50))

    draw = ImageDraw.Draw(base)  # refresh after alpha_composite calls

    # ── Scattered stat annotations ────────────────────
    RED    = (220,  50,  50)
    GREEN  = ( 30, 140,  60)
    BLUE   = ( 30,  80, 200)
    ORANGE = (220, 120,  20)
    BLACK  = ( 20,  20,  20)
    WHITE_BG = (255, 255, 255, 210)

    # Time — top-left, tilted left
    paste_rotated(base,
                  f"时长  {fmt_duration(duration_sec)}",
                  200, 600, -12, f_ann, fg=BLACK, bg_fill=(255,255,255,200))
    draw_arrow(ImageDraw.Draw(base), 300, 630, 380, 600, GREEN)

    # Pace — top-right, tilted right
    pace_label = fmt_pace(speed_ms)
    paste_rotated(base,
                  f"配速  {pace_label}",
                  820, 580, 10, f_ann, fg=BLACK, bg_fill=(255,255,255,200))

    # Heart rate — left side
    hr_text = f"心率  {int(heart_rate)} bpm" if heart_rate else "心率  未记录"
    paste_rotated(base, hr_text, 210, 760, -8, f_ann, fg=RED,
                  bg_fill=(255, 240, 240, 210))

    # Calories — right side
    cal_text = f"消耗  {int(calories)} 大卡" if calories else "消耗  未记录"
    paste_rotated(base, cal_text, 840, 730, 6, f_ann, fg=ORANGE,
                  bg_fill=(255, 248, 230, 210))

    # Two random side comments (small, scattered)
    comments = random.sample(SIDE_COMMENTS, 2)
    paste_rotated(base, comments[0], 180, 920, -15, f_side,
                  fg=GREEN, bg_fill=(220,255,220,180))
    paste_rotated(base, comments[1], 870, 870, 18,  f_side,
                  fg=BLUE,  bg_fill=(220,230,255,180))

    # ── "打卡完成" stamp ───────────────────────────────
    draw = ImageDraw.Draw(base)
    f_stamp = find_font(38, bold=True)
    paste_rotated(base, "打卡完成 ✓", W-160, 120, 15, f_stamp,
                  fg=(200,30,30), bg_fill=None)

    # ── Big humorous caption (bottom banner) ──────────
    caption  = get_witty_caption(distance_km, pace_sec)
    banner_y = 1020
    banner_h = 120

    # Banner background
    banner = Image.new('RGBA', (W, banner_h), (0, 0, 0, 0))
    bd     = ImageDraw.Draw(banner)
    bd.rectangle([0, 0, W, banner_h], fill=(255, 200, 0, 230))
    base.alpha_composite(banner, (0, banner_y))

    draw = ImageDraw.Draw(base)

    # Auto-shrink caption font
    cap_font = f_caption; cap_size = 82
    while cap_size > 38:
        cb = draw.textbbox((0,0), caption, font=cap_font)
        if (cb[2]-cb[0]) <= W - 60:
            break
        cap_size -= 4
        cap_font = find_font(cap_size, bold=True)

    cb = draw.textbbox((0,0), caption, font=cap_font)
    cw = cb[2]-cb[0]
    # Shadow
    draw.text((W//2 - cw//2 + 3, banner_y + (banner_h - (cb[3]-cb[1]))//2 + 3),
              caption, font=cap_font, fill=(160, 80, 0))
    # Main
    draw.text((W//2 - cw//2, banner_y + (banner_h - (cb[3]-cb[1]))//2),
              caption, font=cap_font, fill=(30, 20, 0))

    # ── Hashtags ──────────────────────────────────────
    tags = "#跑步  #运动打卡  #跑步打卡  #今日份运动"
    draw.text((W//2, 1175), tags, font=f_tag, fill=(255,255,255),
              anchor='ma', stroke_width=2, stroke_fill=(0,0,0))

    # ── Via Strava ────────────────────────────────────
    f_foot = find_font(28)
    draw.text((W//2, H-40), "via Strava", font=f_foot, fill=(200,200,200),
              anchor='ma', stroke_width=1, stroke_fill=(0,0,0))

    base.convert('RGB').save(output_path, quality=95)
    return output_path


# ── Text caption for XHS / Twitter ───────────────────────────────────────────
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
