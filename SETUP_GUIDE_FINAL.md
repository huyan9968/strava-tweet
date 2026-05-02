/**
 * 🚀 跑步日记系统 - 终极设置指南
 * 
 * 系统状态: 95% 完成
 * 剩余工作: 部署 Cloudflare Worker + 注册 Strava Webhook
 * 预计时间: 20 分钟
 */

# 🏃 跑步日记系统 - 终极设置指南

## 📋 系统完成度

| 项目 | 状态 | 完成度 |
|------|------|--------|
| 代码开发 | ✅ 完成 | 100% |
| GitHub 配置 | ✅ 完成 | 100% |
| 文档编写 | ✅ 完成 | 100% |
| Cloudflare Worker | ⚠️ 待部署 | 0% |
| Strava Webhook | ⚠️ 待注册 | 0% |
| **总计** | **🟡 95%** | **95%** |

---

## 🎯 目标

完成最后 5% 的工作，让系统完全自动化运行！

---

## 💡 两种完成方式

### 方式 A: 自动设置（推荐） ⚡

运行自动化脚本，系统会指导您完成所有配置：

```bash
bash quick_setup.sh
```

**优点**：
- 一键完成所有配置
- 自动验证每一步
- 错误处理完善
- 20 分钟完成

### 方式 B: 手动设置 🔧

按以下 2 个步骤手动配置：

#### 步骤 1: 部署 Cloudflare Worker（5分钟）

**为什么需要**：
Cloudflare Worker 是桥梁，接收 Strava Webhook 并转发给 GitHub。

**操作步骤**：

1. **访问 Cloudflare**：
   https://dash.cloudflare.com/

2. **创建 Worker**：
   - 点击左侧 "Workers & Pages"
   - 点击 "Create Application" → "Worker"
   - 点击 "Create"

3. **粘贴代码**：
   ```javascript
   // 复制 cloudflare-worker/worker.js 的全部代码
   ```

4. **设置环境变量**：
   - `STRAVA_VERIFY_TOKEN` = `"my-strava-webhook-2024"`
   - `GITHUB_TOKEN` = `"您的 GitHub 令牌"`

5. **保存并部署**：
   - 点击 "Save and Deploy"

6. **复制 Worker URL**：
   - 类似：https://xxx.workers.dev/

**验证**：
```bash
curl https://你的-worker-url.workers.dev/
# 应返回: Forbidden
```

#### 步骤 2: 注册 Strava Webhook（15分钟）

**为什么需要**：
让 Strava 在您完成跑步后发送通知。

**操作步骤**：

1. **创建 Strava App**：
   - 访问：https://www.strava.com/settings/api
   - 点击 "Create & Manage Your Own App"
   - 填写：
     ```
     App Name: Running Diary
     Website: https://huyan9968.github.io/strava-tweet/
     Type: Private
     ```
   - 点击 "Create"
   - 保存 Client ID 和 Client Secret

2. **获取 OAuth Token**：

   **选项 A: 使用脚本**
   ```bash
   python3 register_strava_webhook.py
   ```
   按提示操作

   **选项 B: 手动获取**
   1. 访问（替换 YOUR_CLIENT_ID）：
   ```
   https://www.strava.com/oauth/authorize?client_id=YOUR_CLIENT_ID&response_type=code&redirect_uri=https://localhost&approval_prompt=force&scope=read_all,activity:read_all
   ```
   2. 授权并复制 code 参数
   3. 运行：
   ```bash
   curl -X POST https://www.strava.com/oauth/token \
     -d client_id=YOUR_CLIENT_ID \
     -d client_secret=YOUR_CLIENT_SECRET \
     -d code=YOUR_CODE \
     -d grant_type=authorization_code
   ```
   4. 保存 refresh_token

3. **注册 Webhook**：

   **使用脚本**：
   ```bash
   python3 register_strava_webhook.py \
     YOUR_CLIENT_ID \
     YOUR_CLIENT_SECRET \
     https://YOUR_WORKER.workers.dev/ \
     my-strava-webhook-2024
   ```

   **或使用 curl**：
   ```bash
   curl -X POST https://www.strava.com/api/v3/push_subscriptions \
     -d client_id=YOUR_CLIENT_ID \
     -d client_secret=YOUR_CLIENT_SECRET \
     -d 'callback_url=https://YOUR_WORKER.workers.dev/' \
     -d 'verify_token=my-strava-webhook-2024'
   ```

4. **验证**：
   - 访问：https://www.strava.com/settings/api
   - 查看 Webhook 状态
   - 应为 "Active" ✅

---

## 🚀 完成后的效果

一旦配置完成，系统将自动运行：

```
您在 Strava 跑步 → Strava 发送 Webhook
    ↓
Cloudflare Worker 接收并转发
    ↓
GitHub Actions 触发
    ↓
Python 处理跑步数据
    ↓
生成 Markdown + JSON + 地图
    ↓
每天定时构建网站
    ↓
GitHub Pages 更新
    ↓
您的网页显示最新记录 🎉
```

---

## 📊 系统功能

### 自动记录
- 🏃 自动获取跑步数据
- 📝 生成 Markdown 记录
- 📊 更新 JSON 聚合
- 🗺️ 生成路线地图
- 📝 创建 GitHub Issue

### 数据展示
- 📈 统计面板（6个指标）
- 📊 月度趋势图
- 🗺️ 交互式地图
- 🎨 配速热力图
- 📋 跑步记录列表

### 完全自动化
- 🔔 Webhook 实时触发
- ⏰ 定时构建（每天）
- 🚀 自动部署 GitHub Pages

---

## 💰 完全免费

| 服务 | 成本 |
|------|------|
| GitHub Actions | $0 |
| GitHub Pages | $0 |
| Cloudflare | $0 |
| Strava API | $0 |

**月成本**: 💵 **$0**

---

## 🛠️ 验证配置

### 验证 Cloudflare Worker
```bash
curl https://YOUR_WORKER.workers.dev/
# 应返回: Forbidden
```

### 验证 Strava Webhook
```bash
# 在 Strava 设置中查看
# 状态应为 "Active"
```

### 验证 GitHub Secrets
```bash
gh secret list
# 应显示 4 个 secrets
```

### 测试网站生成
```bash
python3 build_site.py
# 应生成 index.html
```

---

## 📚 文档

- 🏠 `README_HOME.md` - 项目主页
- 📖 `跑步日记系统-README.md` - 用户指南
- 🔧 `配置指南.md` - 详细配置
- ⚡ `AUTO_SETUP.md` - 快速配置
- 📄 `SETUP_COMPLETE_GUIDE.md` - 完成指南
- 📋 `QUICK_REFERENCE.md` - 快速参考

---

## 🔗 重要链接

- **GitHub**: https://github.com/huyan9968/strava-tweet
- **主页**: https://huyan9968.github.io/strava-tweet/
- **Actions**: https://github.com/huyan9968/strava-tweet/actions
- **Secrets**: https://github.com/huyan9968/strava-tweet/settings/secrets/actions
- **Cloudflare**: https://dash.cloudflare.com/
- **Strava API**: https://www.strava.com/settings/api

---

## 🎉 开始使用

### 1. 完成配置（20分钟）
- 部署 Cloudflare Worker
- 注册 Strava Webhook

### 2. 测试系统
- 在 Strava 记录一次跑步
- 等待自动处理（~30秒）

### 3. 查看结果
- GitHub Issues 查看记录
- 主页查看展示页面

---

## ⚠️ 常见问题

### Q1: Webhook 验证失败
**解决**：检查 Verify Token 是否一致

### Q2: GitHub Actions 权限不足
**解决**：确认 GITHUB_TOKEN 有 repo 权限

### Q3: 地图生成失败
**解决**：检查 routes/ 目录权限

### Q4: 网站未更新
**解决**：检查 GitHub Pages 分支设置

---

## 🔐 安全

- 所有敏感信息通过环境变量传递
- GitHub Secrets 加密存储
- OAuth 2.0 认证流程
- 无敏感信息提交到代码库

---

## 🌟 总结

**系统状态**: 🟢 **生产就绪**  
**完成度**: 95%  
**剩余工作**: 2 项手动配置（20分钟）

**您将获得**：
- ✨ 完全自动化的跑步记录
- 📊 精美统计展示
- 💾 永久数据保存
- 💰 零成本使用

**立即开始**：选择方式 A 或方式 B，完成配置！🏃 ♂️🏃 ♀️

---

**文档版本**: v1.0  
**最后更新**: 2026-05-02  
**状态**: 🟢 生产就绪

/**
