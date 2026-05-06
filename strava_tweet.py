#!/usr/bin/env python3
import os
import sys
import json
import base64
import smtplib
import requests
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from datetime import datetime

STRAVA_CLIENT_ID = os.environ['STRAVA_CLIENT_ID']
STRAVA_CLIENT_SECRET = os.environ['STRAVA_CLIENT_SECRET']
STRAVA_REFRESH_TOKEN = os.environ['STRAVA_REFRESH_TOKEN']
STRAVA_VERIFY_TOKEN = os.environ.get('STRAVA_VERIFY_TOKEN', '')
GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN', '')
if not GITHUB_TOKEN and 'GITHUB_TOKEN' in os.environ:
    GITHUB_TOKEN = os.environ['GITHUB_TOKEN']
GITHUB_REPO = os.environ.get('GITHUB_REPOSITORY', 'huyan9968/strava-tweet')

TWITTER_API_KEY             = os.environ.get('CONSUMER_KEY', '')
TWITTER_API_SECRET          = os.environ.get('CONSUMER_KEY_SECRET', '')
TWITTER_ACCESS_TOKEN        = os.environ.get('ACCESS_TOKEN', '')
TWITTER_ACCESS_TOKEN_SECRET = os.environ.get('ACCESS_TOKEN_SECRET', '')

THREADS_USER_ID      = os.environ.get('THREADS_USER_ID', '')
THREADS_ACCESS_TOKEN = os.environ.get('THREADS_ACCESS_TOKEN', '')

INSTAGRAM_USER_ID      = os.environ.get('INSTAGRAM_USER_ID', '')
INSTAGRAM_ACCESS_TOKEN = os.environ.get('INSTAGRAM_ACCESS_TOKEN', '')


def get_strava_token():
    resp = requests.post('https://www.strava.com/oauth/token', data={
        'client_id': STRAVA_CLIENT_ID,
        'client_secret': STRAVA_CLIENT_SECRET,
        'refresh_token': STRAVA_REFRESH_TOKEN,
        'grant_type': 'refresh_token'
    })
    resp.raise_for_status()
    return resp.json()['access_token']


def get_latest_run(token):
    headers = {'Authorization': f'Bearer {token}'}
    resp = requests.get(
        'https://www.strava.com/api/v3/athlete/activities',
        headers=headers,
        params={'per_page': 5}
    )
    resp.raise_for_status()
    for activity in resp.json():
        if activity['sport_type'] in ('Run', 'TrailRun', 'VirtualRun'):
            return activity
    return None


def get_activity_detail(token, activity_id):
    headers = {'Authorization': f'Bearer {token}'}
    resp = requests.get(
        f'https://www.strava.com/api/v3/activities/{activity_id}',
        headers=headers
    )
    resp.raise_for_status()
    return resp.json()


def format_pace(speed_ms):
    if not speed_ms:
        return "N/A"
    pace_seconds = 1000 / speed_ms
    minutes = int(pace_seconds // 60)
    seconds = int(pace_seconds % 60)
    return f"{minutes}'{seconds:02d}\"/公里"


def format_duration(seconds):
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    if hours > 0:
        return f"{hours}小时{minutes}分{secs:02d}秒"
    return f"{minutes}分{secs:02d}秒"


def generate_map_image(polyline_str, activity_id):
    try:
        import polyline as polyline_lib
        from staticmap import StaticMap, Line

        coordinates = polyline_lib.decode(polyline_str)
        if not coordinates:
            return None

        m = StaticMap(800, 500, url_template='https://tile.openstreetmap.org/{z}/{x}/{y}.png')
        coords_lnglat = [(lng, lat) for lat, lng in coordinates]
        m.add_line(Line(coords_lnglat, '#FF4500', 4))
        image = m.render()

        path = f"/tmp/map_{activity_id}.png"
        image.save(path)
        return path
    except Exception as e:
        print(f"地图生成失败: {e}", file=sys.stderr)
        return None


def upload_map_to_repo(image_path, activity_id):
    filename = f"maps/map_{activity_id}.png"
    with open(image_path, 'rb') as f:
        content = base64.b64encode(f.read()).decode()

    headers = {
        'Authorization': f'token {GITHUB_TOKEN}',
        'Accept': 'application/vnd.github.v3+json'
    }

    check = requests.get(
        f'https://api.github.com/repos/{GITHUB_REPO}/contents/{filename}',
        headers=headers
    )
    data = {'message': f'map: activity {activity_id}', 'content': content}
    if check.status_code == 200:
        data['sha'] = check.json()['sha']

    resp = requests.put(
        f'https://api.github.com/repos/{GITHUB_REPO}/contents/{filename}',
        headers=headers,
        json=data
    )
    if resp.status_code in (200, 201):
        owner, repo = GITHUB_REPO.split('/')
        return f"https://raw.githubusercontent.com/{owner}/{repo}/main/{filename}"
    return None


def already_tweeted(activity_id):
    activities_file = 'data/activities.json'
    if not os.path.exists(activities_file):
        return False
    with open(activities_file, 'r', encoding='utf-8') as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError:
            return False
    return any(a['id'] == activity_id and a.get('tweeted') for a in data.get('activities', []))


def mark_as_tweeted(activity_id, tweet_id):
    activities_file = 'data/activities.json'
    if not os.path.exists(activities_file):
        return
    with open(activities_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    for a in data['activities']:
        if a['id'] == activity_id:
            a['tweeted'] = True
            a['tweet_id'] = str(tweet_id)
    with open(activities_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def post_to_twitter(text, image_path=None):
    if not all([TWITTER_API_KEY, TWITTER_API_SECRET, TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_TOKEN_SECRET]):
        print("未配置 Twitter API 凭据，跳过发推。")
        return None
    try:
        import tweepy

        client = tweepy.Client(
            consumer_key=TWITTER_API_KEY,
            consumer_secret=TWITTER_API_SECRET,
            access_token=TWITTER_ACCESS_TOKEN,
            access_token_secret=TWITTER_ACCESS_TOKEN_SECRET
        )
        response = client.create_tweet(text=text)
        tweet_id = response.data['id']
        print(f"推文已发布！https://x.com/i/web/status/{tweet_id}")
        return tweet_id
    except Exception as e:
        print(f"发推失败: {e}", file=sys.stderr)
        return None


def post_to_threads(text):
    if not all([THREADS_USER_ID, THREADS_ACCESS_TOKEN]):
        print("未配置 Threads 凭据，跳过。")
        return None
    try:
        resp = requests.post(
            f'https://graph.threads.net/v1.0/{THREADS_USER_ID}/threads',
            params={'media_type': 'TEXT', 'text': text, 'access_token': THREADS_ACCESS_TOKEN}
        )
        resp.raise_for_status()
        creation_id = resp.json()['id']

        resp2 = requests.post(
            f'https://graph.threads.net/v1.0/{THREADS_USER_ID}/threads_publish',
            params={'creation_id': creation_id, 'access_token': THREADS_ACCESS_TOKEN}
        )
        resp2.raise_for_status()
        post_id = resp2.json()['id']
        print(f"Threads 发布成功！ID: {post_id}")
        return post_id
    except Exception as e:
        print(f"Threads 发布失败: {e}", file=sys.stderr)
        return None


def post_to_instagram(caption, image_url):
    if not all([INSTAGRAM_USER_ID, INSTAGRAM_ACCESS_TOKEN]):
        print("未配置 Instagram 凭据，跳过。")
        return None
    if not image_url:
        print("Instagram 需要图片，无路线地图跳过。")
        return None
    try:
        resp = requests.post(
            f'https://graph.instagram.com/v21.0/{INSTAGRAM_USER_ID}/media',
            params={'image_url': image_url, 'caption': caption, 'access_token': INSTAGRAM_ACCESS_TOKEN}
        )
        resp.raise_for_status()
        creation_id = resp.json()['id']

        resp2 = requests.post(
            f'https://graph.instagram.com/v21.0/{INSTAGRAM_USER_ID}/media_publish',
            params={'creation_id': creation_id, 'access_token': INSTAGRAM_ACCESS_TOKEN}
        )
        resp2.raise_for_status()
        post_id = resp2.json()['id']
        print(f"Instagram 发布成功！ID: {post_id}")
        return post_id
    except Exception as e:
        print(f"Instagram 发布失败: {e}", file=sys.stderr)
        return None


def send_card_email(subject, text_body, card_path, to_addr):
    gmail_user = os.environ.get('GMAIL_USER', '')
    gmail_pass = os.environ.get('GMAIL_APP_PASSWORD', '')
    if not gmail_user or not gmail_pass:
        print("未配置 GMAIL_USER / GMAIL_APP_PASSWORD，跳过邮件发送")
        return

    msg = MIMEMultipart('related')
    msg['From']    = gmail_user
    msg['To']      = to_addr
    msg['Subject'] = subject

    # 正文（inline 图片 + 文字）
    html = f"""
<html><body>
<img src="cid:xhs_card" style="max-width:540px;display:block;margin:0 auto;border-radius:16px;">
<pre style="font-family:sans-serif;margin-top:20px;color:#333;">{text_body}</pre>
</body></html>"""
    msg.attach(MIMEText(html, 'html', 'utf-8'))

    if card_path and os.path.exists(card_path):
        with open(card_path, 'rb') as f:
            img = MIMEImage(f.read(), _subtype='png')
        img.add_header('Content-ID', '<xhs_card>')
        img.add_header('Content-Disposition', 'inline', filename='xhs_card.png')
        msg.attach(img)

    try:
        with smtplib.SMTP('smtp.gmail.com', 587) as smtp:
            smtp.starttls()
            smtp.login(gmail_user, gmail_pass)
            smtp.send_message(msg)
        print(f"邮件已发送至 {to_addr}")
    except Exception as e:
        print(f"邮件发送失败: {e}", file=sys.stderr)


def create_github_issue(title, body):
    headers = {
        'Authorization': f'token {GITHUB_TOKEN}',
        'Accept': 'application/vnd.github.v3+json'
    }
    requests.post(
        f'https://api.github.com/repos/{GITHUB_REPO}/labels',
        headers=headers,
        json={'name': '跑步记录', 'color': 'FF4500'}
    )
    resp = requests.post(
        f'https://api.github.com/repos/{GITHUB_REPO}/issues',
        headers=headers,
        json={'title': title, 'body': body, 'labels': ['跑步记录']}
    )
    resp.raise_for_status()
    return resp.json()['html_url']


def write_run_markdown(detail, activity_id, date_str, tweet):
    """写入单个跑步记录的Markdown文件"""
    os.makedirs('runs', exist_ok=True)

    distance    = detail['distance'] / 1000
    duration    = detail['moving_time']
    speed_ms    = detail.get('average_speed', 0)
    heart_rate  = detail.get('average_heartrate')
    calories    = detail.get('calories')
    elevation   = detail.get('total_elevation_gain', 0)
    max_speed   = detail.get('max_speed', 0)
    pace    = format_pace(speed_ms)
    hr_str  = f"{int(heart_rate)} bpm" if heart_rate else "未记录"
    cal_str = f"{int(calories)} 大卡" if calories else "未记录"

    start_latlng = detail.get('start_latlng', [0, 0])
    end_latlng   = detail.get('end_latlng', [0, 0])
    polyline_data = detail.get('map', {}).get('polyline') or detail.get('map', {}).get('summary_polyline') or ''

    # 获取温度（如果有的话）
    temp = detail.get('average_temp', '')

    # 获取天气描述
    weather_desc = ''
    if 'weather' in detail:
        weather_desc = detail['weather'].get('summary', '')

    # 构建frontmatter
    frontmatter = f"""---
id: {activity_id}
date: {(detail.get('start_date_local') or detail['start_date'])[:10]}
title: {detail.get('name', '跑步记录')}
sport_type: {detail.get('sport_type', 'Run')}
distance: {distance:.1f}
duration: {duration}
moving_time: {detail.get('moving_time', duration)}
average_speed: {speed_ms}
average_heartrate: {heart_rate if heart_rate else ''}
calories: {calories if calories else ''}
max_speed: {max_speed}
elevation_gain: {elevation}
start_latlng: [{start_latlng[0]}, {start_latlng[1]}]
end_latlng: [{end_latlng[0]}, {end_latlng[1]}]
polyline: "{polyline_data}"
"""
    if temp:
        frontmatter += f"temperature: {temp}\n"
    if weather_desc:
        frontmatter += f'weather: "{weather_desc}"\n'
    frontmatter += """---

## 今日跑步数据

"""

    # 统计数据表格
    frontmatter += f"""| 项目 | 数据 |
|------|------|
| **距离** | {distance:.1f} 公里 |
| **时长** | {format_duration(duration)} |
| **配速** | {pace} |
| **平均心率** | {hr_str} |
| **最大速度** | {max_speed:.2f} m/s |
| **爬升** | {elevation} 米 |
| **消耗** | {cal_str} |
"""

    if temp:
        frontmatter += f"| **温度** | {temp}°C |\n"
    if weather_desc:
        frontmatter += f"| **天气** | {weather_desc} |\n"

    frontmatter += """\n## 路线地图

"""

    if detail.get('map', {}).get('polyline') or detail.get('map', {}).get('summary_polyline'):
        frontmatter += f"![路线地图](maps/map_{activity_id}.png)\n\n"

    frontmatter += """---
*由 GitHub Actions 自动生成*
"""

    md_filename = f"runs/{(detail.get('start_date_local') or detail['start_date'])[:10]}-run-{activity_id}.md"
    with open(md_filename, 'w', encoding='utf-8') as f:
        f.write(frontmatter)

    print(f"Markdown文件已写入: {md_filename}")
    return md_filename


def update_activities_json(detail, activity_id, md_filename, map_url):
    """更新聚合的JSON数据文件"""
    os.makedirs('data', exist_ok=True)

    distance    = detail['distance'] / 1000
    duration    = detail['moving_time']
    speed_ms    = detail.get('average_speed', 0)
    polyline_data = detail.get('map', {}).get('polyline') or detail.get('map', {}).get('summary_polyline') or ''

    # 读取现有数据
    activities_file = 'data/activities.json'
    if os.path.exists(activities_file):
        with open(activities_file, 'r', encoding='utf-8') as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                data = {"total_activities": 0, "total_distance": 0, "total_duration": 0, "activities": []}
    else:
        data = {"total_activities": 0, "total_distance": 0, "total_duration": 0, "activities": []}

    # 检查是否已存在该活动
    existing = any(a['id'] == activity_id for a in data['activities'])

    if not existing:
        latlng = detail.get('start_latlng') or []
        activity_data = {
            "id": activity_id,
            "date": (detail.get('start_date_local') or detail['start_date'])[:10],
            "title": detail.get('name', '跑步记录'),
            "distance": round(distance, 1),
            "duration": duration,
            "moving_time": detail.get('moving_time', duration),
            "pace": int(1000 / speed_ms) if speed_ms > 0 else 0,
            "speed_ms": round(speed_ms, 3),
            "average_heartrate": detail.get('average_heartrate'),
            "max_heartrate": detail.get('max_heartrate'),
            "calories": detail.get('calories'),
            "elevation_gain": detail.get('total_elevation_gain', 0),
            "start_latlng": latlng if len(latlng) == 2 else None,
            "polyline": polyline_data,
            "type": detail.get('sport_type', 'Run'),
            "map_url": map_url or '',
            "md_file": md_filename,
            "strava_url": f"https://www.strava.com/activities/{activity_id}"
        }
        data['activities'].append(activity_data)
        data['total_activities'] = len(data['activities'])
        data['total_distance'] = round(sum(a['distance'] for a in data['activities']), 1)
        data['total_duration'] = sum(a['duration'] for a in data['activities'])
        # 按日期排序（最新的在前）
        data['activities'].sort(key=lambda x: x['date'], reverse=True)

        with open(activities_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        print(f"JSON数据已更新: {activities_file}")
    else:
        print(f"活动已存在，跳过重复写入: {activity_id}")

    return data


def main():
    print("获取 Strava 令牌...")
    token = get_strava_token()

    print("获取最近跑步记录...")
    activity = get_latest_run(token)
    if not activity:
        print("最近没有跑步记录，退出。")
        return

    activity_id = activity['id']
    print(f"找到活动：{activity['name']} (ID: {activity_id})")

    if already_tweeted(activity_id):
        print(f"活动 {activity_id} 已发布过推文，退出。")
        return

    detail = get_activity_detail(token, activity_id)

    distance    = detail['distance'] / 1000
    duration    = detail['moving_time']
    speed_ms    = detail.get('average_speed', 0)
    heart_rate  = detail.get('average_heartrate')
    calories    = detail.get('calories')
    start_local = detail.get('start_date_local') or detail['start_date']
    date_str    = start_local[:10]
    start_hour  = int(start_local[11:13])

    hr_str  = f"{int(heart_rate)} bpm" if heart_rate else "未记录"
    cal_str = f"{int(calories)} 大卡" if calories else "未记录"
    pace    = format_pace(speed_ms)

    tweet = f"""今日跑步 🏃

📍 距离：{distance:.1f} 公里
⏱️ 时长：{format_duration(duration)}
🏃 配速：{pace}
❤️ 平均心率：{hr_str}
🔥 消耗：{cal_str}

#跑步 #Running #Strava"""

    print(f"\n推文内容：\n{tweet}\n")

    # ── 生成路线地图 ──────────────────────────────────
    map_url = None
    map_file = None
    polyline_str = (detail.get('map') or {}).get('polyline') or (detail.get('map') or {}).get('summary_polyline')
    if polyline_str:
        print("生成路线地图...")
        map_file = generate_map_image(polyline_str, activity_id)
        if map_file:
            print("上传地图...")
            map_url = upload_map_to_repo(map_file, activity_id)

    # ── 生成小红书卡片 ────────────────────────────────
    xhs_card_url = None
    xhs_caption  = None
    try:
        from generate_xhs_card import create_xhs_card, get_xhs_text_caption
        print("生成小红书卡片...")
        card_path = create_xhs_card(
            distance_km  = distance,
            duration_sec = duration,
            speed_ms     = speed_ms,
            heart_rate   = heart_rate,
            calories     = calories,
            date_str     = date_str,
            start_hour   = start_hour,
            output_path  = f'/tmp/xhs_{activity_id}.png',
        )
        xhs_caption = get_xhs_text_caption(distance, duration, speed_ms, heart_rate, calories)
        print("上传小红书卡片...")
        xhs_card_url = upload_map_to_repo(card_path, f'xhs_{activity_id}')
    except Exception as e:
        print(f"小红书卡片生成失败: {e}", file=sys.stderr)

    # ── 写入跑步日记数据 (Markdown + JSON) ─────────────────────────────
    md_filename = write_run_markdown(detail, activity_id, date_str, tweet)
    activities_data = update_activities_json(detail, activity_id, md_filename, map_url)

    # ── 创建 GitHub Issue ─────────────────────────────
    title = f"🏃 跑步记录 {date_str}"

    body  = f"## Twitter 推文草稿\n\n```\n{tweet}\n```\n\n"
    body += f"**Strava 链接**：https://www.strava.com/activities/{activity_id}\n\n"
    if map_url:
        body += f"**路线地图**：\n\n![路线地图]({map_url})\n\n"

    body += "---\n\n## 小红书草稿\n\n"
    if xhs_caption:
        body += f"**文案**（复制粘贴）：\n\n```\n{xhs_caption}\n```\n\n"
    if xhs_card_url:
        body += f"**图片卡片**（长按保存）：\n\n![小红书卡片]({xhs_card_url})\n\n"

    body += "---\n*由 GitHub Actions 自动生成*"

    issue_url = create_github_issue(title, body)
    print(f"Issue 已创建：{issue_url}")

    # ── 发送邮件（卡片图 + 文案） ────────────────────
    card_path_local = f'/tmp/xhs_{activity_id}.png'
    email_subject   = f"🏃 跑步打卡 {date_str} · {distance:.1f}km"
    email_body      = xhs_caption or tweet
    send_card_email(email_subject, email_body, card_path_local,
                    to_addr='canghai8005@gmail.com')

    # ── 发布到各平台 ─────────────────────────────────
    print("发布推文...")
    tweet_id = post_to_twitter(tweet)

    print("发布到 Threads...")
    post_to_threads(tweet)

    print("发布到 Instagram...")
    post_to_instagram(tweet, map_url)

    mark_as_tweeted(activity_id, tweet_id or 'unknown')
    print("所有平台发布完成，已记录。")


if __name__ == '__main__':
    main()
