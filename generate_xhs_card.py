from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageFilter, ImageOps
import os, random, math, urllib.request, sys

# ── Nature background photos ──────────────────────────────────────────────────
BG_PHOTOS = [
    'https://images.unsplash.com/photo-1441974231531-c6227db76b6e?w=1080&q=90',
    'https://images.unsplash.com/photo-1476611338391-6f395a0dd82e?w=1080&q=90',
    'https://images.unsplash.com/photo-1465188162913-8fb5709d6d57?w=1080&q=90',
    'https://images.unsplash.com/photo-1518173946687-a4c8892bbd9f?w=1080&q=90',
    'https://images.unsplash.com/photo-1502082553048-f009c37129b9?w=1080&q=90',
]

# ── Captions ──────────────────────────────────────────────────────────────────
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


def get_witty_caption(distance_km, pace_sec=None):
    if pace_sec and pace_sec < 270:   return random.choice(FAST_CAPTIONS)
    if pace_sec and pace_sec > 420:   return random.choice(SLOW_CAPTIONS)
    if distance_km < 3:    pool = CAPTIONS['tiny']
    elif distance_km < 5:  pool = CAPTIONS['short']
    elif distance_km < 10: pool = CAPTIONS['medium']
    elif distance_km < 15: pool = CAPTIONS['long']
    else:                   pool = CAPTIONS['insane']
    return random.choice(pool)


# ── Fonts ─────────────────────────────────────────────────────────────────────
def find_font(size, bold=False):
    candidates = [
        '/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc'    if bold else
        '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',
        '/usr/share/fonts/noto-cjk/NotoSansCJK-Regular.ttc',
        '/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc',
        '/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc',
        '/System/Library/Fonts/PingFang.ttc',
        '/System/Library/Fonts/STHeiti Medium.ttc',
    ]
    for p in candidates:
        if os.path.exists(p):
            try:   return ImageFont.truetype(p, size)
            except Exception: continue
    return ImageFont.load_default()


def fmt_duration(sec):
    h = sec // 3600; m = (sec % 3600) // 60; s = sec % 60
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m}'{s:02d}\""

def fmt_pace(speed_ms):
    if not speed_ms: return "--"
    sec = 1000 / speed_ms
    return f"{int(sec//60)}'{int(sec%60):02d}\"/km"


# ── Background ────────────────────────────────────────────────────────────────
def load_nature_bg(W, H):
    cache = '/tmp/nature_bg_latest.jpg'
    try:
        url = random.choice(BG_PHOTOS)
        urllib.request.urlretrieve(url, cache)
        bg = Image.open(cache).convert('RGB')
    except Exception as e:
        print(f"背景下载失败: {e}", file=sys.stderr)
        bg = Image.new('RGB', (W, H), (34, 85, 40))

    # Fill crop
    r = bg.width / bg.height
    t = W / H
    if r > t:
        nw, nh = int(H * r), H
    else:
        nw, nh = W, int(W / r)
    bg = bg.resize((nw, nh), Image.LANCZOS)
    bg = bg.crop(((nw - W)//2, (nh - H)//2, (nw - W)//2 + W, (nh - H)//2 + H))

    # Vivid but not posterized — keeps photo quality
    bg = ImageEnhance.Color(bg).enhance(1.4)
    bg = ImageEnhance.Contrast(bg).enhance(1.1)
    return bg


def make_gradient_overlay(W, H):
    """Cinematic gradient: slight dark at top, clears in middle, deep dark at bottom."""
    overlay = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    draw    = ImageDraw.Draw(overlay)

    for y in range(H):
        yr = y / H
        if yr < 0.18:                           # top strip: moderate dark for date
            a = int(160 * yr / 0.18)
        elif yr < 0.42:                          # clear window: photo shines
            a = int(160 * (1 - (yr - 0.18) / 0.24))
        elif yr < 0.60:                          # mid: very light overlay
            a = int(20 + 40 * (yr - 0.42) / 0.18)
        else:                                    # bottom: deep dark for text
            a = int(60 + 185 * ((yr - 0.60) / 0.40) ** 1.6)

        draw.line([(0, y), (W, y)], fill=(0, 0, 0, min(a, 245)))
    return overlay


# ── Text helpers ──────────────────────────────────────────────────────────────
def txt(draw, text, x, y, font, fill, anchor='la',
        stroke_width=0, stroke_fill=None):
    draw.text((x, y), text, font=font, fill=fill, anchor=anchor,
              stroke_width=stroke_width, stroke_fill=stroke_fill or fill)


def centered(draw, text, y, font, fill, W,
             stroke_width=0, stroke_fill=None):
    txt(draw, text, W//2, y, font, fill, anchor='ma',
        stroke_width=stroke_width, stroke_fill=stroke_fill)


def stat_block(draw, label, value, cx, y_label, f_label, f_value,
               col_clr=(200, 200, 200), val_clr=(255, 255, 255)):
    lb = draw.textbbox((0, 0), label, font=f_label)
    draw.text((cx - (lb[2]-lb[0])//2, y_label), label, font=f_label, fill=col_clr)
    vb = draw.textbbox((0, 0), value, font=f_value)
    draw.text((cx - (vb[2]-vb[0])//2, y_label + 44), value, font=f_value, fill=val_clr)


# ── Main card ─────────────────────────────────────────────────────────────────
def create_xhs_card(distance_km, duration_sec, speed_ms,
                    heart_rate=None, calories=None, date_str=None,
                    output_path='/tmp/xhs_card.png'):
    W, H    = 1080, 1350
    AMBER   = (255, 200,  50)
    WHITE   = (255, 255, 255)
    LGRAY   = (200, 200, 200)
    MGRAY   = (140, 140, 140)

    # ── Compose background + gradient ─────────────────
    bg   = load_nature_bg(W, H)
    base = Image.alpha_composite(bg.convert('RGBA'), make_gradient_overlay(W, H))
    draw = ImageDraw.Draw(base)

    pace_sec = (1000 / speed_ms) if speed_ms else None

    # ── Fonts ──────────────────────────────────────────
    f_date    = find_font(32)
    f_badge   = find_font(30, bold=True)
    f_dist    = find_font(220, bold=True)
    f_km      = find_font(52,  bold=True)
    f_caption = find_font(76,  bold=True)
    f_val     = find_font(62,  bold=True)
    f_lbl     = find_font(30)
    f_tag     = find_font(30)
    f_foot    = find_font(26)

    SW = 4   # stroke width for text on photo

    # ── DATE  (top-left) ──────────────────────────────
    if date_str:
        txt(draw, date_str, 54, 54, f_date, WHITE,
            stroke_width=2, stroke_fill=(0,0,0))

    # ── BADGE (top-right) ─────────────────────────────
    badge_text = "打卡完成  √"
    bb = draw.textbbox((0,0), badge_text, font=f_badge)
    bw, bh = bb[2]-bb[0]+28, bb[3]-bb[1]+16
    bx = W - 54 - bw;  by = 46
    draw.rounded_rectangle([bx, by, bx+bw, by+bh], radius=bh//2,
                            fill=(255,255,255,30), outline=AMBER, width=2)
    draw.text((bx+14, by+8), badge_text, font=f_badge, fill=AMBER)

    # ── DISTANCE (hero, center) ───────────────────────
    dist_str = f"{distance_km:.1f}"
    bb  = draw.textbbox((0,0), dist_str, font=f_dist)
    dw  = bb[2]-bb[0]
    dist_y = 290
    draw.text((W//2 - dw//2, dist_y), dist_str, font=f_dist, fill=WHITE,
              stroke_width=SW, stroke_fill=(0,0,0))

    # KM
    bb2 = draw.textbbox((0,0), "KM", font=f_km)
    draw.text((W//2 - (bb2[2]-bb2[0])//2, dist_y + (bb[3]-bb[1]) + 8),
              "KM", font=f_km, fill=AMBER,
              stroke_width=2, stroke_fill=(0,0,0))

    # ── ACCENT LINE ───────────────────────────────────
    line_y = 760
    lpad   = 80
    draw.rectangle([lpad, line_y, W-lpad, line_y+3], fill=AMBER)

    # ── HUMOROUS CAPTION ──────────────────────────────
    caption   = get_witty_caption(distance_km, pace_sec)
    cap_size  = 76
    cap_font  = f_caption
    while cap_size > 36:
        cb = draw.textbbox((0,0), caption, font=cap_font)
        if (cb[2]-cb[0]) <= W - 80:
            break
        cap_size -= 4
        cap_font = find_font(cap_size, bold=True)

    centered(draw, caption, line_y + 22, cap_font, AMBER, W,
             stroke_width=3, stroke_fill=(80, 40, 0))

    # ── THIN SEPARATOR ────────────────────────────────
    sep_y = line_y + cap_size + 50
    draw.rectangle([lpad, sep_y, W-lpad, sep_y+1], fill=(255,255,255,80))

    # ── STATS ROW ─────────────────────────────────────
    stats = [
        ("时  长",  fmt_duration(duration_sec)),
        ("配  速",  fmt_pace(speed_ms)),
        ("心  率",  f"{int(heart_rate)} bpm" if heart_rate else "--"),
        ("消  耗",  f"{int(calories)} 卡"    if calories   else "--"),
    ]
    stat_y = sep_y + 28
    col_w  = W // 4
    for i, (lbl, val) in enumerate(stats):
        cx = col_w * i + col_w // 2
        stat_block(draw, lbl, val, cx, stat_y, f_lbl, f_val,
                   col_clr=LGRAY, val_clr=WHITE)
        if i < 3:
            sx = col_w * (i+1)
            draw.rectangle([sx, stat_y, sx+1, stat_y+110], fill=(255,255,255,60))

    # ── BOTTOM SEPARATOR ──────────────────────────────
    bot_sep = stat_y + 140
    draw.rectangle([lpad, bot_sep, W-lpad, bot_sep+1], fill=(255,255,255,50))

    # ── HASHTAGS ──────────────────────────────────────
    tags = "#跑步  #运动打卡  #跑步打卡  #今日份运动"
    centered(draw, tags, bot_sep + 22, f_tag, MGRAY, W)

    # ── FOOTER ────────────────────────────────────────
    centered(draw, "via Strava", H - 36, f_foot, (110,110,110), W)

    base.convert('RGB').save(output_path, quality=95)
    return output_path


# ── Text caption (XHS + Twitter) ─────────────────────────────────────────────
def get_xhs_text_caption(distance_km, duration_sec, speed_ms,
                          heart_rate=None, calories=None):
    pace_sec = (1000 / speed_ms) if speed_ms else None
    witty    = get_witty_caption(distance_km, pace_sec)
    hr_str   = f"{int(heart_rate)} bpm" if heart_rate else "未记录"
    cal_str  = f"{int(calories)} 大卡"  if calories   else "未记录"
    return f"""{witty} !!

今日跑步数据 ↓
📍 距离：{distance_km:.1f} 公里
⏱️ 时长：{fmt_duration(duration_sec)}
🏃 配速：{fmt_pace(speed_ms)}
❤️ 心率：{hr_str}
🔥 消耗：{cal_str}

#跑步 #运动打卡 #跑步打卡 #健身打卡 #晨跑 #夜跑"""
