
#!/usr/bin/env python3
#
# 🏃 Strava Webhook 注册脚本
# 用于注册 Strava Webhook 到 Cloudflare Worker
#

import requests
import json
import sys
import os

def print_header():
    print("\n" + "="*70)
    print("  🏃 Strava Webhook 注册脚本")
    print("="*70 + "\n")

def print_success(msg):
    print(f"✅ {msg}")

def print_warning(msg):
    print(f"⚠️  {msg}")

def print_error(msg):
    print(f"❌ {msg}")

def print_info(msg):
    print(f"ℹ️  {msg}")

def register_webhook(client_id, client_secret, callback_url, verify_token):
    """注册 Strava Webhook"""

    url = "https://www.strava.com/api/v3/push_subscriptions"

    data = {
        'client_id': client_id,
        'client_secret': client_secret,
        'callback_url': callback_url,
        'verify_token': verify_token
    }

    print_info(f"正在注册 Webhook...")
    print_info(f"  Callback URL: {callback_url}")
    print_info(f"  Verify Token: {verify_token}")
    print()

    try:
        response = requests.post(url, data=data)

        if response.status_code == 200:
            result = response.json()
            print_success("Webhook 注册成功！")
            print()
            print("响应数据：")
            print("-" * 70)
            print(json.dumps(result, indent=2))
            print("-" * 70)
            print()

            # 保存配置
            config = {
                'client_id': client_id,
                'callback_url': callback_url,
                'verify_token': verify_token,
                'webhook_id': result.get('id'),
                'status': result.get('status', 'active')
            }

            with open('.webhook_config.json', 'w') as f:
                json.dump(config, f, indent=2)

            print_success("Webhook 配置已保存到 .webhook_config.json")
            return True

        elif response.status_code == 409:
            result = response.json()
            print_warning("Webhook 已存在")
            print_info(f"消息: {result.get('message', '')}")

            # 尝试获取现有 webhook
            return get_existing_webhooks(client_id, client_secret)

        else:
            print_error(f"注册失败: {response.status_code}")
            print_error(f"响应: {response.text}")
            return False

    except Exception as e:
        print_error(f"请求失败: {e}")
        return False

def get_existing_webhooks(client_id, client_secret):
    """获取现有的 webhook 列表"""

    url = "https://www.strava.com/api/v3/athletes/webhooks"

    try:
        # 注意：获取 webhook 列表需要特殊权限
        # 这里只是尝试，实际可能需要不同的方法
        print_info("尝试获取现有 webhook 列表...")
        response = requests.get(url, auth=(client_id, client_secret))

        if response.status_code == 200:
            webhooks = response.json()
            print_success(f"找到 {len(webhooks)} 个 webhook")

            for wh in webhooks:
                print(f"  - ID: {wh.get('id')}")
                print(f"    URL: {wh.get('callback_url')}")
                print(f"    Status: {wh.get('status')}")
                print()

            return True
        else:
            print_warning(f"无法获取 webhook 列表: {response.status_code}")
            return False

    except Exception as e:
        print_warning(f"获取 webhook 列表失败: {e}")
        return False

def interactive_mode():
    """交互式模式"""

    print_header()

    print_info("请提供以下信息：")
    print()

    client_id = input("Strava Client ID: ").strip()
    client_secret = input("Strava Client Secret: ").strip()
    callback_url = input("Callback URL (Worker URL) [默认: https://strava-webhook-demo.workers.dev/]: ").strip()
    verify_token = input("Verify Token [默认: my-strava-webhook-2024]: ").strip()

    # 设置默认值
    if not callback_url:
        callback_url = "https://strava-webhook-demo.workers.dev/"

    if not verify_token:
        verify_token = "my-strava-webhook-2024"

    print()
    print("="*70)
    print("确认信息：")
    print(f"  Client ID:     {client_id}")
    print(f"  Client Secret: {'*' * len(client_secret)}")
    print(f"  Callback URL:  {callback_url}")
    print(f"  Verify Token:  {verify_token}")
    print("="*70)
    print()

    confirm = input("确认注册？ (y/n): ").strip().lower()

    if confirm == 'y':
        register_webhook(client_id, client_secret, callback_url, verify_token)
    else:
        print_info("已取消")

def command_line_mode():
    """命令行模式"""

    if len(sys.argv) < 5:
        print("使用方法:")
        print("  python3 register_strava_webhook.py CLIENT_ID CLIENT_SECRET CALLBACK_URL VERIFY_TOKEN")
        print()
        print("示例:")
        print("  python3 register_strava_webhook.py 12345 abcde https://worker.workers.dev/ my-token")
        print()
        return False

    client_id = sys.argv[1]
    client_secret = sys.argv[2]
    callback_url = sys.argv[3]
    verify_token = sys.argv[4]

    return register_webhook(client_id, client_secret, callback_url, verify_token)

def main():
    """主函数"""

    # 检查依赖
    try:
        import requests
    except ImportError:
        print_error("缺少 requests 库")
        print_info("安装方法: pip install requests")
        sys.exit(1)

    # 选择模式
    if len(sys.argv) > 1:
        # 命令行模式
        success = command_line_mode()
    else:
        # 交互模式
        success = interactive_mode()

    # 显示后续步骤
    print()
    print("="*70)
    print("后续步骤：")
    print("="*70)
    print()
    print("1. 在 Strava 设置中验证 Webhook 状态")
    print("   访问: https://www.strava.com/settings/api")
    print()
    print("2. 测试 Webhook")
    print("   在 Strava 记录一次跑步")
    print("   检查 GitHub Actions 是否触发")
    print()
    print("3. 查看 GitHub Issues")
    print("   检查是否创建了跑步记录")
    print()

    if success:
        print_success("Webhook 注册完成！")
    else:
        print_warning("Webhook 注册未完成，请检查错误信息")

    print()

if __name__ == '__main__':
    main()
