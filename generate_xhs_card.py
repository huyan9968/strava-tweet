#!/usr/bin/env python3
import os
import random
from datetime import datetime

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
    if pace_sec and pace_sec < 270:
        return random.choice(FAST_CAPTIONS)
    if pace_sec and pace_sec > 420:
        return random.choice(SLOW_CAPTIONS)
    if distance_km < 3:    pool = CAPTIONS['tiny']
    elif distance_km < 5:  pool = CAPTIONS['short']
    elif distance_km < 10: pool = CAPTIONS['medium']
    elif distance_km < 15: pool = CAPTIONS['long']
    else:                   pool = CAPTIONS['insane']
    return random.choice(pool)


def _fmt_duration(sec):
    h = sec // 3600
    m = (sec % 3600) // 60
    s = sec % 60
    if h:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m}'{s:02d}\""


def _fmt_pace(speed_ms):
    if not speed_ms:
        return "--"
    total = int(1000 / speed_ms)
    return f"{total // 60}'{total % 60:02d}\""


def create_xhs_card(distance_km, duration_sec, speed_ms,
                    heart_rate=None, calories=None, date_str=None,
                    start_hour=None, output_path='/tmp/xhs_card.png'):
    from playwright.sync_api import sync_playwright

    pace_sec = (1000 / speed_ms) if speed_ms else None
    caption = get_witty_caption(distance_km, pace_sec)

    # Morning = before noon, Night = evening/night (default)
    is_morning = (start_hour is not None) and (start_hour < 12)
    run_emoji = "☀" if is_morning else "🌙"
    run_label = "晨跑打卡" if is_morning else "夜跑打卡"
    hashtag_type = "晨跑" if is_morning else "夜跑"

    hr_str  = str(int(heart_rate)) if heart_rate else "--"
    cal_str = str(int(calories))   if calories   else "--"

    # Convert "2026-05-03" → "2026年5月3日"
    if date_str and len(date_str) >= 10:
        y, mo, d = date_str[:10].split('-')
        date_cn = f"{y}年{int(mo)}月{int(d)}日"
    else:
        now = datetime.now()
        date_cn = f"{now.year}年{now.month}月{now.day}日"

    hashtags = f"#跑步 #运动打卡 #{hashtag_type} #跑步打卡"

    template_name = 'xhs_card_morning.html' if is_morning else 'xhs_card.html'
    template_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                 'templates', template_name)
    with open(template_path, 'r', encoding='utf-8') as f:
        html = f.read()

    for placeholder, value in [
        ('{{DATE}}',      date_cn),
        ('{{DISTANCE}}',  f"{distance_km:.1f}"),
        ('{{DURATION}}',  _fmt_duration(duration_sec)),
        ('{{PACE}}',      _fmt_pace(speed_ms)),
        ('{{HEARTRATE}}', hr_str),
        ('{{CALORIES}}',  cal_str),
        ('{{CAPTION}}',   caption),
        ('{{RUN_EMOJI}}', run_emoji),
        ('{{RUN_LABEL}}', run_label),
        ('{{HASHTAGS}}',  hashtags),
    ]:
        html = html.replace(placeholder, value)

    tmp_html = f'/tmp/xhs_card_{os.getpid()}.html'
    with open(tmp_html, 'w', encoding='utf-8') as f:
        f.write(html)

    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = browser.new_page(viewport={'width': 1080, 'height': 1350})
            page.goto(f'file://{tmp_html}')
            page.wait_for_timeout(2500)  # wait for Google Fonts
            page.screenshot(path=output_path, full_page=False)
            browser.close()
    finally:
        if os.path.exists(tmp_html):
            os.unlink(tmp_html)

    return output_path


def get_xhs_text_caption(distance_km, duration_sec, speed_ms,
                          heart_rate=None, calories=None):
    pace_sec = (1000 / speed_ms) if speed_ms else None
    witty    = get_witty_caption(distance_km, pace_sec)
    hr_str   = f"{int(heart_rate)} bpm" if heart_rate else "未记录"
    cal_str  = f"{int(calories)} 大卡"  if calories   else "未记录"
    return f"""{witty} !!

今日跑步数据 ↓
📍 距离：{distance_km:.1f} 公里
⏱️ 时长：{_fmt_duration(duration_sec)}
🏃 配速：{_fmt_pace(speed_ms)}
❤️ 心率：{hr_str}
🔥 消耗：{cal_str}

#跑步 #运动打卡 #跑步打卡 #健身打卡 #晨跑 #夜跑"""
