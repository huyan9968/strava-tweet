
#!/bin/bash
#
# 🚀 跑步日记系统 - 自动化配置脚本
# ======================================
#
# 本脚本帮助您完成系统的配置流程
# 包括：GitHub Secrets 设置、Cloudflare Worker 部署等
#
# 使用方法：
#   bash config.sh
#

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印标题
print_header() {
    echo -e "\n${BLUE}══════════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}  🏃 跑步日记系统 - 配置向导${NC}"
    echo -e "${BLUE}══════════════════════════════════════════════════════════${NC}\n"
}

# 打印成功信息
print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

# 打印警告信息
print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

# 打印错误信息
print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# 打印信息
print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# 检查先决条件
check_prerequisites() {
    print_header
    print_info "检查先决条件..."

    # 检查 GitHub CLI
    if command -v gh &> /dev/null; then
        print_success "GitHub CLI (gh) 已安装"
    else
        print_warning "GitHub CLI 未安装"
        print_info "安装方法: brew install gh"
    fi

    # 检查 git
    if command -v git &> /dev/null; then
        print_success "Git 已安装"
    else
        print_error "Git 未安装"
        exit 1
    fi

    # 检查 python3
    if command -v python3 &> /dev/null; then
        print_success "Python3 已安装 ($(python3 --version))"
    else
        print_error "Python3 未安装"
        exit 1
    fi

    echo ""
}

# 步骤 1: 配置 GitHub Secrets
configure_github_secrets() {
    print_header
    print_info "步骤 1: 配置 GitHub Secrets"
    echo ""

    print_warning "⚠️  请准备以下信息："
    echo "  1. STRAVA_CLIENT_ID - Strava App Client ID"
    echo "  2. STRAVA_CLIENT_SECRET - Strava App Client Secret"
    echo "  3. STRAVA_REFRESH_TOKEN - Strava OAuth Refresh Token"
    echo "  4. STRAVA_VERIFY_TOKEN - 自定义验证字符串"
    echo "  5. GITHUB_TOKEN - GitHub Personal Access Token"
    echo ""

    read -p "是否已准备好这些信息？(y/n): " ready
    if [[ ! "$ready" =~ ^[Yy]$ ]]; then
        print_warning "请先准备这些信息，然后重新运行脚本"
        return 1
    fi

    echo ""
    print_info "请输入以下信息："

    read -p "STRAVA_CLIENT_ID: " STRAVA_CLIENT_ID
    read -p "STRAVA_CLIENT_SECRET: " STRAVA_CLIENT_SECRET
    read -p "STRAVA_REFRESH_TOKEN: " STRAVA_REFRESH_TOKEN
    read -p "STRAVA_VERIFY_TOKEN [建议使用 my-strava-webhook-2024]: " STRAVA_VERIFY_TOKEN
    read -p "GITHUB_TOKEN: " GITHUB_TOKEN

    # 设置默认值
    STRAVA_VERIFY_TOKEN=${STRAVA_VERIFY_TOKEN:-my-strava-webhook-2024}
    GITHUB_REPOSITORY="huyan9968/strava-tweet"

    echo ""
    print_info "正在配置 GitHub Secrets..."

    # 检查是否在 git 仓库中
    if ! git rev-parse --git-dir > /dev/null 2>&1; then
        print_error "当前目录不是 git 仓库"
        return 1
    fi

    # 使用 GitHub CLI 设置 secrets
    if command -v gh &> /dev/null; then
        print_info "使用 GitHub CLI 设置 secrets..."

        gh secret set STRAVA_CLIENT_ID --body "$STRAVA_CLIENT_ID" 2>/dev/null || true
        gh secret set STRAVA_CLIENT_SECRET --body "$STRAVA_CLIENT_SECRET" 2>/dev/null || true
        gh secret set STRAVA_REFRESH_TOKEN --body "$STRAVA_REFRESH_TOKEN" 2>/dev/null || true
        gh secret set STRAVA_VERIFY_TOKEN --body "$STRAVA_VERIFY_TOKEN" 2>/dev/null || true
        gh secret set GITHUB_TOKEN --body "$GITHUB_TOKEN" 2>/dev/null || true
        gh secret set GITHUB_REPOSITORY --body "$GITHUB_REPOSITORY" 2>/dev/null || true

        print_success "GitHub Secrets 已配置"
    else
        print_warning "GitHub CLI 未安装，请手动配置 Secrets"
        print_info "访问: https://github.com/huyan9968/strava-tweet/settings/secrets/actions"
        echo ""
        echo "需要添加的 Secrets："
        echo "  STRAVA_CLIENT_ID=$STRAVA_CLIENT_ID"
        echo "  STRAVA_CLIENT_SECRET=$STRAVA_CLIENT_SECRET"
        echo "  STRAVA_REFRESH_TOKEN=$STRAVA_REFRESH_TOKEN"
        echo "  STRAVA_VERIFY_TOKEN=$STRAVA_VERIFY_TOKEN"
        echo "  GITHUB_TOKEN=$GITHUB_TOKEN"
        echo "  GITHUB_REPOSITORY=$GITHUB_REPOSITORY"
    fi

    # 保存到本地环境文件
    cat > .env.local << EOF
# 本地环境变量文件（仅用于参考）
STRAVA_CLIENT_ID=$STRAVA_CLIENT_ID
STRAVA_CLIENT_SECRET=$STRAVA_CLIENT_SECRET
STRAVA_REFRESH_TOKEN=$STRAVA_REFRESH_TOKEN
STRAVA_VERIFY_TOKEN=$STRAVA_VERIFY_TOKEN
GITHUB_TOKEN=$GITHUB_TOKEN
GITHUB_REPOSITORY=$GITHUB_REPOSITORY
EOF

    print_success "环境变量已保存到 .env.local（仅用于参考）"

    echo ""
    return 0
}

# 步骤 2: 生成 OAuth 配置脚本
generate_oauth_script() {
    print_header
    print_info "步骤 2: 生成 OAuth 认证脚本"
    echo ""

    cat > get_oauth_token.py << 'PYTHON_EOF'
#!/usr/bin/env python3
"""
Strava OAuth Token 获取脚本
用于获取 OAuth Refresh Token
"""

import webbrowser
import sys

def main():
    # 从命令行参数或输入获取 Client ID
    if len(sys.argv) > 1:
        client_id = sys.argv[1]
    else:
        client_id = input("请输入 Strava Client ID: ").strip()

    if not client_id:
        print("❌ 错误：Client ID 不能为空")
        sys.exit(1)

    print(f"\nℹ️  Strava Client ID: {client_id}")
    print("ℹ️  请在浏览器中完成授权\n")

    # 构建 OAuth URL
    oauth_url = (
        f"https://www.strava.com/oauth/authorize"
        f"?client_id={client_id}"
        f"&response_type=code"
        f"&redirect_uri=https://localhost"
        f"&approval_prompt=force"
        f"&scope=read_all,activity:read_all"
    )

    print(f"授权链接: {oauth_url}\n")

    # 询问是否打开浏览器
    try:
        open_browser = input("是否要自动打开浏览器？(y/n): ").lower().strip()
        if open_browser == 'y':
            webbrowser.open(oauth_url)
            print("✅ 浏览器已打开，请完成授权\n")
    except:
        pass

    # 获取授权码
    auth_code = input("请输入授权码 (code 参数): ").strip()

    if not auth_code:
        print("❌ 错误：授权码不能为空")
        sys.exit(1)

    # 获取 Client Secret
    client_secret = input("请输入 Strava Client Secret: ").strip()

    if not client_secret:
        print("❌ 错误：Client Secret 不能为空")
        sys.exit(1)

    # 请求 Refresh Token
    print("\nℹ️  正在请求 Refresh Token...")

    import requests

    try:
        response = requests.post('https://www.strava.com/oauth/token', data={
            'client_id': client_id,
            'client_secret': client_secret,
            'code': auth_code,
            'grant_type': 'authorization_code'
        })

        if response.status_code == 200:
            token_data = response.json()

            print("\n" + "="*60)
            print("✅ 成功获取 OAuth Token！")
            print("="*60)
            print(f"\n🔑 Refresh Token: {token_data['refresh_token']}")
            print(f"📅 有效期至: {token_data.get('expires_at', 'N/A')}")
            print(f"👤 运动员: {token_data.get('athlete', {}).get('firstname', 'N/A')}")

            print("\n" + "-"*60)
            print("请将以下信息添加到 GitHub Secrets：")
            print("-"*60)
            print(f"  STRAVA_CLIENT_ID={client_id}")
            print(f"  STRAVA_CLIENT_SECRET={client_secret}")
            print(f"  STRAVA_REFRESH_TOKEN={token_data['refresh_token']}")
            print(f"  STRAVA_VERIFY_TOKEN=my-strava-webhook-2024")
            print("  GITHUB_TOKEN=<your-github-token>")

            # 保存到文件
            with open('.env.strava', 'w') as f:
                f.write(f"# Strava OAuth Token\n")
                f.write(f"STRAVA_CLIENT_ID={client_id}\n")
                f.write(f"STRAVA_CLIENT_SECRET={client_secret}\n")
                f.write(f"STRAVA_REFRESH_TOKEN={token_data['refresh_token']}\n")

            print("\n✅ Token 已保存到 .env.strava 文件")
            print("⚠️  请妥善保存，不要分享给他人！")

        else:
            print(f"❌ 错误：{response.status_code}")
            print(response.text)
            sys.exit(1)

    except Exception as e:
        print(f"❌ 请求失败: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
PYTHON_EOF

    chmod +x get_oauth_token.py
    print_success "OAuth 脚本已生成: get_oauth_token.py"
    echo ""
    print_info "使用方法:"
    echo "  python3 get_oauth_token.py [CLIENT_ID]"
    echo ""
}

# 步骤 3: 部署 Cloudflare Worker
deploy_cloudflare_worker() {
    print_header
    print_info "步骤 3: 部署 Cloudflare Worker"
    echo ""

    print_warning "⚠️  需要 Cloudflare 账户"
    echo ""
    print_info "请执行以下操作："
    echo ""
    echo "1. 访问: https://dash.cloudflare.com/"
    echo "2. 登录或创建账户"
    echo "3. 进入 'Workers & Pages'"
    echo "4. 点击 'Create Application' → 'Worker'"
    echo "5. 点击 'Create'"
    echo "6. 复制 worker.js 代码到编辑器中"
    echo "7. 点击 'Save and Deploy'"
    echo ""

    # 显示 worker.js 文件内容
    if [[ -f "cloudflare-worker/worker.js" ]]; then
        print_info "worker.js 文件路径: cloudflare-worker/worker.js"
        echo ""
        print_warning "请确保配置以下环境变量："
        echo "  - STRAVA_VERIFY_TOKEN=my-strava-webhook-2024"
        echo "  - GITHUB_TOKEN=<your-github-token>"
        echo ""
    else
        print_error "未找到 worker.js 文件"
        return 1
    fi

    read -p "是否已部署 Worker？ (y/n): " deployed
    if [[ "$deployed" =~ ^[Yy]$ ]]; then
        read -p "请输入 Worker URL: " WORKER_URL

        if [[ -n "$WORKER_URL" ]]; then
            # 保存 Worker URL
            echo "WORKER_URL=$WORKER_URL" >> .env.local
            print_success "Worker URL 已保存"

            echo ""
            print_info "接下来需要在 Strava 注册 Webhook："
            echo ""
            echo "使用以下命令注册："
            echo ""
            echo "curl -X POST https://www.strava.com/api/v3/push_subscriptions \\"
            echo "  -d client_id=YOUR_CLIENT_ID \\"
            echo "  -d client_secret=YOUR_CLIENT_SECRET \\"
            echo "  -d 'callback_url=${WORKER_URL}' \\"
            echo "  -d 'verify_token=my-strava-webhook-2024'"
            echo ""
        fi
    fi

    echo ""
    return 0
}

# 步骤 4: 测试工作流
test_workflow() {
    print_header
    print_info "步骤 4: 测试工作流"
    echo ""

    print_info "测试本地 Python 脚本..."

    # 创建设置目录
    mkdir -p runs data maps

    # 测试 build_site.py
    print_info "测试网站生成器..."
    if python3 build_site.py > /dev/null 2>&1; then
        print_success "网站生成器工作正常"

        if [[ -f "index.html" ]]; then
            print_success "已生成 index.html"
            echo ""
            print_info "网站预览地址: file://$(pwd)/index.html"
        fi
    else
        print_warning "网站生成器测试失败"
    fi

    echo ""
    print_info "测试 GitHub Actions..."
    print_warning "⚠️  请手动测试："
    echo "  1. 访问: https://github.com/huyan9968/strava-tweet/actions"
    echo "  2. 运行 'Strava 跑步记录' workflow"
    echo "  3. 检查是否成功"
    echo ""
}

# 主菜单
main_menu() {
    print_header

    echo "请选择要执行的操作："
    echo ""
    echo "  1) 配置 GitHub Secrets"
    echo "  2) 生成 OAuth 认证脚本"
    echo "  3) 部署 Cloudflare Worker"
    echo "  4) 运行完整配置流程"
    echo "  5) 测试工作流"
    echo "  6) 显示配置状态"
    echo "  0) 退出"
    echo ""

    read -p "请输入选项 [0-6]: " choice

    case $choice in
        1)
            configure_github_secrets
            ;;
        2)
            generate_oauth_script
            ;;
        3)
            deploy_cloudflare_worker
            ;;
        4)
            check_prerequisites
            configure_github_secrets
            generate_oauth_script
            deploy_cloudflare_worker
            test_workflow
            ;;
        5)
            test_workflow
            ;;
        6)
            show_status
            ;;
        0)
            print_info "再见！"
            exit 0
            ;;
        *)
            print_error "无效的选项"
            ;;
    esac

    echo ""
    read -p "按 Enter 键继续..."
    main_menu
}

# 显示配置状态
show_status() {
    print_header
    print_info "配置状态"
    echo ""

    echo "📁 文件结构："
    ls -la | grep -E "^-|^d" | head -20
    echo ""

    echo "🔧 GitHub Actions："
    ls -la .github/workflows/ 2>/dev/null || echo "  未找到 workflow 文件"
    echo ""

    echo "🌐 GitHub Pages："
    if [[ -f "index.html" ]]; then
        print_success "index.html 已生成"
    else
        print_warning "index.html 未生成"
    fi
    echo ""

    echo "📄 文档："
    [[ -f "配置指南.md" ]] && print_success "配置指南.md"
    [[ -f "跑步日记系统-README.md" ]] && print_success "跑步日记系统-README.md"
    echo ""
}

# 启动脚本
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main_menu
fi
