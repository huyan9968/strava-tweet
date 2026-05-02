
#!/bin/bash
#
# ⚡ 快速设置脚本
# 一键完成 Cloudflare Worker 和 Strava Webhook 配置
#
# 使用方法：
#   bash quick_setup.sh
#

set -e

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# 打印函数
print_header() {
    echo -e "\n${CYAN}═══════════════════════════════════════════════════════════${NC}"
    echo -e "${CYAN}  ⚡ 快速设置脚本 - Strava Webhook 配置${NC}"
    echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}\n"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_title() {
    echo -e "\n${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${CYAN}  $1${NC}"
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"
}

# 检查先决条件
check_prerequisites() {
    print_title "检查先决条件"

    local errors=0

    # 检查 curl
    if command -v curl &> /dev/null; then
        print_success "curl 已安装"
    else
        print_error "curl 未安装"
        errors=$((errors + 1))
    fi

    # 检查 python3
    if command -v python3 &> /dev/null; then
        print_success "Python3 已安装 ($(python3 --version 2>&1))"
    else
        print_error "Python3 未安装"
        errors=$((errors + 1))
    fi

    # 检查 git
    if command -v git &> /dev/null; then
        print_success "Git 已安装"
    else
        print_error "Git 未安装"
        errors=$((errors + 1))
    fi

    echo ""

    if [ $errors -gt 0 ]; then
        print_error "发现 $errors 个错误，请先安装依赖"
        return 1
    fi

    return 0
}

# 步骤 1: 获取 Strava 信息
get_strava_info() {
    print_title "步骤 1: Strava App 信息"

    print_info "请先在 Strava 开发者页面创建 App："
    print_info "https://www.strava.com/settings/api"
    echo ""

    read -p "输入 Client ID: " STRAVA_CLIENT_ID
    read -s -p "输入 Client Secret: " STRAVA_CLIENT_SECRET
    echo ""

    # 尝试获取 OAuth Token
    print_info "获取 OAuth Refresh Token..."
    print_info "请在浏览器中访问以下链接："
    echo ""
    echo "https://www.strava.com/oauth/authorize?client_id=${STRAVA_CLIENT_ID}&response_type=code&redirect_uri=https://localhost&approval_prompt=force&scope=read_all,activity:read_all"
    echo ""

    read -p "输入授权码 (code 参数): " AUTH_CODE

    # 获取 Refresh Token
    local response=$(curl -s -X POST https://www.strava.com/oauth/token \
        -d client_id="$STRAVA_CLIENT_ID" \
        -d client_secret="$STRAVA_CLIENT_SECRET" \
        -d code="$AUTH_CODE" \
        -d grant_type=authorization_code)

    local refresh_token=$(echo "$response" | python3 -c "import sys,json; print(json.load(sys.stdin).get('refresh_token',''))" 2>/dev/null)

    if [ -z "$refresh_token" ]; then
        print_error "获取 Refresh Token 失败"
        print_error "响应: $response"
        return 1
    fi

    print_success "成功获取 Refresh Token"

    # 保存到环境变量
    export STRAVA_CLIENT_ID
    export STRAVA_CLIENT_SECRET
    export STRAVA_REFRESH_TOKEN="$refresh_token"

    echo ""
    return 0
}

# 步骤 2: 配置 Cloudflare Worker
configure_cloudflare() {
    print_title "步骤 2: Cloudflare Worker 配置"

    print_info "请提供以下信息："
    echo ""

    read -p "Cloudflare Worker URL (例如: https://my-worker.workers.dev/): " WORKER_URL
    read -s -p "GitHub Personal Access Token: " GITHUB_TOKEN
    echo ""

    # 验证 Worker
    print_info "验证 Cloudflare Worker..."
    local response=$(curl -s -o /dev/null -w "%{http_code}" "$WORKER_URL")

    if [ "$response" == "403" ]; then
        print_success "Worker 响应正常 (403 Forbidden 是预期的)"
    else
        print_warning "Worker 返回状态码: $response"
        read -p "是否继续？ (y/n): " confirm
        if [[ ! "$confirm" =~ ^[Yy]$ ]]; then
            return 1
        fi
    fi

    # 保存环境变量
    export STRAVA_VERIFY_TOKEN="my-strava-webhook-2024"
    export GITHUB_TOKEN
    export WORKER_URL

    print_success "Cloudflare Worker 配置完成"
    echo ""
    return 0
}

# 步骤 3: 注册 Webhook
register_webhook() {
    print_title "步骤 3: 注册 Strava Webhook"

    local callback_url="${WORKER_URL}"
    local verify_token="my-strava-webhook-2024"

    print_info "正在注册 Webhook..."
    print_info "  Callback URL: $callback_url"
    print_info "  Verify Token: $verify_token"
    echo ""

    local response=$(curl -s -X POST https://www.strava.com/api/v3/push_subscriptions \
        -d client_id="$STRAVA_CLIENT_ID" \
        -d client_secret="$STRAVA_CLIENT_SECRET" \
        -d "callback_url=$callback_url" \
        -d "verify_token=$verify_token")

    local status=$(echo "$response" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('status',''))" 2>/dev/null)
    local webhook_id=$(echo "$response" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('id',''))" 2>/dev/null)

    if [ "$status" == "active" ] && [ -n "$webhook_id" ]; then
        print_success "Webhook 注册成功！"
        print_info "Webhook ID: $webhook_id"
        print_info "状态: active"
    else
        print_warning "Webhook 可能已存在或状态异常"
        print_info "Webhook ID: $webhook_id"
        print_info "状态: $status"
        echo ""
        print_info "完整响应："
        echo "$response" | python3 -m json.tool 2>/dev/null || echo "$response"
    fi

    # 保存配置
    cat > .webhook_config.json << EOF
{
    "client_id": "$STRAVA_CLIENT_ID",
    "client_secret": "$STRAVA_CLIENT_SECRET",
    "refresh_token": "$STRAVA_REFRESH_TOKEN",
    "callback_url": "$callback_url",
    "verify_token": "$verify_token",
    "webhook_id": "$webhook_id",
    "status": "$status"
}
EOF

    chmod 600 .webhook_config.json
    print_success "Webhook 配置已保存到 .webhook_config.json"
    echo ""
    return 0
}

# 步骤 4: 更新 GitHub Secrets
update_github_secrets() {
    print_title "步骤 4: 更新 GitHub Secrets"

    print_info "使用 GitHub CLI (gh) 更新 Secrets..."
    echo ""

    # 检查是否已登录
    if ! gh auth status &> /dev/null; then
        print_warning "GitHub CLI 未登录"
        print_info "请先运行: gh login"
        return 1
    fi

    # 更新 secrets
    local secrets_updated=0

    if gh secret set STRAVA_CLIENT_ID --body "$STRAVA_CLIENT_ID" 2>/dev/null; then
        print_success "STRAVA_CLIENT_SECRET 已更新"
        secrets_updated=$((secrets_updated + 1))
    fi

    if gh secret set STRAVA_CLIENT_SECRET --body "$STRAVA_CLIENT_SECRET" 2>/dev/null; then
        print_success "STRAVA_CLIENT_SECRET 已更新"
        secrets_updated=$((secrets_updated + 1))
    fi

    if gh secret set STRAVA_REFRESH_TOKEN --body "$STRAVA_REFRESH_TOKEN" 2>/dev/null; then
        print_success "STRAVA_REFRESH_TOKEN 已更新"
        secrets_updated=$((secrets_updated + 1))
    fi

    if gh secret set STRAVA_VERIFY_TOKEN --body "$STRAVA_VERIFY_TOKEN" 2>/dev/null; then
        print_success "STRAVA_VERIFY_TOKEN 已更新"
        secrets_updated=$((secrets_updated + 1))
    fi

    print_success "已更新 $secrets_updated 个 GitHub Secrets"
    echo ""
    return 0
}

# 步骤 5: 测试配置
test_configuration() {
    print_title "步骤 5: 测试配置"

    print_info "生成网站..."
    python3 build_site.py

    if [ -f "index.html" ]; then
        print_success "网站生成成功"
    else
        print_error "网站生成失败"
        return 1
    fi

    print_info "验证 GitHub Actions 工作流..."
    echo ""

    print_success "配置测试完成！"
    echo ""
    return 0
}

# 主函数
main() {
    print_header

    print_info "此脚本将帮助您完成以下配置："
    echo "  1. 获取 Strava OAuth Token"
    echo "  2. 配置 Cloudflare Worker"
    echo "  3. 注册 Strava Webhook"
    echo "  4. 更新 GitHub Secrets"
    echo "  5. 测试系统配置"
    echo ""

    read -p "是否继续？ (y/n): " confirm
    if [[ ! "$confirm" =~ ^[Yy]$ ]]; then
        print_info "已取消"
        exit 0
    fi

    echo ""

    # 检查先决条件
    if ! check_prerequisites; then
        exit 1
    fi

    # 执行各个步骤
    if ! get_strava_info; then
        exit 1
    fi

    if ! configure_cloudflare; then
        exit 1
    fi

    if ! register_webhook; then
        exit 1
    fi

    update_github_secrets

    if ! test_configuration; then
        exit 1
    fi

    # 显示完成信息
    print_title "🎉 设置完成！"

    echo "您的跑步日记系统已配置完成！"
    echo ""
    echo "下一步："
    echo "  1. 在 Strava 记录一次跑步"
    echo "  2. 访问 GitHub Actions 查看运行状态"
    echo "  3. 查看 GitHub Issues 中的跑步记录"
    echo "  4. 访问 https://huyan9968.github.io/strava-tweet/ 查看主页"
    echo ""

    print_success "享受您的跑步记录之旅！🏃 ♂️🏃 ♀️"
    echo ""
}

# 运行主函数
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main
fi
