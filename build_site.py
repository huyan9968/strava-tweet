
#!/usr/bin/env python3
"""
静态网站生成器
读取 data/activities.json 和 runs/ 目录，生成 index.html 页面
"""

import os
import json
import base64
from datetime import datetime

# ─── 配置 ─────────────────────────────────────────
DATA_FILE = 'data/activities.json'
OUTPUT_FILE = 'docs/index.html'
RUNS_DIR = 'runs'

# ─── 颜色主题 ─────────────────────────────────────
COLORS = {
    'primary':   '#1e40af',   # indigo-800
    'secondary': '#3b82f6',   # blue-500
    'accent':    '#10b981',   # emerald-500
    'card_bg':   '#f8fafc',   # slate-50
    'text':      '#1e293b',   # slate-800
    'text_light':'#64748b',   # slate-500
    'border':    '#e2e8f0',   # slate-200
}

def format_pace(speed_ms):
    """速度(m/s) → 配速(分秒/公里)"""
    if not speed_ms or speed_ms <= 0:
        return "--"
    pace_sec = 1000 / speed_ms
    m = int(pace_sec // 60)
    s = int(pace_sec % 60)
    return f"{m}'{s:02d}\"/km"

def format_duration(seconds):
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    if h > 0:
        return f"{h}h {m}m {s}s"
    return f"{m}m {s}s"

def load_data():
    """加载聚合数据"""
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"total_activities": 0, "total_distance": 0, "total_duration": 0, "activities": []}

def compute_stats(activities):
    """计算统计指标"""
    if not activities:
        return {}

    total_dist = sum(a.get('distance', 0) for a in activities)
    total_dur  = sum(a.get('duration', 0) for a in activities)
    total_cal  = sum(a.get('calories') or 0 for a in activities)
    total_ele  = sum(a.get('elevation_gain', 0) for a in activities)

    # 最佳配速
    best_pace = min(
        (a for a in activities if a.get('speed_ms', 0) > 0),
        key=lambda x: x['speed_ms'],
        default=None
    )

    # 最近一年/月的统计
    now = datetime.now()
    year_ago = now.year
    month_ago = now.month

    yearly = [a for a in activities if a.get('date', '').startswith(str(year_ago))]
    monthly = [a for a in activities if a.get('date', '').startswith(f"{year_ago}-{month_ago:02d}")]

    return {
        'total_distance': round(total_dist, 1),
        'total_duration': total_dur,
        'total_calories': total_cal,
        'total_elevation': total_ele,
        'best_pace': best_pace,
        'yearly_count': len(yearly),
        'yearly_dist': round(sum(a.get('distance', 0) for a in yearly), 1),
        'monthly_count': len(monthly),
        'monthly_dist': round(sum(a.get('distance', 0) for a in monthly), 1),
        'longest_run': max(activities, key=lambda a: a.get('distance', 0)),
        'total_activities': len(activities),
    }

def build_monthly_chart(activities):
    """构建月度统计的JS数组"""
    if not activities:
        return "[]"

    # 按年月分组
    monthly = {}
    for a in activities:
        ym = a.get('date', '')[:7]  # "2024-01"
        if ym not in monthly:
            monthly[ym] = {'count': 0, 'distance': 0, 'duration': 0}
        monthly[ym]['count'] += 1
        monthly[ym]['distance'] += a.get('distance', 0)
        monthly[ym]['duration'] += a.get('duration', 0)

    # 排序
    items = sorted(monthly.items())
    labels = [f"'{ym}'" for ym, _ in items]
    counts = [d['count'] for _, d in items]
    dists = [round(d['distance'], 1) for _, d in items]

    return f"""
    labels: [{', '.join(labels)}],
    datasets: [{{
        label: '跑步次数',
        data: {counts},
        borderColor: '#10b981',
        backgroundColor: 'rgba(16, 185, 129, 0.1)',
        tension: 0.4
    }}, {{
        label: '距离(km)',
        data: {dists},
        borderColor: '#3b82f6',
        backgroundColor: 'rgba(59, 130, 246, 0.1)',
        tension: 0.4,
        yAxisID: 'y1'
    }}]"""

def build_pace_distribution(activities):
    """配速分布 (用于热力图)"""
    lines = []
    for a in activities:
        polyline = a.get('polyline', '')
        avg_pace = a.get('pace', 0)
        if polyline and avg_pace:
            # 将配速映射到颜色 (300-420s → 蓝绿红)
            intensity = min(1, max(0, (avg_pace - 300) / 120))
            r = int(30 + intensity * 150)
            g = int(150 - intensity * 100)
            b = int(200 - intensity * 100)
            color = f"rgb({r},{g},{b})"
            lines.append(f"{{coords: polyline.decode('{polyline}'), color: '{color}', weight: 5}}")

    return ',\n              '.join(lines)

def generate_html(data):
    """生成完整HTML"""
    activities = data.get('activities', [])
    stats = compute_stats(activities)

    # 计算地图中心（用实际活动坐标均值，不再硬编码北京）
    latlngs = [a['start_latlng'] for a in activities
               if a.get('start_latlng') and len(a['start_latlng']) == 2
               and a['start_latlng'][0] != 0]
    if latlngs:
        map_center_lat = sum(l[0] for l in latlngs) / len(latlngs)
        map_center_lng = sum(l[1] for l in latlngs) / len(latlngs)
    else:
        map_center_lat, map_center_lng = 39.9042, 116.4074

    # 所有有路线数据的活动（供地图批量绘制）
    route_data = []
    for a in activities:
        pl = a.get('polyline', '')
        if pl:
            pace = a.get('pace', 0)
            if pace and pace > 0:
                intensity = min(1, max(0, (pace - 300) / 120))
                r = int(30 + intensity * 150)
                g = int(150 - intensity * 100)
                b = int(200 - intensity * 100)
                color = f"rgb({r},{g},{b})"
            else:
                color = "#3b82f6"
            route_data.append({"polyline": pl, "color": color})

    # 最近的跑步记录（显示全部）
    recent = activities  # 显示所有记录

    # Chart.js 月度数据
    monthly_chart = build_monthly_chart(activities)
    route_data_json = json.dumps(route_data, ensure_ascii=False)


    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>跑步日记 - 我的跑步记录</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/luxon@3.0.4/build/global/luxon.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/chartjs-adapter-luxon@1.0.0"></script>
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; color: {COLORS['text']}; background: #f1f5f9; line-height: 1.6; }}
        .header {{ background: linear-gradient(135deg, {COLORS['primary']} 0%, {COLORS['secondary']} 100%); color: white; padding: 2rem 1rem; text-align: center; }}
        .header h1 {{ font-size: 2rem; margin-bottom: 0.5rem; }}
        .header p {{ opacity: 0.9; }}
        .container {{ max-width: 1200px; margin: 0 auto; padding: 2rem 1rem; }}
        .stats-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; margin-bottom: 2rem; }}
        .stat-card {{ background: white; padding: 1.5rem; border-radius: 12px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); text-align: center; transition: transform 0.2s; }}
        .stat-card:hover {{ transform: translateY(-2px); box-shadow: 0 4px 12px rgba(0,0,0,0.15); }}
        .stat-card .value {{ font-size: 2rem; font-weight: bold; color: {COLORS['primary']}; }}
        .stat-card .label {{ color: {COLORS['text_light']}; margin-top: 0.5rem; font-size: 0.9rem; }}
        .chart-section {{ background: white; padding: 1.5rem; border-radius: 12px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); margin-bottom: 2rem; }}
        .chart-section h2 {{ font-size: 1.3rem; margin-bottom: 1rem; color: {COLORS['primary']}; }}
        .runs-list {{ display: flex; flex-direction: column; gap: 1rem; }}
        .run-item {{ background: white; padding: 1.5rem; border-radius: 12px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); display: flex; flex-wrap: wrap; gap: 1rem; align-items: center; transition: transform 0.2s; }}
        .run-item:hover {{ transform: translateX(4px); box-shadow: 0 4px 12px rgba(0,0,0,0.15); }}
        .run-date {{ font-weight: bold; color: {COLORS['primary']}; min-width: 100px; }}
        .run-stats {{ flex: 1; display: flex; gap: 1.5rem; flex-wrap: wrap; }}
        .run-stat {{ font-size: 0.9rem; color: {COLORS['text_light']}; }}
        .run-stat strong {{ color: {COLORS['text']}; }}
        .run-map-btn {{ padding: 0.5rem 1rem; background: {COLORS['secondary']}; color: white; border: none; border-radius: 6px; cursor: pointer; transition: opacity 0.2s; }}
        .run-map-btn:hover {{ opacity: 0.9; }}
        #map {{ width: 100%; height: 400px; border-radius: 12px; margin-top: 1rem; }}
        .badge {{ display: inline-block; padding: 0.25rem 0.75rem; border-radius: 20px; font-size: 0.8rem; font-weight: 600; }}
        .badge-run {{ background: {COLORS['accent']}; color: white; }}
        @media (max-width: 640px) {{ .run-item {{ flex-direction: column; align-items: flex-start; }} .run-stats {{ width: 100%; }} }}
    </style>
</head>
<body>
    <header class="header">
        <h1>🏃 跑步日记</h1>
        <p>记录每一次奔跑的足迹</p>
    </header>

    <div class="container">
        <!-- 统计面板 -->
        <div class="stats-grid">
            <div class="stat-card">
                <div class="value">{stats.get('total_activities', 0)}</div>
                <div class="label">总跑步次数</div>
            </div>
            <div class="stat-card">
                <div class="value">{stats.get('total_distance', 0)}</div>
                <div class="label">总距离 (km)</div>
            </div>
            <div class="stat-card">
                <div class="value">{stats.get('monthly_count', 0)}</div>
                <div class="label">本月次数</div>
            </div>
            <div class="stat-card">
                <div class="value">{stats.get('monthly_dist', 0)}</div>
                <div class="label">本月距离 (km)</div>
            </div>
            <div class="stat-card">
                <div class="value">{stats.get('total_calories', 0)}</div>
                <div class="label">总消耗 (卡路里)</div>
            </div>
            <div class="stat-card">
                <div class="value">{stats.get('total_elevation', 0)}</div>
                <div class="label">总爬升 (m)</div>
            </div>
        </div>

        <!-- 月度趋势图 -->
        <div class="chart-section">
            <h2>📈 月度跑步统计</h2>
            <canvas id="monthlyChart"></canvas>
        </div>

        <!-- 路线热力图 -->
        <div class="chart-section">
            <h2>🗺️ 跑步路线地图</h2>
            <div id="map"></div>
        </div>

        <!-- 最近跑步记录 -->
        <div class="chart-section">
            <h2>📋 最近跑步记录</h2>
            <div class="runs-list">
"""

    for a in recent:
        date = a.get('date', '')
        title = a.get('title', '')
        dist = a.get('distance', 0)
        dur = format_duration(a.get('duration', 0))
        pace = format_pace(a.get('speed_ms', 0))
        hr = a.get('average_heartrate', '')
        cal = a.get('calories', '')
        sid = a.get('id', '')

        hr_str = f"{int(hr)} bpm" if hr else "--"
        cal_str = f"{int(cal)} kcal" if cal else "--"
        map_url = a.get('map_url', '') or f"maps/map_{sid}.png"

        html += f"""
                <div class="run-item">
                    <span class="run-date">{date}</span>
                    <span class="badge badge-run">跑步</span>
                    <div class="run-stats">
                        <span class="run-stat"><strong>{title}</strong></span>
                        <span class="run-stat">📏 {dist:.1f} km</span>
                        <span class="run-stat">⏱️ {dur}</span>
                        <span class="run-stat">🏃 {pace}</span>
                        <span class="run-stat">❤️ {hr_str}</span>
                        <span class="run-stat">🔥 {cal_str}</span>
                    </div>
                    <button class="run-map-btn" onclick="showMap('{sid}')">查看地图</button>
                </div>
"""

    # 注入配速热力图数据
    html += f"""            </div>
        </div>
    </div>

    <script>
        // 月度统计图
        const monthlyCtx = document.getElementById('monthlyChart').getContext('2d');
        new Chart(monthlyCtx, {{
            type: 'line',
            data: {{{monthly_chart}}},
            options: {{
                responsive: true,
                interaction: {{ mode: 'index', intersect: false }},
                scales: {{
                    y: {{ beginAtZero: true, title: {{ display: true, text: '次数' }} }},
                    y1: {{ type: 'linear', display: true, position: 'right',
                        title: {{ display: true, text: '距离(km)' }},
                        grid: {{ drawOnChartArea: false }}
                    }}
                }}
            }}
        }});

        // 地图（中心取自实际活动坐标）
        const map = L.map('map').setView([{map_center_lat:.4f}, {map_center_lng:.4f}], 12);
        L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
            attribution: '© OpenStreetMap'
        }}).addTo(map);

        // 绘制所有有路线的活动，并自动缩放到合适范围
        const routeData = {route_data_json};
        const allCoords = [];
        routeData.forEach(r => {{
            const coords = polyline.decode(r.polyline);
            if (coords.length > 0) {{
                L.polyline(coords, {{ color: r.color, weight: 3, opacity: 0.6 }}).addTo(map);
                coords.forEach(c => allCoords.push(c));
            }}
        }});
        if (allCoords.length > 0) {{
            map.fitBounds(allCoords, {{ padding: [20, 20] }});
        }}

        function showMap(id) {{
            const run = {json.dumps({a.get('id', ''): a for a in activities})};
            const r = run[id] || {{}};
            if (r.polyline) {{
                const coords = polyline.decode(r.polyline);
                map.fitBounds([coords]);
                L.polyline(coords, {{color: '#10b981', weight: 6}}).addTo(map);
                const popup = L.popup()
                    .setLatLng(coords[Math.floor(coords.length/2)])
                    .setContent(`<b>${{r.title || '跑步记录'}}</b><br/>距离: ${{r.distance}} km<br/>配速: ${{Math.round(1000/r.speed_ms)}}分/公里`)
                    .openOn(map);
            }}
        }}

        // polyline解码库
        var polyline = {{}};
        polyline.decode = function(str) {{
            if (!str) return [];
            let index = 0, lat = 0, lng = 0, coordinates = [];
            let shift, result, byte;
            while (index < str.length) {{
                byte = null; shift = 0; result = 0;
                do {{
                    byte = str.charCodeAt(index++) - 63;
                    result |= (byte & 0x1f) << shift;
                    shift += 5;
                }} while (byte >= 0x20);
                lat += ((result & 1) ? ~(result >> 1) : (result >> 1));
                shift = 0; result = 0;
                do {{
                    byte = str.charCodeAt(index++) - 63;
                    result |= (byte & 0x1f) << shift;
                    shift += 5;
                }} while (byte >= 0x20);
                lng += ((result & 1) ? ~(result >> 1) : (result >> 1));
                coordinates.push([lat * 1e-5, lng * 1e-5]);
            }}
            return coordinates;
        }};
    </script>
</body>
</html>
"""

    return html


def main():
    print("加载跑步数据...")
    data = load_data()
    activities = data.get('activities', [])
    print(f"找到 {len(activities)} 次跑步记录")

    if not activities:
        print("⚠  警告：没有跑步记录，将生成空页面")

    print("生成静态网站...")
    html = generate_html(data)

    os.makedirs('docs', exist_ok=True)
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"✅ 网站已生成: {OUTPUT_FILE}")
    print(f"   总跑步次数: {len(activities)}")
    if activities:
        total_dist = sum(a.get('distance', 0) for a in activities)
        print(f"   总距离: {total_dist:.1f} km")


if __name__ == '__main__':
    main()
