"""
自动清理项目临时文件
"""
import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent

# 要删除的文件模式
PATTERNS_TO_DELETE = [
    # 临时文档
    'BRAVE_MONITOR_*.md',
    'HAMA_MARKET_*.md',
    'HAMA_OVERLAY_*.md',
    'HAMA_TRADINGVIEW_*.md',
    'TRADINGVIEW_*.md',
    'TV_HAMA_*.md',
    'BATCH_HAMA_*.md',
    'BROWSER_MONITORING_*.md',
    'FIND_TV_API_*.md',
    'HAMA_OCR_*.md',
    'HAMA_README_*.md',
    'HAMA_TESTING_*.md',
    'OCR_HAMA_*.md',
    'TEST_SUMMARY*.md',
    'QUICK_START.md',

    # 临时脚本
    'batch_hama_*.py',
    'auto_login_*.py',
    'check_cookie.py',
    'extract_hama_*.py',
    'hama_brave_monitor.py',

    # 测试截图
    'hama_batch_*.png',
    'hama_brave_*.png',
    'cookie_check_screenshot.png',

    # 测试数据
    'hama_batch_results_*.csv',
    'hama_batch_results_*.json',

    # Pine脚本
    '*.pine',
]

# 要保留的文件
KEEP_PATTERNS = [
    'backend_api_python/app/screenshot/',  # screenshot目录可能需要
]

def get_git_untracked():
    """获取git未跟踪的文件"""
    result = subprocess.run(
        ['git', 'status', '--short', '--porcelain'],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True
    )

    untracked = []
    for line in result.stdout.splitlines():
        if line.startswith('??'):
            file_path = line[3:].strip()
            untracked.append(file_path)

    return untracked

def should_delete(file_path, patterns):
    """判断文件是否应该删除"""
    from fnmatch import fnmatch

    # 检查是否匹配删除模式
    for pattern in patterns:
        # 检查文件名
        if fnmatch(Path(file_path).name, pattern):
            return True
        # 检查完整路径
        if fnmatch(file_path.replace('\\', '/'), pattern):
            return True

    return False

def should_keep(file_path, keep_patterns):
    """判断文件是否应该保留"""
    for pattern in keep_patterns:
        if file_path.startswith(pattern.rstrip('/')):
            return True
    return False

def main():
    print("扫描未跟踪文件...")
    untracked = get_git_untracked()
    print(f"找到 {len(untracked)} 个未跟踪文件\n")

    files_to_delete = []
    files_to_keep = []

    for file_path in untracked:
        if should_keep(file_path, KEEP_PATTERNS):
            files_to_keep.append(file_path)
        elif should_delete(file_path, PATTERNS_TO_DELETE):
            files_to_delete.append(file_path)
        else:
            files_to_keep.append(file_path)

    print(f"准备删除: {len(files_to_delete)} 个文件")
    print(f"保留检查: {len(files_to_keep)} 个文件\n")

    if files_to_delete:
        # 删除文件和目录
        deleted_count = 0
        for file_path in files_to_delete:
            full_path = PROJECT_ROOT / file_path

            try:
                if full_path.is_dir():
                    import shutil
                    shutil.rmtree(full_path)
                    print(f"[OK] 删除目录: {file_path}")
                elif full_path.is_file():
                    full_path.unlink()
                    print(f"[OK] 删除文件: {file_path}")
                deleted_count += 1
            except Exception as e:
                print(f"[FAIL] 失败: {file_path} - {e}")

        print(f"\n[SUCCESS] 成功删除 {deleted_count}/{len(files_to_delete)} 个文件")

    if files_to_keep:
        print(f"\n保留的文件 (需要手动检查): {len(files_to_keep)}")
        for f in files_to_keep[:20]:
            print(f"  - {f}")
        if len(files_to_keep) > 20:
            print(f"  ... 还有 {len(files_to_keep)-20} 个")

if __name__ == "__main__":
    main()
