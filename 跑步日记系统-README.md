
# 跑步日记系统 - Strava Webhook + GitHub Pages

## 📖 功能概述

本系统实现了基于 Strava Webhook 的自动跑步记录功能，包含：

### 核心功能 1️⃣：自动跑步日记
- **触发方式**：Strava Webhook → Cloudflare Worker → GitHub Repository Dispatch
- **数据处理**：GitHub Actions 获取跑步详情（距离、时长、配速、心率、卡路里、路线）
- **输出文件**：
  - `runs/YYYY-MM-DD-run-{id}.md` - Markdown 格式的跑步记录
  - `data/activities.json` - 聚合的跑步数据（用于前端展示）
  - `maps/map_{id}.png` - 跑步路线截图
  - GitHub Issue - 自动生成的跑步记录卡片

### 核心功能 2️⃣：跑步主页
- **技术栈**：HTML + CSS + JavaScript + Chart.js + Leaflet.js
- **数据源**：`data/activities.json`
- **展示内容**：
  - 📊 统计面板（总距离、次数、消耗等）
  - 📈 月度趋势图（跑步次数、距离）
  - 🗺️ 交互式路线地图（含配速热力图）
  - 📋 最近跑步记录列表
- **部署**：GitHub Actions 自动构建 → GitHub Pages

## 🏗️ 系统架构

```
strava-tweet/
├── cloudflare-worker/          # Cloudflare Worker
│   ├── worker.js               # 处理 Strava Webhook
│   └── wrangler.toml           # Worker 配置
├── .github/workflows/
│   ├── strava_tweet.yml        # Webhook 触发：处理跑步数据
│   └── build_site.yml          # 定时/手动触发：构建静态网站
├── runs/                       # 跑步记录 Markdown 文件
├── data/
│   └── activities.json         # 聚合的跑步数据
├── maps/                       # 路线地图图片
├── strava_tweet.py             # 主程序：获取数据、生成内容
├── build_site.py               # 静态网站生成器
├── index.html                  # 首页（GitHub Pages）
└── requirements.txt            # Python 依赖
```

## 🔧 工作流程详解

### 流程 1：Webhook 触发（实时）

```
1. Strava 新建活动 → Strava 发送 Webhook
     ↓
2. Cloudflare Worker (worker.js)
   - 验证 webhook (hub.verify_token)
   - 调用 GitHub API 触发 repository_dispatch
     ↓
3. GitHub Actions (strava_tweet.yml)
   - 下载 Python 依赖
   - 调用 strava_tweet.py
     ↓
4. strava_tweet.py 执行
   - 获取 Strava OAuth 令牌
   - 获取最新跑步详情
   - 生成配速、心率等统计数据
   - 🆕 写入 runs/ 目录的 Markdown 文件
   - 🆕 更新 data/activities.json
   - 生成路线地图并上传
   - 创建 GitHub Issue
```

### 流程 2：静态网站构建（定时 + 手动）

```
1. GitHub Actions (build_site.yml) 触发
   - 定时：每天 UTC 2:00
   - 手动：workflow_dispatch
   - 数据更新：repository_dispatch
     ↓
2. build_site.py 执行
   - 读取 data/activities.json
   - 读取所有 Markdown 记录
   - 计算统计数据
   - 生成 index.html（含 Chart.js 图表）
     ↓
3. GitHub Pages 自动部署
   - 提交更改到 main 分支
   - GitHub Pages 构建并发布
```

## 📄 Markdown 跑步记录格式

```markdown
---
id: 123456789
date: 2024-12-09
title: 晨间跑步
sport_type: Run
distance: 10.5
duration: 3600
moving_time: 3540
average_speed: 2.94
average_heartrate: 145
calories: 650
max_speed: 3.89
elevation_gain: 45
start_latlng: [39.9042, 116.4074]
end_latlng: [39.9042, 116.4074]
polyline: "加密路线字符串..."
---

## 今日跑步数据

| 项目 | 数据 |
|------|------|
| **距离** | 10.5 公里 |
| **时长** | 60分钟0秒 |
| **配速** | 5'41"/km |
| ... | ... |

## 路线地图

![路线地图](maps/map_123456789.png)
```

## 🎨 静态网站展示

### 首页包含：

1. **统计面板**（6个卡片）
   - 总跑步次数
   - 总距离 (km)
   - 本月次数
   - 本月距离 (km)
   - 总消耗 (卡路里)
   - 总爬升 (米)

2. **月度趋势图** (Chart.js)
   - 双Y轴：跑步次数 + 距离
   - 展示历史月度数据

3. **路线地图** (Leaflet.js)
   - 所有跑步路线叠加显示
   - 配速热力图（颜色代表配速快慢）
   - 点击按钮可定位到具体跑步

4. **最近跑步记录**
   - 日期、标题、距离、时长、配速、心率、卡路里
   - 查看地图按钮

## ⚙️ 配置说明

### Secrets 需要配置：

| 名称 | 说明 | 来源 |
|------|------|------|
| `STRAVA_CLIENT_ID` | Strava App Client ID | Strava 开发者后台 |
| `STRAVA_CLIENT_SECRET` | Strava App Secret | Strava 开发者后台 |
| `STRAVA_REFRESH_TOKEN` | Strava OAuth Refresh Token | 通过 OAuth 2.0 获取 |
| `STRAVA_VERIFY_TOKEN` | Webhook 验证 Token | 自定义字符串 |
| `GITHUB_TOKEN` | GitHub Personal Access Token | GitHub → Settings → Developer settings |
| `GITHUB_REPOSITORY` | 仓库名 (格式: owner/repo) | 自动注入 |

### Cloudflare Worker 环境变量：

- `STRAVA_VERIFY_TOKEN` - 与上面一致
- `GITHUB_TOKEN` - GitHub PAT (需 repo 权限)

### Strava App 配置：

1. https://www.strava.com/settings/api
2. 创建 App → "Create & Manage Your Own App"
3. 回调 URL：https://YOUR_WORKER.workers.dev/
4. 权限：至少需要 `read_all`（活动读取）
5. 注册 Webhook：
   ```
   Callback URL: https://YOUR_WORKER.workers.dev/
   Verify Token: 自定义字符串
   ```

## 🚀 本地测试

### 1. 测试静态网站生成

```bash
cd strava-tweet
python3 build_site.py
# 生成 index.html
```

### 2. 测试 Strava 数据获取（需要配置环境变量）

```bash
export STRAVA_CLIENT_ID=xxx
export STRAVA_CLIENT_SECRET=xxx
export STRAVA_REFRESH_TOKEN=xxx

cd strava-tweet
python3 strava_tweet.py
```

### 3. 本地预览网站

```bash
# 使用 Python HTTP 服务器
python3 -m http.server 8000
# 访问 http://localhost:8000
```

## 🔐 安全注意事项

1. **不要提交敏感信息**
   - 不要在代码中硬编码 Token
   - 使用 GitHub Secrets 保护敏感数据
   - Cloudflare Worker 也使用环境变量

2. **权限控制**
   - GitHub Token 只需要 `repo` 权限
   - Strava App 限制回调域名
   - Cloudflare Worker 验证 Token

3. **数据隐私**
   - 路线地图可能暴露地理位置
   - 公开页面时考虑隐私影响
   - 可设置为私有仓库

## 📈 扩展功能建议

- [ ] 添加跑步类型筛选（路跑、越野跑、室内跑）
- [ ] 天气数据集成（温度、湿度）
- [ ] 成就系统（里程碑、周/月目标）
- [ ] 数据导出（CSV/GPX）
- [ ] 个人最佳记录（PB）追踪
- [ ] 社交分享功能
- [ ] 年度回顾页面

## 🐛 故障排查

### 问题：Webhook 验证失败
**解决**：检查 `STRAVA_VERIFY_TOKEN` 是否一致

### 问题：GitHub Actions 权限不足
**解决**：确保 GITHUB_TOKEN 有 `repo` 权限

### 问题：地图生成失败
**解决**：安装中文字体或简化地图渲染

### 问题：Strava 令牌过期
**解决**：更新 `STRAVA_REFRESH_TOKEN`

## 📄 开源协议

MIT License - 自由使用和修改

## 🔗 相关链接

- [Strava API 文档](https://developers.strava.com/docs/reference/)
- [GitHub Pages](https://pages.github.com/)
- [Cloudflare Workers](https://workers.cloudflare.com/)
