
# 🚀 一键自动配置指南

## 剩余工作：最后 5% ⚠️

| 项目 | 状态 | 时间 |
|------|------|------|
| Cloudflare Worker 部署 | ⚠️ 待完成 | ~5 分钟 |
| Strava Webhook 注册 | ⚠️ 待完成 | ~15 分钟 |
| **总计** | **~20 分钟** | |

---

## 🎯 快速完成步骤

### 步骤 1：准备信息（2分钟）

您需要准备以下信息：

1. **Cloudflare 账户**
   - 注册：https://dash.cloudflare.com/
   - 登录即可

2. **Strava App 信息**
   - 访问：https://www.strava.com/settings/api
   - 创建 App
   - 获取 `Client ID` 和 `Client Secret`

3. **OAuth 授权**
   - 使用以下链接获取授权码：
   ```
   https://www.strava.com/oauth/authorize?client_id=YOUR_CLIENT_ID&response_type=code&redirect_uri=https://localhost&approval_prompt=force&scope=read_all,activity:read_all
   ```

### 步骤 2：部署 Cloudflare Worker（3分钟）⏱️

#### 方法 A：手动部署（推荐）

1. 访问：https://dash.cloudflare.com/
2. 点击左侧 **"Workers & Pages"**
3. 点击 **"Create Application"** → **"Worker"**
4. 点击 **"Create"** 按钮
5. **删除默认代码**，粘贴以下内容：

```javascript
/**
 * Strava Webhook → GitHub Actions 触发器
 * 
 * 环境变量：
 *   STRAVA_VERIFY_TOKEN  = "my-strava-webhook-2024"
 *   GITHUB_TOKEN         = "ghp_xxxxxxxxxxxx" (您的 GitHub PAT)
 */

const GITHUB_REPO = 'huyan9968/strava-tweet';

export default {
  async fetch(request, env) {
    const url = new URL(request.url);

    // GET: 验证请求
    if (request.method === 'GET') {
      const mode      = url.searchParams.get('hub.mode');
      const challenge = url.searchParams.get('hub.challenge');
      const token     = url.searchParams.get('hub.verify_token');

      if (mode === 'subscribe' && token === env.STRAVA_VERIFY_TOKEN) {
        return Response.json({ 'hub.challenge': challenge });
      }
      return new Response('Forbidden', { status: 403 });
    }

    // POST: Webhook 通知
    if (request.method === 'POST') {
      let body;
      try {
        body = await request.json();
      } catch {
        return new Response('Bad Request', { status: 400 });
      }

      // 只处理新活动
      if (body.object_type === 'activity' && body.aspect_type === 'create') {
        const resp = await fetch(
          `https://api.github.com/repos/${GITHUB_REPO}/dispatches`,
          {
            method: 'POST',
            headers: {
              Authorization:  `token ${env.GITHUB_TOKEN}`,
              Accept:         'application/vnd.github.v3+json',
              'Content-Type': 'application/json',
              'User-Agent':   'strava-webhook-worker',
            },
            body: JSON.stringify({ event_type: 'strava_activity' }),
          }
        );

        if (!resp.ok) {
          const text = await resp.text();
          return new Response(`GitHub trigger failed: ${text}`, { status: 502 });
        }
      }

      return new Response('OK');
    }

    return new Response('Not Found', { status: 404 });
  },
};
```

6. 点击 **"Save and Deploy"** 按钮
7. 复制您的 Worker URL（类似：https://your-worker.workers.dev/）

#### 方法 B：使用 Wrangler CLI

如果熟悉命令行，可以使用 Wrangler：

```bash
# 安装 Wrangler
npm install -g wrangler

# 登录 Cloudflare
wrangler login

# 部署
cd cloudflare-worker
wrangler deploy
```

### 步骤 3：设置环境变量（1分钟）

在 Cloudflare Worker 页面：

1. 点击 **"Settings"** 标签
2. 找到 **"Variables"** 部分
3. 点击 **"Add"** 添加：

| 变量名 | 值 | 说明 |
|--------|-----|------|
| `STRAVA_VERIFY_TOKEN` | `my-strava-webhook-2024` | 自定义验证字符串 |
| `GITHUB_TOKEN` | `ghp_xxxxxxxxxxxx` | GitHub Personal Access Token |

4. 点击 **"Save"**

### 步骤 4：注册 Strava Webhook（5分钟）⏱️

#### 4.1 创建 Strava App

1. 访问：https://www.strava.com/settings/api
2. 滚动到底部，点击 **"Create & Manage Your Own App"**
3. 填写表单：
   ```
   App Name:         Running Diary
   Website:          https://huyan9968.github.io/strava-tweet/
   Application Type: Private（私有）
   ```
4. 点击 **"Create"**

#### 4.2 获取 OAuth Token

**方法 A：使用脚本（推荐）**

运行脚本：
```bash
python3 get_oauth_token.py YOUR_CLIENT_ID
```

按提示操作，获取 `Refresh Token`

**方法 B：手动获取**

1. 访问授权链接（替换 YOUR_CLIENT_ID）：
```
https://www.strava.com/oauth/authorize?client_id=YOUR_CLIENT_ID&response_type=code&redirect_uri=https://localhost&approval_prompt=force&scope=read_all,activity:read_all
```

2. 授权后，复制地址栏的 `code` 参数

3. 使用 curl 获取 Token：
```bash
curl -X POST https://www.strava.com/oauth/token \
  -d client_id=YOUR_CLIENT_ID \
  -d client_secret=YOUR_CLIENT_SECRET \
  -d code=YOUR_AUTH_CODE \
  -d grant_type=authorization_code
```

4. 保存响应中的 `refresh_token`

#### 4.3 注册 Webhook

使用以下命令注册（替换相应值）：

```bash
curl -X POST https://www.strava.com/api/v3/push_subscriptions \
  -d client_id=YOUR_CLIENT_ID \
  -d client_secret=YOUR_CLIENT_SECRET \
  -d 'callback_url=https://YOUR_WORKER.workers.dev/' \
  -d 'verify_token=my-strava-webhook-2024'
```

成功响应：
```json
{
  "id": 12345,
  "resource_state": 2,
  "object_type": "activity",
  "aspect_type": "create",
  "callback_url": "https://your-worker.workers.dev/",
  "verify_token": "my-strava-webhook-2024",
  "status": "active"
}
```

### 步骤 5：验证配置（2分钟）⏱️

#### 5.1 验证 Worker

```bash
curl https://YOUR_WORKER.workers.dev/
# 应返回: Forbidden
```

#### 5.2 验证 Webhook

在 Strava 设置页面：
- Webhook 状态应为 **"Active"** ✅

#### 5.3 测试 GitHub Actions

访问：https://github.com/huyan9968/strava-tweet/actions

点击 **"Run workflow"**，运行测试：
- 应看到绿色 ✓ 成功标志

---

## 📝 配置检查清单

完成配置后，请核对：

### ✅ 已完成
- [x] GitHub Secrets 配置
- [x] GitHub Actions 工作流
- [x] GitHub Pages 启用
- [x] 代码开发完成
- [x] 文档编写完成

### ⚠️ 待完成
- [ ] Cloudflare Worker 部署
- [ ] Strava App 创建
- [ ] OAuth Token 获取
- [ ] Webhook 注册
- [ ] 系统测试

---

## 🚀 完成后的效果

### 自动流程

```
您在 Strava 跑步 → Strava 发送 Webhook
    ↓
Cloudflare Worker 接收 → GitHub Actions 触发
    ↓
Python 处理数据 → 生成 Markdown + JSON
    ↓
上传地图 → 创建 GitHub Issue
    ↓
每天定时构建 → GitHub Pages 更新
    ↓
您访问主页 → 看到最新跑步记录！🎉
```

### 主页展示

访问：https://huyan9968.github.io/strava-tweet/

您将看到：
- 📊 统计面板（6个指标）
- 📈 月度趋势图
- 🗺️ 交互式路线地图
- 📋 跑步记录列表

---

## 🔄 自动化频率

| 触发方式 | 频率 | 说明 |
|----------|------|------|
| Webhook | 实时 | 每次跑步后立即触发 |
| 定时构建 | 每天 UTC 2:00 | 自动更新主页 |
| 手动触发 | 随时 | 通过 GitHub Actions |

---

## 🔧 故障排除

### 问题 1：Webhook 验证失败
**解决方案**：
- 检查 Verify Token 是否一致
- 确保 Worker URL 正确

### 问题 2：GitHub Actions 权限不足
**解决方案**：
- 确认 GITHUB_TOKEN 有 `repo` 权限
- 检查 Secrets 是否正确

### 问题 3：地图生成失败
**解决方案**：
- 检查 routes/ 目录是否存在
- 确认有写权限

### 问题 4：网站未更新
**解决方案**：
- 检查 GitHub Actions 执行日志
- 确认 GitHub Pages 分支设置
- 等待几分钟（构建需要时间）

---

## 💡 提示与建议

1. **首次使用**：手动触发一次工作流进行测试
2. **监控**：定期检查 GitHub Actions 日志
3. **备份**：所有数据已保存在 GitHub 仓库中
4. **扩展**：可轻松添加新的统计指标
5. **自定义**：可修改主页样式和设计

---

## 📞 获取帮助

### 文档
- 跑步日记系统-README.md - 用户指南
- 配置指南.md - 详细配置说明
- CONFIG_STATUS.md - 当前状态

### 问题反馈
- GitHub Issues: https://github.com/huyan9968/strava-tweet/issues

---

## ✨ 最后的鼓励

恭喜！您已经完成了 95% 的工作！

只需要再花 **20 分钟** 完成最后两步：
1. 部署 Cloudflare Worker（5分钟）
2. 注册 Strava Webhook（15分钟）

之后，您的系统将**全自动运行**，记录每一次奔跑，展示每一个成就！🏃 ♂️🏃 ♀️✨

**快去完成配置，然后去跑步吧！** 🏃 ♂️💨

---

**预计完成时间**: 20 分钟  
**系统状态**: 🟡 95% 完成  
**难度**: ⭐⭐☆ 中等  
**价值**: 💎 无价（完全自动化记录您的每一次奔跑！）
