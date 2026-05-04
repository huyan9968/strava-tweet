#!/usr/bin/env python3
"""
全量同步 Strava 历史跑步数据到 data/activities.json
使用列表接口分页拉取，无需对每条记录单独调用详情接口
"""
import os
import sys
import json
import requests
from datetime import datetime

STRAVA_CLIENT_ID     = os.environ['STRAVA_CLIENT_ID']
STRAVA_CLIENT_SECRET = os.environ['STRAVA_CLIENT_SECRET']
STRAVA_REFRESH_TOKEN = os.environ['STRAVA_REFRESH_TOKEN']

SPORT_TYPES = {'Run', 'TrailRun', 'VirtualRun'}


def get_token():
    r = requests.post('https://www.strava.com/oauth/token', data={
        'client_id':     STRAVA_CLIENT_ID,
        'client_secret': STRAVA_CLIENT_SECRET,
        'refresh_token': STRAVA_REFRESH_TOKEN,
        'grant_type':    'refresh_token',
    })
    r.raise_for_status()
    return r.json()['access_token']


def fetch_all_activities(token):
    headers = {'Authorization': f'Bearer {token}'}
    all_acts = []
    page = 1
    while True:
        r = requests.get(
            'https://www.strava.com/api/v3/athlete/activities',
            headers=headers,
            params={'per_page': 200, 'page': page},
        )
        r.raise_for_status()
        batch = r.json()
        if not batch:
            break
        all_acts.extend(batch)
        print(f"  第 {page} 页，{len(batch)} 条，累计 {len(all_acts)} 条")
        if len(batch) < 200:
            break
        page += 1
    return all_acts


def to_record(a, existing=None):
    start   = a.get('start_date_local') or a.get('start_date', '')
    latlng  = a.get('start_latlng') or []
    speed   = a.get('average_speed') or 0
    polyline = (a.get('map') or {}).get('summary_polyline') or ''

    rec = {
        'id':               a['id'],
        'date':             start[:10],
        'title':            a.get('name', '跑步记录'),
        'distance':         round((a.get('distance') or 0) / 1000, 2),
        'duration':         a.get('moving_time') or 0,
        'moving_time':      a.get('moving_time') or 0,
        'pace':             int(1000 / speed) if speed > 0 else 0,
        'speed_ms':         round(speed, 3),
        'average_heartrate': a.get('average_heartrate'),
        'max_heartrate':    a.get('max_heartrate'),
        'calories':         a.get('calories'),
        'elevation_gain':   a.get('total_elevation_gain') or 0,
        'start_latlng':     latlng if len(latlng) == 2 else None,
        'polyline':         polyline,
        'type':             a.get('sport_type', 'Run'),
        'strava_url':       f"https://www.strava.com/activities/{a['id']}",
        'map_url':          '',
        'md_file':          '',
    }
    # 保留历史生成的 map_url / md_file
    if existing:
        rec['map_url'] = existing.get('map_url') or ''
        rec['md_file'] = existing.get('md_file') or ''
    return rec


def main():
    print("获取 Strava 访问令牌...")
    token = get_token()

    print("拉取所有活动（分页）...")
    all_acts = fetch_all_activities(token)
    runs = [a for a in all_acts if a.get('sport_type') in SPORT_TYPES]
    print(f"共 {len(all_acts)} 条活动，跑步 {len(runs)} 条")

    # 读取现有 JSON 以保留 map_url / md_file
    os.makedirs('data', exist_ok=True)
    data_file = 'data/activities.json'
    existing_map = {}
    if os.path.exists(data_file):
        with open(data_file) as f:
            old = json.load(f)
        for a in old.get('activities', []):
            existing_map[a['id']] = a

    records = [to_record(a, existing_map.get(a['id'])) for a in runs]
    records.sort(key=lambda x: x['date'], reverse=True)

    out = {
        'total_activities': len(records),
        'total_distance':   round(sum(r['distance'] for r in records), 1),
        'total_duration':   sum(r['duration'] for r in records),
        'total_calories':   sum((r.get('calories') or 0) for r in records),
        'activities':       records,
    }
    with open(data_file, 'w', encoding='utf-8') as f:
        json.dump(out, f, indent=2, ensure_ascii=False)

    with_latlng  = sum(1 for r in records if r.get('start_latlng'))
    with_polyline = sum(1 for r in records if r.get('polyline'))
    print(f"写入完成：{len(records)} 条，有坐标 {with_latlng} 条，有路线 {with_polyline} 条")


if __name__ == '__main__':
    main()
