#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
QuantDinger 部署状态检查脚本
运行此脚本检查 Docker 容器和服务的健康状态
"""

import subprocess
import requests
import time
import sys
from datetime import datetime

def run_command(cmd):
    """运行命令并返回输出"""
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=30
        )
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)

def check_docker():
    """检查 Docker 是否运行"""
    print("🔍 检查 Docker 状态...")
    success, stdout, stderr = run_command("docker --version")
    if success:
        print(f"✅ Docker 已安装: {stdout.strip()}")
        return True
    else:
        print(f"❌ Docker 未安装或未运行")
        return False

def check_containers():
    """检查容器状态"""
    print("\n🔍 检查容器状态...")
    success, stdout, stderr = run_command("docker compose ps")

    if not success:
        print(f"❌ 无法获取容器状态")
        print(f"错误: {stderr}")
        return False

    print(stdout)

    # 检查是否两个容器都在运行
    if "quantdinger-backend" in stdout and "quantdinger-frontend" in stdout:
        if "Up" in stdout:
            print("✅ 容器正在运行")
            return True
        else:
            print("⚠️ 容器已创建但可能未正常运行")
            return False
    else:
        print("❌ 容器未找到")
        return False

def check_backend_health():
    """检查后端健康"""
    print("\n🔍 检查后端健康...")

    # 等待后端启动
    for i in range(10):
        try:
            response = requests.get("http://localhost:5000/api/health", timeout=5)
            if response.status_code == 200:
                data = response.json()
                print(f"✅ 后端健康检查通过")
                print(f"   状态: {data.get('status')}")
                print(f"   时间戳: {data.get('timestamp')}")
                return True
        except:
            print(f"⏳ 等待后端启动... ({i+1}/10)")
            time.sleep(2)

    print("❌ 后端健康检查失败")
    return False

def check_frontend():
    """检查前端"""
    print("\n🔍 检查前端服务...")

    for i in range(10):
        try:
            response = requests.get("http://localhost:8888", timeout=5)
            if response.status_code == 200:
                print("✅ 前端服务正常运行")
                return True
        except:
            print(f"⏳ 等待前端启动... ({i+1}/10)")
            time.sleep(2)

    print("❌ 前端服务检查失败")
    return False

def check_gainer_analysis_api():
    """检查涨幅榜API"""
    print("\n🔍 检查涨幅榜分析API...")

    try:
        # 先尝试登录获取session
        login_data = {
            "username": "quantdinger",
            "password": "123456"
        }
        session = requests.Session()
        response = session.post(
            "http://localhost:5000/api/user/login",
            json=login_data,
            timeout=5
        )

        if response.status_code == 200:
            print("✅ 登录成功")

            # 测试涨幅榜API
            response = session.get(
                "http://localhost:5000/api/gainer-analysis/top-gainers?limit=3",
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    symbols = data.get("data", {}).get("symbols", [])
                    print(f"✅ 涨幅榜API正常 (获取到 {len(symbols)} 个币种)")
                    return True
                else:
                    print(f"⚠️ API返回错误: {data.get('message')}")
                    return False
            else:
                print(f"❌ API请求失败: HTTP {response.status_code}")
                return False
        else:
            print(f"⚠️ 登录失败: HTTP {response.status_code}")
            return False

    except Exception as e:
        print(f"❌ API检查失败: {str(e)}")
        return False

def show_logs(container):
    """显示容器日志"""
    print(f"\n📋 显示 {container} 日志 (最后20行):")
    print("=" * 60)
    success, stdout, stderr = run_command(f"docker compose logs --tail=20 {container}")
    if success:
        print(stdout)
    else:
        print(f"无法获取日志: {stderr}")

def main():
    """主函数"""
    print("=" * 60)
    print("QuantDinger 部署状态检查")
    print("=" * 60)
    print(f"检查时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    # 检查步骤
    results = {}

    results["docker"] = check_docker()

    if not results["docker"]:
        print("\n❌ Docker 未运行,请先启动 Docker Desktop")
        return False

    results["containers"] = check_containers()

    if not results["containers"]:
        print("\n❌ 容器未运行,请先执行部署")
        print("   运行: 一键部署.bat")
        return False

    results["backend"] = check_backend_health()
    results["frontend"] = check_frontend()
    results["api"] = check_gainer_analysis_api()

    # 总结
    print("\n" + "=" * 60)
    print("检查结果汇总")
    print("=" * 60)

    all_passed = True
    for name, passed in results.items():
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"{name.upper():15} {status}")
        if not passed:
            all_passed = False

    print("=" * 60)

    if all_passed:
        print("\n🎉 所有检查通过!")
        print("\n📱 访问地址:")
        print("   前端首页: http://localhost:8888")
        print("   涨幅榜分析: http://localhost:8888/gainer-analysis")
        print("   后端API: http://localhost:5000")
        print("\n👤 登录信息:")
        print("   用户名: quantdinger")
        print("   密码: 123456")
    else:
        print("\n⚠️ 部分检查未通过")
        print("\n建议操作:")
        if not results.get("containers"):
            print("   1. 运行 '一键部署.bat' 重新部署")
        elif not results.get("backend"):
            print("   1. 检查后端日志: docker compose logs backend")
            print("   2. 重启后端: docker compose restart backend")
        elif not results.get("api"):
            print("   1. 检查后端日志: docker compose logs backend")
            show_logs("backend")

    print("\n" + "=" * 60)

    return all_passed

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️ 检查被中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 发生错误: {str(e)}")
        sys.exit(1)
