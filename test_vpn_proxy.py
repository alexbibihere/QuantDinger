"""
测试Docker容器内的VPN代理连接
"""
import docker
import time

def test_proxy_in_container():
    """测试容器内代理连接"""

    print("=" * 70)
    print("测试Docker容器内的VPN代理")
    print("=" * 70)

    client = docker.from_env()

    # 获取后端容器
    try:
        container = client.containers.get("quantdinger-backend")
        print(f"\n✅ 找到容器: {container.name}")
    except Exception as e:
        print(f"\n❌ 容器不存在: {e}")
        return

    # 测试1: 检查环境变量
    print("\n" + "-" * 70)
    print("测试1: 检查代理环境变量")
    print("-" * 70)

    exit_code, output = container.exec_run("env | grep -i proxy")

    if exit_code == 0:
        print("✅ 代理环境变量已设置:")
        print(output.decode('utf-8'))
    else:
        print("❌ 未找到代理环境变量")

    # 测试2: 检查host.docker.internal
    print("\n" + "-" * 70)
    print("测试2: 测试host.docker.internal解析")
    print("-" * 70)

    exit_code, output = container.exec_run("ping -c 2 host.docker.internal")

    if exit_code == 0:
        print("✅ host.docker.internal可以解析")
    else:
        print("⚠️  host.docker.internal无法ping通（正常，可能禁用了ICMP）")

    # 测试3: 测试代理端口连接
    print("\n" + "-" * 70)
    print("测试3: 测试代理端口7890连接")
    print("-" * 70)

    exit_code, output = container.exec_run(
        "nc -zv host.docker.internal 7890 -w 3",
        workdir="/tmp"
    )

    if exit_code == 0:
        print("✅ 代理端口7890可以连接")
    else:
        print("❌ 代理端口7890无法连接")
        print("请确认:")
        print("  1. VPN软件正在运行")
        print("  2. 代理端口是7890")
        print("  3. 允许局域网连接（如果需要）")

    # 测试4: 通过代理访问Google
    print("\n" + "-" * 70)
    print("测试4: 通过代理访问Google")
    print("-" * 70)

    exit_code, output = container.exec_run(
        "curl -x socks5h://host.docker.internal:7890 -I https://www.google.com --connect-timeout 10",
        workdir="/tmp"
    )

    if exit_code == 0:
        print("✅ 可以通过代理访问Google")
        print("输出:", output.decode('utf-8')[:200])
    else:
        print("❌ 无法通过代理访问Google")
        print("错误:", output.decode('utf-8'))

    # 测试5: 通过代理访问TradingView
    print("\n" + "-" * 70)
    print("测试5: 通过代理访问TradingView")
    print("-" * 70)

    exit_code, output = container.exec_run(
        "curl -x socks5h://host.docker.internal:7890 -I https://scanner.tradingview.com --connect-timeout 10",
        workdir="/tmp"
    )

    if exit_code == 0:
        print("✅ 可以通过代理访问TradingView")
        print("输出:", output.decode('utf-8')[:200])
    else:
        print("❌ 无法通过代理访问TradingView")
        print("错误:", output.decode('utf-8'))

    # 测试6: 通过代理访问Binance
    print("\n" + "-" * 70)
    print("测试6: 通过代理访问Binance API")
    print("-" * 70)

    exit_code, output = container.exec_run(
        "curl -x socks5h://host.docker.internal:7890 https://api.binance.com/api/v3/ping --connect-timeout 10",
        workdir="/tmp"
    )

    if exit_code == 0:
        print("✅ 可以通过代理访问Binance API")
        print("输出:", output.decode('utf-8'))
    else:
        print("❌ 无法通过代理访问Binance API")
        print("错误:", output.decode('utf-8'))

    print("\n" + "=" * 70)
    print("测试完成")
    print("=" * 70)

if __name__ == "__main__":
    try:
        test_proxy_in_container()
    except ImportError:
        print("请安装docker库: pip install docker")
    except Exception as e:
        print(f"错误: {e}")
