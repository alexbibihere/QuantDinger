#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
一键启动所有服务
包括：后端 API、HAMA Brave 监控、邮件通知、前端 Vue
"""
import sys
import os
import time
import subprocess
import io
import signal

# Windows 控制台编码修复
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# 存储子进程
processes = []

def signal_handler(sig, frame):
    """处理 Ctrl+C 信号"""
    print("\n\n⏹️  正在停止所有服务...")
    for proc in processes:
        if proc.poll() is None:  # 进程还在运行
            proc.terminate()
    print("✅ 所有服务已停止")
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

def start_backend():
    """启动后端服务"""
    print("\n" + "="*80)
    print("🚀 启动后端服务")
    print("="*80)

    backend_dir = os.path.join(os.path.dirname(__file__), 'backend_api_python')
    log_file = os.path.join(os.path.dirname(__file__), 'logs', 'backend.log')

    # 确保日志目录存在
    os.makedirs(os.path.dirname(log_file), exist_ok=True)

    # 启动后端
    cmd = [sys.executable, 'run.py']
    proc = subprocess.Popen(
        cmd,
        cwd=backend_dir,
        stdout=open(log_file, 'w'),
        stderr=subprocess.STDOUT,
        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == 'win32' else 0
    )
    processes.append(proc)

    print(f"✅ 后端服务已启动 (PID: {proc.pid})")
    print(f"   日志文件: {log_file}")
    print(f"   端口: 5000")

    # 等待后端启动
    print("   等待后端初始化...")
    time.sleep(15)  # 给 OCR 模型加载时间

    return proc

def start_hama_monitor():
    """启动 HAMA Brave 监控服务"""
    print("\n" + "="*80)
    print("🤖 启动 HAMA Brave 监控服务")
    print("="*80)

    log_file = os.path.join(os.path.dirname(__file__), 'logs', 'hama_monitor.log')

    # 启动监控脚本
    script_file = os.path.join(os.path.dirname(__file__), 'start_hama_monitor_simple.py')
    cmd = [sys.executable, script_file]

    proc = subprocess.Popen(
        cmd,
        stdout=open(log_file, 'w'),
        stderr=subprocess.STDOUT,
        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == 'win32' else 0
    )
    processes.append(proc)

    print(f"✅ HAMA 监控服务已启动 (PID: {proc.pid})")
    print(f"   日志文件: {log_file}")
    print(f"   监控币种: BTCUSDT, ETHUSDT, BNBUSDT, SOLUSDT, XRPUSDT, ADAUSDT, DOGEUSDT")
    print(f"   监控间隔: 10分钟")
    print(f"   OCR引擎: PaddleOCR")
    print(f"   邮件通知: 已启用")

    return proc

def start_frontend():
    """启动前端服务"""
    print("\n" + "="*80)
    print("🎨 启动前端服务")
    print("="*80)

    frontend_dir = os.path.join(os.path.dirname(__file__), 'quantdinger_vue')
    log_file = os.path.join(os.path.dirname(__file__), 'logs', 'frontend.log')

    # 启动前端
    cmd = ['npm', 'run', 'serve']
    proc = subprocess.Popen(
        cmd,
        cwd=frontend_dir,
        stdout=open(log_file, 'w'),
        stderr=subprocess.STDOUT,
        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == 'win32' else 0
    )
    processes.append(proc)

    print(f"✅ 前端服务已启动 (PID: {proc.pid})")
    print(f"   日志文件: {log_file}")
    print(f"   端口: 8000")

    # 等待前端启动
    print("   等待前端初始化...")
    time.sleep(10)

    return proc

def check_services():
    """检查服务状态"""
    print("\n" + "="*80)
    print("📊 服务状态检查")
    print("="*80)

    import socket

    def check_port(port, name):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(('localhost', port))
        sock.close()
        if result == 0:
            print(f"✅ {name}: 运行中 (端口 {port})")
            return True
        else:
            print(f"❌ {name}: 未运行 (端口 {port})")
            return False

    backend_ok = check_port(5000, "后端服务")
    frontend_ok = check_port(8000, "前端服务")

    # 检查监控进程
    monitor_ok = any(p.poll() is None for p in processes[1:2])  # HAMA 监控是第二个进程
    if monitor_ok:
        print("✅ HAMA 监控: 运行中")
    else:
        print("❌ HAMA 监控: 未运行")

    return backend_ok and frontend_ok and monitor_ok

def main():
    print("\n" + "="*80)
    print("🚀 QuantDinger 一键启动服务")
    print("="*80)
    print(f"启动时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")

    try:
        # 1. 启动后端
        start_backend()

        # 2. 启动 HAMA 监控
        start_hama_monitor()

        # 3. 启动前端
        start_frontend()

        # 4. 检查服务状态
        time.sleep(2)
        all_ok = check_services()

        print("\n" + "="*80)
        if all_ok:
            print("✅ 所有服务启动成功！")
        else:
            print("⚠️  部分服务启动失败，请检查日志")
        print("="*80)

        print("\n📝 访问地址:")
        print("   前端: http://localhost:8000")
        print("   后端 API: http://localhost:5000/api/health")
        print("   HAMA Market: http://localhost:8000/#/hama-market")

        print("\n📋 日志文件:")
        print("   后端: logs/backend.log")
        print("   监控: logs/hama_monitor.log")
        print("   前端: logs/frontend.log")

        print("\n⚠️  按 Ctrl+C 停止所有服务")
        print("="*80)
        print("\n监控运行中... (按 Ctrl+C 停止)\n")

        # 保持运行
        while True:
            time.sleep(1)

            # 检查进程是否还在运行
            for i, proc in enumerate(processes):
                if proc.poll() is not None:
                    print(f"\n⚠️  警告: 进程 {i} 已意外退出 (PID: {proc.pid})")

    except KeyboardInterrupt:
        signal_handler(None, None)
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        signal_handler(None, None)

    return 0

if __name__ == '__main__':
    sys.exit(main())
