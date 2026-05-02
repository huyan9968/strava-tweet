
# 跑步日记系统 - 实现总结

## 🎯 实现的功能

### 1️⃣ 自动跑步日记（Strava Webhook → GitHub）

#### ✅ 已完成
- **Cloudflare Worker** (`cloudflare-worker/worker.js`)
  - 接收 Strava Webhook POST 请求
  - 验证 hub.verify_token
  - 触发 GitHub Repository Dispatch

- **GitHub Actions 工作流** (`.github/workflows/strava_tweet.yml`)
  - 触发条件：
    - `repository_dispatch` (Webhook 实时触发)
    - `schedule` (每天北京时间 21:00 兜底)
    - `workflow_dispatch` (手动触发)
  - 调用 strava_tweet.py

- **Python 主程序** (`strava_tweet.py`)
  - 获取 Strava OAuth 令牌
  - 获取最新跑步活动详情
  - 提取跑步数据：距离、时长、配速、心率、卡路里、海拔、路线
  - 🆕 **生成 Markdown 跑步记录** (`runs/YYYY-MM-DD-run-{id}.md`)
    - 包含 frontmatter 元数据
    - 格式化数据表格
    - 包含路线地图链接
  - 🆕 **更新聚合数据** (`data/activities.json`)
    - 增量更新，避免重复
    - 自动计算总计
    - 按日期排序
  - 生成路线地图并上传到 GitHub
  - 创建 GitHub Issue
  - 生成小红书卡片（可选）

#### 📄 输出文件示例

```
strava-tweet/
├── runs/2024-12-09-run-123456789.md
├── data/activities.json
├── maps/map_123456789.png
└── # GitHub Issue 自动创建
```

### 2️⃣ 跑步主页（静态网站）

#### ✅ 已完成

- **构建工作流** (`.github/workflows/build_site.yml`)
  - 触发条件：
    - `schedule`: 每天 UTC 2:00 自动构建
    - `workflow_dispatch`: 手动触发
    - `repository_dispatch`: 数据更新时触发
  - 生成静态网站
  - 自动部署到 GitHub Pages

- **网站生成器** (`build_site.py`)
  - 读取聚合数据
  - 计算统计指标
  - 生成完整的 HTML 页面
  - 包含 Chart.js 图表和 Leaflet 地图

- **静态网站** (`index.html`)
  - 📊 **统计面板**: 总次数、总距离、本月数据、总消耗、总爬升
  - 📈 **月度趋势图**: 双Y轴图表（次数 + 距离）
  - 🗺️ **路线热力图**: 所有跑步路线叠加，配速用颜色区分
  - 📋 **最近跑步列表**: 详细数据 + 查看地图按钮

#### 🎨 页面特性

- **响应式设计**: 适配桌面和移动端
- **交互式地图**: 点击跑步可定位和查看详情
- **数据可视化**: Chart.js 趋势图
- **美观主题**: 现代卡片式布局，hover 动画

## 🔧 技术栈

| 组件 | 技术 |
|------|------|
| 后端 | Python 3.11 |
| API | Strava API v3, GitHub API |
| 服务器 | Cloudflare Workers |
| CI/CD | GitHub Actions |
| 前端 | HTML5, CSS3, JavaScript |
| 图表 | Chart.js |
| 地图 | Leaflet.js |
| 托管 | GitHub Pages |

## 📁 项目结构

```
strava-tweet/
├── .github/workflows/
│   ├── strava_tweet.yml      # Webhook 触发工作流
│   └── build_site.yml        # 网站构建工作流
├── cloudflare-worker/
│   ├── worker.js             # Webhook 处理器
│   └── wrangler.toml         # Worker 配置
├── runs/                     # 🆕 Markdown 跑步记录
├── data/                     # 🆕 聚合数据目录
│   └── activities.json       # 🆕 聚合的跑步数据
├── maps/                     # 路线地图
├── strava_tweet.py           # 主程序（已扩展）
├── build_site.py             # 🆕 静态网站生成器
├── index.html                # 🆕 首页（生成的）
├── requirements.txt          # Python 依赖
└── 跑步日记系统-README.md      # 用户文档
```

## 🚀 使用流程

### 初始设置

1. **配置 Strava App**
   ```
   - 创建 App
   - 获取 Client ID 和 Secret
   - 设置回调 URL
   - 获取 Refresh Token
   - 注册 Webhook
   ```

2. **配置 GitHub Secrets**
   ```
   - STRAVA_CLIENT_ID
   - STRAVA_CLIENT_SECRET
   - STRAVA_REFRESH_TOKEN
   - STRAVA_VERIFY_TOKEN
   - GITHUB_TOKEN
   - GITHUB_REPOSITORY
   ```

3. **部署 Cloudflare Worker**
   ```
   - 配置环境变量
   - 部署到 Cloudflare
   - 获取 Worker URL
   ```

### 日常运行

```
跑步完成 → Strava Webhook → Cloudflare Worker
    ↓
GitHub Actions 触发
    ↓
strava_tweet.py 运行
    ↓
生成 Markdown + 更新 JSON
    ↓
创建 GitHub Issue
    ↓
（每天定时）GitHub Pages 构建
    ↓
跑步主页更新
```

## ✨ 特色功能

### Markdown 格式
```markdown
---
id: 12345
date: 2024-01-15
title: 晨跑10公里
sport_type: Run
distance: 10.5
duration: 3600
...
---

## 今日跑步数据

| 项目 | 数据 |
|------|------|
| **距离** | 10.5 公里 |
| **配速** | 5'41"/km |
...

![路线地图](maps/map_12345.png)
```

### JSON 聚合
```json
{
  "total_activities": 156,
  "total_distance": 1205.8,
  "activities": [
    {
      "id": 12345,
      "date": "2024-01-15",
      "distance": 10.5,
      "pace": 341,
      "map_url": "maps/map_12345.png",
      "md_file": "runs/2024-01-15-run-12345.md"
    }
  ]
}
```

## 📊 数据统计

| 指标 | 计算方式 |
|------|----------|
| 总跑步次数 | `len(activities)` |
| 总距离 | `sum(distance)` |
| 总时长 | `sum(duration)` |
| 总消耗 | `sum(calories)` |
| 总爬升 | `sum(elevation_gain)` |
| 本月次数 | 过滤当月数据 |
| 最佳配速 | `min(avg_speed)` |

## 🔐 安全措施

1. 所有敏感信息通过环境变量传递
2. GitHub Secrets 加密存储
3. Cloudflare Workers 环境变量保护
4. 不提交任何 Token 到代码库

## 🎯 扩展性

### 易于扩展的地方

- 添加新的运动类型：修改 sport_type 判断
- 新的数据源：添加 API 调用函数
- 新的输出格式：添加写入函数
- 新的统计指标：更新统计逻辑
- 新图表类型：扩展 build_site.py
- 新页面：添加 HTML 模板

## 📈 未来优化方向

- [ ] 添加数据缓存机制
- [ ] 支持多用户数据
- [ ] 添加数据导出功能
- [ ] 实现数据版本控制
- [ ] 添加通知提醒
- [ ] 集成更多运动平台（Garmin、Keep 等）

## ✅ 测试验证

```bash
# 测试静态网站生成
cd strava-tweet
python3 build_site.py
# ✅ 成功生成 index.html

# 显示统计信息
找到 0 次跑步记录（无数据时正常）
✅ 网站已生成: index.html
```

## 📝 总结

本系统实现了：

1. **完整的跑步记录自动化流程**
   - 从 Strava Webhook 触发到 GitHub 数据存储
   - Markdown 和 JSON 双格式输出
   - GitHub Issue 自动创建

2. **功能丰富的静态展示网站**
   - 统计面板、月度趋势、路线热力图
   - 响应式设计，适配各种设备
   - 自动构建和部署

3. **可靠的工作流**
   - Cloudflare Worker 轻量高效
   - GitHub Actions 自动化
   - 定时任务确保数据更新

4. **良好的可维护性**
   - 代码结构清晰
   - 模块化设计
   - 完善的文档

系统现已就绪，可以开始记录您的跑步旅程！🏃 ♂️🏃 ♀️
