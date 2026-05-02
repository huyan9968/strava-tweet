
#!/bin/bash
#
# 🔍 跑步日记系统 - 验证脚本
# 验证系统配置和组件状态
#

echo "═══════════════════════════════════════"
echo "  🏃 跑步日记系统 - 配置验证"
echo "═══════════════════════════════════════"
echo ""

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

PASS=0
FAIL=0
WARN=0

# 检查函数
check() {
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ $1${NC}"
        PASS=$((PASS+1))
    else
        echo -e "${RED}❌ $1${NC}"
        FAIL=$((FAIL+1))
    fi
}

warn() {
    echo -e "${YELLOW}⚠️  $1${NC}"
    WARN=$((WARN+1))
}

info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

echo "--- 核心文件检查 ---"
[ -f "strava_tweet.py" ] && check "strava_tweet.py 存在" || check "strava_tweet.py 不存在"
[ -f "build_site.py" ] && check "build_site.py 存在" || check "build_site.py 不存在"
[ -f "cloudflare-worker/worker.js" ] && check "worker.js 存在" || check "worker.js 不存在"
[ -f ".github/workflows/strava_tweet.yml" ] && check "strava_tweet.yml 存在" || check "strava_tweet.yml 不存在"
[ -f ".github/workflows/build_site.yml" ] && check "build_site.yml 存在" || check "build_site.yml 不存在"
[ -f "index.html" ] && check "index.html 存在" || check "index.html 不存在"

echo ""
echo "--- 目录检查 ---"
[ -d "runs" ] && check "runs/ 目录存在" || check "runs/ 目录不存在"
[ -d "data" ] && check "data/ 目录存在" || check "data/ 目录不存在"
[ -d "maps" ] && check "maps/ 目录存在" || check "maps/ 目录不存在"

echo ""
echo "--- 文档检查 ---"
[ -f "跑步日记系统-README.md" ] && check "README.md 存在" || check "README.md 不存在"
[ -f "配置指南.md" ] && check "配置指南.md 存在" || check "配置指南.md 不存在"
[ -f "CONFIG_STATUS.md" ] && check "CONFIG_STATUS.md 存在" || check "CONFIG_STATUS.md 不存在"

echo ""
echo "--- 权限检查 ---"
[ -x "strava_tweet.py" ] && info "strava_tweet.py 可执行" || warn "strava_tweet.py 不可执行"
[ -x "build_site.py" ] && info "build_site.py 可执行" || warn "build_site.py 不可执行"
[ -x "build_site.py" ] && info "build_site.py 可执行" || warn "build_site.py 不可执行"

echo ""
echo "--- 语法检查 ---"
python3 -m py_compile strava_tweet.py 2>/dev/null && check "strava_tweet.py 语法正确" || check "strava_tweet.py 语法错误"
python3 -m py_compile build_site.py 2>/dev/null && check "build_site.py 语法正确" || check "build_site.py 语法错误"

echo ""
echo "--- 功能测试 ---"
python3 build_site.py > /tmp/test_output.txt 2>&1
if grep -q "✅ 网站已生成" /tmp/test_output.txt; then
    check "网站生成器工作正常"
else
    warn "网站生成器测试失败"
fi
rm -f /tmp/test_output.txt

echo ""
echo "--- GitHub Secrets 检查 ---"
if gh secret list 2>/dev/null | grep -q "STRAVA_CLIENT_ID"; then
    check "STRAVA_CLIENT_SECRET 已配置"
else
    warn "STRAVA_CLIENT_ID 未配置"
fi

if gh secret list 2>/dev/null | grep -q "STRAVA_CLIENT_SECRET"; then
    check "STRAVA_CLIENT_SECRET 已配置"
else
    warn "STRAVA_CLIENT_SECRET 未配置"
fi

if gh secret list 2>/dev/null | grep -q "STRAVA_REFRESH_TOKEN"; then
    check "STRAVA_REFRESH_TOKEN 已配置"
else
    warn "STRAVA_REFRESH_TOKEN 未配置"
fi

if gh secret list 2>/dev/null | grep -q "STRAVA_VERIFY_TOKEN"; then
    check "STRAVA_VERIFY_TOKEN 已配置"
else
    warn "STRAVA_VERIFY_TOKEN 未配置"
fi

echo ""
echo "--- GitHub Pages 检查 ---"
if curl -s -o /dev/null -w "%{http_code}" https://huyan9968.github.io/strava-tweet/ | grep -q "200"; then
    check "GitHub Pages 可访问"
else
    warn "GitHub Pages 可能不可访问"
fi

echo ""
echo "═══════════════════════════════════════"
echo "  验证结果"
echo "═══════════════════════════════════════"
echo -e "${GREEN}通过: $PASS${NC}"
echo -e "${YELLOW}警告: $WARN${NC}"
echo -e "${RED}失败: $FAIL${NC}"
echo "═══════════════════════════════════════"
echo ""

TOTAL=$((PASS + WARN + FAIL))
if [ $TOTAL -gt 0 ]; then
    PERCENT=$((PASS * 100 / TOTAL))
    echo "完成度: ${PERCENT}%"

    if [ $PERCENT -ge 95 ]; then
        echo -e "${GREEN}状态: 🟢 生产就绪${NC}"
    elif [ $PERCENT -ge 80 ]; then
        echo -e "${YELLOW}状态: 🟡 基本就绪${NC}"
    else
        echo -e "${RED}状态: 🔴 需要配置${NC}"
    fi
fi

echo ""
echo "--- 下一步建议 ---"
if [ $WARN -gt 0 ]; then
    echo "⚠️  请查看警告项并进行配置"
    echo "   参考文档: 配置指南.md"
fi
if [ $FAIL -eq 0 ] && [ $WARN -le 2 ]; then
    echo "✅ 系统已准备就绪！"
    echo "   下一步: 部署 Cloudflare Worker"
    echo "   参考: AUTO_SETUP.md"
fi

echo ""
echo "═══════════════════════════════════════"
