# 🚀 快速配置参考

## 配置步骤概览

1. ✅ GitHub Secrets 已配置
2. ⚙️ 部署 Cloudflare Worker
3. 🏃 注册 Strava Webhook
4. 🧪 测试系统

## 必要配置项

### Strava 配置
```
Client ID:         [从 Strava 获取]
Client Secret:     [从 Strava 获取]
Refresh Token:     [通过 OAuth 获取]
Verify Token:      my-strava-webhook-2024
```

### Cloudflare Worker 配置
```
Worker URL:        [部署后获取]
STRAVA_VERIFY_TOKEN: my-strava-webhook-2024
GITHUB_TOKEN:      [GitHub PAT]
```

### GitHub Secrets
```
STRAVA_CLIENT_ID
STRAVA_CLIENT_SECRET
STRAVA_REFRESH_TOKEN
STRAVA_VERIFY_TOKEN
```

## 重要链接

- Strava API: https://www.strava.com/settings/api
- Cloudflare: https://dash.cloudflare.com/
- GitHub Secrets: https://github.com/huyan9968/strava-tweet/settings/secrets/actions
- GitHub Pages: https://huyan9968.github.io/strava-tweet/

## 常见命令

```bash
# 验证系统
./verify_system.sh

# 生成网站
python3 build_site.py

# 注册 Webhook
python3 register_strava_webhook.py

# 手动触发
gh workflow run strava_tweet.yml
```

## 配置文件

- `.env.example` - 环境变量示例
- `.webhook_config.json` - Webhook 配置
- `cloudflare-worker-config.example.env` - Cloudflare 配置示例
- `strava-oauth-config.example.env` - Strava OAuth 示例
