
#!/bin/bash
#
# ☁️ Cloudflare Worker 部署脚本
# 自动部署 Strava Webhook 处理器到 Cloudflare Workers
#
# 使用方法：
#   bash deploy_cloudflare_worker.sh
#

set -e

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

# 打印函数
print_header() {
    echo -e "\n${BLUE}══════════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}  ☁️  Cloudflare Worker 部署脚本${NC}"
    echo -e "${BLUE}══════════════════════════════════════════════════════════${NC}\n"
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

# 主部署函数
deploy_worker() {
    print_header

    print_info "检查 Cloudflare CLI (wrangler)..."

    # 检查是否安装了 wrangler
    if command -v wrangler &> /dev/null; then
        print_success "Wrangler 已安装 ($(wrangler --version))"
    else
        print_warning "Wrangler 未安装"
        print_info "安装方法: npm install -g wrangler"

        read -p "是否要安装 wrangler? (y/n): " install_wrangler
        if [[ "$install_wrangler" =~ ^[Yy]$ ]]; then
            print_info "正在安装 wrangler..."
            npm install -g wrangler
            print_success "Wrangler 安装完成"
        else
            print_warning "请手动安装 wrangler 后重新运行脚本"
            return 1
        fi
    fi

    print_info "检查 Cloudflare 登录状态..."

    # 检查登录状态
    if wrangler whoami &> /dev/null; then
        print_success "已登录 Cloudflare"
    else
        print_warning "未登录 Cloudflare"
        print_info "正在登录..."
        wrangler login
    fi

    print_info "部署 Worker..."

    # 进入 worker 目录
    cd cloudflare-worker || {
        print_error "cloudflare-worker 目录不存在"
        return 1
    }

    # 部署 worker
    if wrangler deploy; then
        print_success "Worker 部署成功！"

        # 获取 Worker URL
        WORKER_URL=$(wrangler tail --format="{{Worker}}" 2>/dev/null | head -1 || echo "")

        echo ""
        print_info "获取 Worker URL..."
        print_info "请访问 https://dash.cloudflare.com/ 查看"
        print_info "或运行: wrangler tail"
        echo ""

        print_success "Worker 已部署到: https://<your-worker-name>.<your-account>.workers.dev"

        cd ..
        return 0
    else
        print_error "Worker 部署失败"
        cd ..
        return 1
    fi
}

# 手动部署说明
manual_deployment() {
    print_header

    print_warning "⚠️  自动部署需要 Wrangler CLI"
    echo ""
    print_info "请按照以下步骤手动部署："
    echo ""
    echo "1. 访问 https://dash.cloudflare.com/"
    echo "2. 登录您的账户"
    echo "3. 点击左侧 'Workers & Pages'"
    echo "4. 点击 'Create Application' → 'Worker'"
    echo "5. 点击 'Create' 按钮"
    echo "6. 删除默认代码，粘贴以下内容："
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    cat cloudflare-worker/worker.js
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "7. 点击 'Save and Deploy' 按钮"
    echo "8. 复制 Worker URL（类似：https://xxx.workers.dev/）"
    echo ""
    print_info "设置环境变量："
    echo "  STRAVA_VERIFY_TOKEN = \"my-strava-webhook-2024\""
    echo "  GITHUB_TOKEN = \"您的 GitHub PAT\""
    echo ""
    print_success "Worker 部署完成！"
}

# 主菜单
main() {
    echo ""
    echo "请选择部署方式："
    echo ""
    echo "  1) 使用 Wrangler CLI 自动部署"
    echo "  2) 手动部署（通过 Web 界面）"
    echo "  3) 查看 Worker 代码"
    echo "  0) 退出"
    echo ""

    read -p "请输入选项 [0-3]: " choice

    case $choice in
        1)
            deploy_worker
            ;;
        2)
            manual_deployment
            ;;
        3)
            echo ""
            echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
            cat cloudflare-worker/worker.js
            echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
            ;;
        0)
            print_info "退出"
            exit 0
            ;;
        *)
            print_error "无效的选项"
            ;;
    esac
}n

# 运行主函数
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main
fi
