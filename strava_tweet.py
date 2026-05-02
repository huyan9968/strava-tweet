#!/usr/bin/env python3
import os
import sys
import base64
import requests
from datetime import datetime

STRAVA_CLIENT_ID = os.environ['STRAVA_CLIENT_ID']
STRAVA_CLIENT_SECRET = os.environ['STRAVA_CLIENT_SECRET']
STRAVA_REFRESH_TOKEN = os.environ['STRAVA_REFRESH_TOKEN']
GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN', '')
GITHUB_REPO = os.environ.get('GITHUB_REPOSITORY', '')


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

    detail = get_activity_detail(token, activity_id)

    distance = detail['distance'] / 1000
    duration = detail['moving_time']
    pace = format_pace(detail['average_speed'])
    heart_rate = detail.get('average_heartrate')
    calories = detail.get('calories')

    hr_str = f"{int(heart_rate)} bpm" if heart_rate else "未记录"
    cal_str = f"{int(calories)} 大卡" if calories else "未记录"

    tweet = f"""今日跑步 🏃

📍 距离：{distance:.1f} 公里
⏱️ 时长：{format_duration(duration)}
🏃 配速：{pace}
❤️ 平均心率：{hr_str}
🔥 消耗：{cal_str}

#跑步 #Running #Strava"""

    print(f"\n推文内容：\n{tweet}\n")

    # 生成路线地图
    map_url = None
    polyline_str = (detail.get('map') or {}).get('polyline') or (detail.get('map') or {}).get('summary_polyline')
    if polyline_str:
        print("生成路线地图...")
        map_file = generate_map_image(polyline_str, activity_id)
        if map_file:
            print("上传地图...")
            map_url = upload_map_to_repo(map_file, activity_id)

    # 创建 GitHub Issue
    date_str = datetime.now().strftime('%Y-%m-%d')
    title = f"🏃 跑步记录 {date_str}"

    body = f"## 推文草稿\n\n```\n{tweet}\n```\n\n"
    body += f"**Strava 链接**：https://www.strava.com/activities/{activity_id}\n\n"
    if map_url:
        body += f"**路线地图**：\n\n![路线地图]({map_url})\n\n"
    body += "---\n*由 GitHub Actions 自动生成*"

    issue_url = create_github_issue(title, body)
    print(f"Issue 已创建：{issue_url}")


if __name__ == '__main__':
    main()
