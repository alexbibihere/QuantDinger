"""
项目清理脚本 - 删除不需要的临时文件和文档
"""
import os
import shutil
from pathlib import Path

# 项目根目录
PROJECT_ROOT = Path(__file__).parent


def get_untracked_files():
    """获取所有未跟踪的文件"""
    import subprocess
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


def categorize_files(file_list):
    """分类文件"""
    categories = {
        '临时文档': [],
        '临时脚本': [],
        '测试截图': [],
        '测试数据': [],
        'Pine脚本': [],
        '其他': []
    }

    for file_path in file_list:
        full_path = PROJECT_ROOT / file_path

        # 跳过目录
        if full_path.is_dir():
            categories['其他'].append(file_path)
            continue

        # 临时文档
        if any(x in file_path for x in [
            'BRAVE_MONITOR_', 'HAMA_MARKET_', 'HAMA_OVERLAY_',
            'HAMA_TRADINGVIEW_', 'TRADINGVIEW_', 'TV_HAMA_',
            'BATCH_HAMA_', 'BROWSER_MONITORING_', 'FIND_TV_API_',
            'HAMA_OCR_', 'HAMA_README_', 'HAMA_TESTING_', 'OCR_HAMA_',
            'TEST_SUMMARY', 'QUICK_START'
        ]) and file_path.endswith('.md'):
            categories['临时文档'].append(file_path)

        # 临时脚本
        elif any(x in file_path for x in [
            'batch_hama_', 'auto_login_', 'check_cookie.',
            'extract_hama_', 'hama_brave_monitor'
        ]) and file_path.endswith('.py'):
            categories['临时脚本'].append(file_path)

        # 测试截图
        elif 'hama_batch_' in file_path or 'hama_brave_' in file_path:
            if file_path.endswith('.png'):
                categories['测试截图'].append(file_path)

        # 测试数据
        elif 'hama_batch_results_' in file_path:
            categories['测试数据'].append(file_path)

        # Pine脚本
        elif file_path.endswith('.pine'):
            categories['Pine脚本'].append(file_path)

        # 其他
        else:
            categories['其他'].append(file_path)

    return categories


def print_summary(categories):
    """打印清理摘要"""
    print("\n" + "="*80)
    print("项目清理建议")
    print("="*80)

    total = 0
    for category, files in categories.items():
        count = len(files)
        total += count
        if count > 0:
            print(f"\n{category}: {count} 个文件")
            if category in ['临时文档', '临时脚本', '测试截图', '测试数据', 'Pine脚本']:
                for f in files[:5]:  # 只显示前5个
                    print(f"  - {f}")
                if count > 5:
                    print(f"  ... 还有 {count-5} 个")

    print(f"\n总计: {total} 个未跟踪文件")
    print("="*80)


def delete_files(file_list, dry_run=True):
    """删除文件"""
    if not file_list:
        print("没有文件需要删除")
        return

    print(f"\n{'='*80}")
    print(f"模式: {'预览 (不会真正删除)' if dry_run else '执行 (将永久删除!)'}")
    print(f"{'='*80}\n")

    for file_path in file_list:
        full_path = PROJECT_ROOT / file_path

        if dry_run:
            print(f"将删除: {file_path}")
        else:
            try:
                if full_path.is_dir():
                    shutil.rmtree(full_path)
                    print(f"✓ 删除目录: {file_path}")
                else:
                    full_path.unlink()
                    print(f"✓ 删除文件: {file_path}")
            except Exception as e:
                print(f"✗ 删除失败: {file_path} - {e}")


def main():
    """主函数"""
    print("\n正在扫描未跟踪的文件...")
    untracked = get_untracked_files()
    print(f"找到 {len(untracked)} 个未跟踪文件\n")

    categories = categorize_files(untracked)
    print_summary(categories)

    # 建议删除的文件
    files_to_delete = []
    files_to_delete.extend(categories['临时文档'])
    files_to_delete.extend(categories['临时脚本'])
    files_to_delete.extend(categories['测试截图'])
    files_to_delete.extend(categories['测试数据'])
    files_to_delete.extend(categories['Pine脚本'])

    # 保留的文件/目录 (手动检查)
    keep_files = [
        'backend_api_python/app/screenshot/',  # 可能需要
    ]

    # 过滤掉需要保留的
    files_to_delete = [f for f in files_to_delete
                       if not any(f.startswith(k) for k in keep_files)]

    print(f"\n{'='*80}")
    print(f"建议删除: {len(files_to_delete)} 个文件")
    print(f"保留检查: {len(categories['其他'])} 个文件 (请手动检查)")
    print(f"{'='*80}")

    # 先预览
    print("\n预览模式 - 这些文件将被删除:\n")
    for f in files_to_delete[:10]:
        print(f"  - {f}")
    if len(files_to_delete) > 10:
        print(f"  ... 还有 {len(files_to_delete)-10} 个")

    # 询问
    choice = input("\n是否执行删除? (yes/no): ").strip().lower()

    if choice == 'yes':
        delete_files(files_to_delete, dry_run=False)
        print(f"\n✅ 成功删除 {len(files_to_delete)} 个文件")
    else:
        print("\n已取消删除")


if __name__ == "__main__":
    main()