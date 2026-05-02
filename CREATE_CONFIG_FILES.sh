
#!/bin/bash
#
# 📄 创建配置文件脚本
# 生成所有必要的配置文件
#

echo "正在创建配置文件..."

# 创建 Cloudflare Worker 配置示例
cat > cloudflare-worker-config.example.env << 'EOF'
# Cloudflare Worker 环境变量配置示例
# 复制此文件为 .env 并填入实际值

# Strava Webhook 验证 Token
STRAVA_VERIFY_TOKEN="my-strava-webhook-2024"

# GitHub Personal Access Token
# 创建地址: https://github.com/settings/tokens
# 权限要求: repo (完整控制)
GITHUB_TOKEN="ghp_xxxxxxxxxxxxxxxxxxxx"
EOF

print_success "创建: cloudflare-worker-config.example.env"

# 创建 Strava OAuth 配置示例
cat > strava-oauth-config.example.env << 'EOF'
# Strava OAuth 配置示例
# 复制此文件为 .env.strava 并填入实际值

# 在 https://www.strava.com/settings/api 创建应用后获取
STRAVA_CLIENT_ID="your_client_id"
STRAVA_CLIENT_SECRET="your_client_secret"

# 通过 OAuth 流程获取
# 参考: https://www.strava.com/oauth/authorize
STRAVA_REFRESH_TOKEN="your_refresh_token"

# Webhook 验证 Token（与 Cloudflare Worker 保持一致）
STRAVA_VERIFY_TOKEN="my-strava-webhook-2024"
EOF

print_success "创建: strava-oauth-config.example.env"

# 创建 GitHub Actions 配置示例
cat > .github-actions-config.example.yml << 'EOF'
# GitHub Actions 配置示例
# 此文件仅用于参考

name: Strava 跑步记录

on:
  schedule:
    - cron: '0 13 * * *'   # 每天北京时间 21:00
  workflow_dispatch:
  repository_dispatch:
    types: [strava_activity]

jobs:
  generate-tweet:
    runs-on: ubuntu-latest
    permissions:
      contents: write
      issues: write

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: pip install -r requirements.txt

      - name: Generate tweet
        env:
          STRAVA_CLIENT_ID: ${{ secrets.STRAVA_CLIENT_ID }}
          STRAVA_CLIENT_SECRET: ${{ secrets.STRAVA_CLIENT_SECRET }}
          STRAVA_REFRESH_TOKEN: ${{ secrets.STRAVA_REFRESH_TOKEN }}
          STRAVA_VERIFY_TOKEN: ${{ secrets.STRAVA_VERIFY_TOKEN }}
          GITHUB_TOKEN: ${{ github.token }}
        run: python strava_tweet.py
EOF

print_success "创建: .github-actions-config.example.yml"

# 创建 README 快速引用
cat > QUICK_REFERENCE.md << 'EOF'
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
EOF

print_success "创建: QUICK_REFERENCE.md"

# 创建 .gitignore 示例
cat > .gitignore.example << 'EOF'
# 环境变量
.env
.env.local
.env.strava
.env.cloudflare

# 配置文件
.webhook_config.json

# 依赖
__pycache__/
*.py[cod]
*$py.class

# 虚拟环境
venv/
env/
ENV/

# IDE
.vscode/
.idea/
*.swp
*.swo

# 操作系统
.DS_Store
Thumbs.db

# 日志
*.log

# 临时文件
*.tmp
*.temp
EOF

print_success "创建: .gitignore.example"

echo ""
echo "✅ 配置文件创建完成！"
echo ""
echo "请根据以下文件配置系统："
echo "  1. cloudflare-worker-config.example.env"
echo "  2. strava-oauth-config.example.env"
echo "  3. QUICK_REFERENCE.md"
echo ""
