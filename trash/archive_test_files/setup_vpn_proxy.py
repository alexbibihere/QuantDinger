"""
VPN代理配置脚本
请根据您的VPN软件填写以下信息
"""

# ========================================
# 请填写您的VPN代理信息
# ========================================

# 常见VPN软件的默认端口：
# Clash: 7890 (HTTP) / 7891 (SOCKS5)
# V2Ray: 10808 (HTTP) / 10809 (SOCKS5)
# Shadowsocks: 1080
# 其他: 请查看您的VPN软件设置

VPN_PORT = 7890  # 修改为您的VPN端口
VPN_HOST = "127.0.0.1"  # 通常不需要修改
VPN_SCHEME = "socks5h"  # 或 "http" / "socks5"

# Docker环境中，如果VPN在宿主机上，使用:
# VPN_HOST = "host.docker.internal"

# ========================================
# 配置说明
# ========================================

"""
方案1: 使用 PROXY_PORT (推荐)
适合: 本地VPN代理 (Clash/V2Ray/SS等)

配置:
PROXY_PORT=7890
PROXY_HOST=127.0.0.1
PROXY_SCHEME=socks5h

Docker环境:
PROXY_PORT=7890
PROXY_HOST=host.docker.internal
PROXY_SCHEME=socks5h


方案2: 使用 PROXY_URL (高级)
适合: 需要自定义代理URL

配置:
PROXY_URL=socks5h://127.0.0.1:7890

Docker环境:
PROXY_URL=socks5h://host.docker.internal:7890


方案3: 使用标准环境变量
适合: 兼容性最好

配置:
HTTP_PROXY=socks5h://127.0.0.1:7890
HTTPS_PROXY=socks5h://127.0.0.1:7890
ALL_PROXY=socks5h://127.0.0.1:7890

Docker环境:
HTTP_PROXY=socks5h://host.docker.internal:7890
HTTPS_PROXY=socks5h://host.docker.internal:7890
ALL_PROXY=socks5h://host.docker.internal:7890
"""

# ========================================
# 自动生成配置
# ========================================

def generate_env_config(port=7890, host="127.0.0.1", scheme="socks5h", use_docker=True):
    """生成.env配置"""

    if use_docker:
        proxy_host = "host.docker.internal"
        docker_note = "# Docker环境: 使用host.docker.internal访问宿主机代理"
    else:
        proxy_host = host
        docker_note = f"# 本地环境: 直接使用{host}"

    config = f"""# =========================
# VPN代理配置
# =========================
{docker_note}

# 方案1: 简化配置 (推荐)
PROXY_PORT={port}
PROXY_HOST={proxy_host}
PROXY_SCHEME={scheme}

# 方案2: 完整URL (可选，如果方案1不工作)
PROXY_URL={scheme}://{proxy_host}:{port}

# 方案3: 标准环境变量 (可选，兼容性最好)
ALL_PROXY={scheme}://{proxy_host}:{port}
HTTP_PROXY={scheme}://{proxy_host}:{port}
HTTPS_PROXY={scheme}://{proxy_host}:{port}
"""

    return config


def generate_docker_compose_extra():
    """生成Docker Compose额外配置"""

    return """# 在docker-compose.yml的backend服务中添加:
extra_hosts:
  - "host.docker.internal:host-gateway"

# 或者使用host网络模式 (Linux):
# network_mode: "host"
"""


if __name__ == "__main__":
    print("=" * 70)
    print("VPN代理配置生成器")
    print("=" * 70)

    print("\n请选择您的部署环境:")
    print("1. Docker部署 (推荐)")
    print("2. 本地开发环境")

    choice = input("\n请输入选项 (1 或 2): ").strip()

    if choice == "1":
        config = generate_env_config(
            port=VPN_PORT,
            use_docker=True
        )
        print("\n" + "=" * 70)
        print("Docker环境配置")
        print("=" * 70)
        print(config)

        print("\n" + "=" * 70)
        print("Docker Compose额外配置")
        print("=" * 70)
        print(generate_docker_compose_extra())

    elif choice == "2":
        config = generate_env_config(
            port=VPN_PORT,
            use_docker=False
        )
        print("\n" + "=" * 70)
        print("本地开发环境配置")
        print("=" * 70)
        print(config)

    else:
        print("无效选项")
        exit(1)

    print("\n" + "=" * 70)
    print("配置说明")
    print("=" * 70)
    print("""
1. 将上面的配置复制到 backend_api_python/.env 文件
2. 取消注释代理相关的行
3. 根据需要修改端口号和类型
4. 重启后端服务:
   docker compose restart backend

5. 验证代理是否工作:
   docker compose logs -f backend | grep -i proxy
""")

    print("\n常见VPN软件默认端口:")
    print("- Clash:      HTTP 7890 / SOCKS5 7891")
    print("- V2Ray:      HTTP 10808 / SOCKS5 10809")
    print("- Shadowsocks: SOCKS5 1080")
    print("\n请检查您的VPN软件设置以确认端口号")
