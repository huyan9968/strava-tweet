from PIL import Image, ImageDraw, ImageFont
import os
import random


WITTY_CAPTIONS = {
    'short': [   # < 3km
        "今天出门了，就是赢家",
        "小跑一下，聊胜于无",
        "三公里以内，跑了个寂寞",
    ],
    'medium': [  # 3-5km
        "跑完了，今晚的奶茶挣到了",
        "稳稳当当，佛系选手在此",
        "四公里俱乐部，打卡成功",
    ],
    'long': [    # 5-10km
        "腿有点酸，心很满足",
        "跑完才能安心摸鱼",
        "五公里以上，今晚必须加鸡腿",
    ],
    'very_long': [  # 10km+
        "今天这条腿不是我的了",
        "十公里选手，让路让路",
        "跑了这么远，人是不是傻了",
    ],
    'insane': [  # 15km+
        "这人有病，半马都敢跑",
        "腿腿：我们要分手了",
        "医生说不能跑这么远，我当没听见",
    ],
}

PACE_COMMENTS = {
    'fast': "今天在飞，这不是跑步这是逃命",   # < 4:30/km
    'good': "配速稳得一批，选手风范",         # 4:30-5:30
    'easy': "慢跑派，享受生活慢慢来",         # 5:30-6:30
    'slow': "散步plus，别拆穿我",             # > 6:30
}


def get_witty_caption(distance_km, pace_sec_per_km=None):
    if distance_km < 3:
        base = random.choice(WITTY_CAPTIONS['short'])
    elif distance_km < 5:
        base = random.choice(WITTY_CAPTIONS['medium'])
    elif distance_km < 10:
        base = random.choice(WITTY_CAPTIONS['long'])
    elif distance_km < 15:
        base = random.choice(WITTY_CAPTIONS['very_long'])
    else:
        base = random.choice(WITTY_CAPTIONS['insane'])

    if pace_sec_per_km:
        if pace_sec_per_km < 270:
            base = PACE_COMMENTS['fast']
        elif pace_sec_per_km > 390:
            base = PACE_COMMENTS['slow']

    return base


def find_font(size, bold=False):
    candidates = [
        '/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc' if bold else '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',
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
    m = int(sec // 60)
    s = int(sec % 60)
    return f"{m}'{s:02d}\"/km"


def create_xhs_card(distance_km, duration_sec, speed_ms,
                    heart_rate=None, calories=None, date_str=None,
                    output_path='/tmp/xhs_card.png'):

    W, H = 1080, 1350

    # Color palette
    BG          = (13,  17,  23)
    CARD        = (22,  27,  34)
    ACCENT      = (255, 88,  50)   # orange-red
    ACCENT2     = (255, 175, 50)   # amber
    WHITE       = (255, 255, 255)
    LIGHT       = (190, 190, 190)
    MUTED       = (90,  90,  90)

    img  = Image.new('RGB', (W, H), BG)
    draw = ImageDraw.Draw(img)

    # Subtle glow in top-right corner
    for r in range(250, 0, -5):
        alpha = int(18 * (r / 250))
        draw.ellipse([W - r - 50, -r // 2, W + r // 2, r], fill=None)

    # ── Fonts ──────────────────────────────────────────
    f_title    = find_font(54, bold=True)
    f_huge     = find_font(200, bold=True)
    f_unit     = find_font(52)
    f_stat_val = find_font(58, bold=True)
    f_stat_lbl = find_font(34)
    f_caption  = find_font(46, bold=True)
    f_tag      = find_font(32)
    f_foot     = find_font(28)
    f_date     = find_font(30)

    # ── Header ─────────────────────────────────────────
    draw.text((80, 72), "今日跑步打卡", font=f_title, fill=WHITE)
    # orange underline
    draw.rectangle([80, 138, 80 + 7 * 54, 143], fill=ACCENT)

    if date_str:
        draw.text((W - 80, 88), date_str, font=f_date, fill=LIGHT, anchor='ra')

    draw.rectangle([80, 178, W - 80, 181], fill=MUTED)

    # ── Big Distance ───────────────────────────────────
    dist_str = f"{distance_km:.1f}"
    bbox = draw.textbbox((0, 0), dist_str, font=f_huge)
    dw = bbox[2] - bbox[0]
    cx = W // 2
    draw.text((cx - dw // 2, 205), dist_str, font=f_huge, fill=WHITE)

    unit_x = cx + dw // 2 + 10
    draw.text((unit_x, 345), "公里", font=f_unit, fill=LIGHT)

    # ── Three Stat Boxes ──────────────────────────────
    stats = [
        (fmt_duration(duration_sec), "时  长"),
        (fmt_pace(speed_ms),         "配速/km"),
        (f"{int(heart_rate)} bpm" if heart_rate else "--", "心  率"),
    ]

    pad   = 20
    bw    = (W - 160 - pad * 2) // 3
    bh    = 190
    by    = 620

    for i, (val, lbl) in enumerate(stats):
        x = 80 + i * (bw + pad)
        draw.rounded_rectangle([x, by, x + bw, by + bh], radius=18, fill=CARD)

        # color dot top-left
        dot_color = [ACCENT, ACCENT2, (120, 200, 140)][i]
        draw.ellipse([x + 18, by + 18, x + 36, by + 36], fill=dot_color)

        # value
        vbb = draw.textbbox((0, 0), val, font=f_stat_val)
        vw  = vbb[2] - vbb[0]
        draw.text((x + bw // 2 - vw // 2, by + 55), val, font=f_stat_val, fill=WHITE)

        # label
        lbb = draw.textbbox((0, 0), lbl, font=f_stat_lbl)
        lw  = lbb[2] - lbb[0]
        draw.text((x + bw // 2 - lw // 2, by + 138), lbl, font=f_stat_lbl, fill=LIGHT)

    # ── Calories ──────────────────────────────────────
    cal_y = 840
    if calories:
        draw.rounded_rectangle([80, cal_y, W - 80, cal_y + 85], radius=18, fill=CARD)
        cal_text = f"消耗  {int(calories)}  大卡"
        cbb = draw.textbbox((0, 0), cal_text, font=f_stat_val)
        cw  = cbb[2] - cbb[0]
        draw.text((W // 2 - cw // 2, cal_y + 18), cal_text, font=f_stat_val, fill=ACCENT2)
        # flame decoration
        draw.text((80 + 20, cal_y + 20), ">>", font=f_stat_lbl, fill=ACCENT)

    # ── Witty Caption ─────────────────────────────────
    pace_sec = (1000 / speed_ms) if speed_ms else None
    caption  = get_witty_caption(distance_km, pace_sec)

    cap_y = 980
    draw.rounded_rectangle([80, cap_y, W - 80, cap_y + 95], radius=30, fill=ACCENT)
    cbb = draw.textbbox((0, 0), caption, font=f_caption)
    cw  = cbb[2] - cbb[0]
    draw.text((W // 2 - cw // 2, cap_y + 24), caption, font=f_caption, fill=WHITE)

    # Speech bubble tail
    draw.polygon([(180, cap_y + 95), (220, cap_y + 95), (190, cap_y + 125)], fill=ACCENT)

    # ── Hashtags ──────────────────────────────────────
    tag_y = 1130
    tags  = "#跑步   #运动打卡   #跑步打卡   #健身打卡"
    draw.text((80, tag_y), tags, font=f_tag, fill=ACCENT)

    # ── Divider ───────────────────────────────────────
    draw.rectangle([80, 1210, W - 80, 1212], fill=MUTED)

    # ── Footer ────────────────────────────────────────
    draw.text((80, 1230), "Powered by Strava", font=f_foot, fill=MUTED)
    draw.text((W - 80, 1230), "Keep Running :)", font=f_foot, fill=MUTED, anchor='ra')

    img.save(output_path, quality=95)
    return output_path


def get_xhs_text_caption(distance_km, duration_sec, speed_ms,
                          heart_rate=None, calories=None):
    pace_sec = (1000 / speed_ms) if speed_ms else None
    pace_str = fmt_pace(speed_ms)
    hr_str   = f"{int(heart_rate)} bpm" if heart_rate else "未记录"
    cal_str  = f"{int(calories)} 大卡" if calories else "未记录"
    witty    = get_witty_caption(distance_km, pace_sec)

    return f"""{witty} !!

今日跑步数据 ↓
📍 距离：{distance_km:.1f} 公里
⏱️ 时长：{fmt_duration(duration_sec)}
🏃 配速：{pace_str}
❤️ 心率：{hr_str}
🔥 消耗：{cal_str}

#跑步 #运动打卡 #跑步打卡 #健身打卡 #晨跑 #夜跑"""
