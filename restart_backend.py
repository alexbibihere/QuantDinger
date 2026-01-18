#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速重启后端服务 (Windows)
"""
import os
import sys
import time
import subprocess

def main():
    print("\n" + "="*80)
    print("🔄 重启后端服务")
    print("="*80)

    # 查找并终止现有进程
    print("\n1️⃣ 查找现有后端进程...")
    try:
        # 查找 Python run.py 进程
        result = subprocess.run(
            ['tasklist', '/FI', 'IMAGENAME eq python.exe', '/FO', 'CSV'],
            capture_output=True,
            text=True
        )

        if 'run.py' in result.stdout:
            print("   ⚠️  发现现有后端进程")
            print("   请手动关闭后端服务窗口,然后重新运行: python backend_api_python/run.py")
            return
        else:
            print("   ✅ 没有发现现有后端进程")
    except Exception as e:
        print(f"   ⚠️  检查进程失败: {e}")

    # 提示启动命令
    print("\n2️⃣ 启动后端服务...")
    print("   请在新终端窗口运行:")
    print("   cd backend_api_python")
    print("   python run.py")

    print("\n" + "="*80)
    print("✅ 准备完成!")
    print("="*80)
    print("\n📝 启动后可以测试:")
    print("   python backend_api_python/test_screenshot_cache.py --api")


if __name__ == '__main__':
    main()
