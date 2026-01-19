#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查根目录中可能不需要的文档
"""
import os
import re
from pathlib import Path

# 明确应该保留的核心文档
CORE_DOCS = {
    'README.md', 'README_CN.md', 'README_JA.md', 'README_KO.md', 'README_TW.md',
    'CLAUDE.md',
    'CODE_OF_CONDUCT.md', 'CONTRIBUTING.md', 'SECURITY.md',
    'START_HERE.md', 'COMPLETE_GUIDE.md', 'TROUBLESHOOTING.md',
    'docker-compose.yml'
}

# 功能指南文档（如果被引用则保留）
GUIDE_DOCS = {
    'DEPLOY_STEP_BY_STEP.md',
    'DOCKER_DEPLOYMENT.md',
    'DEPLOYMENT_CHECKLIST.md',
}

def find_references(directory, filename):
    """查找特定文件的引用"""
    references = []
    pattern = re.compile(re.escape(filename), re.IGNORECASE)

    for root, dirs, files in os.walk(directory):
        # 排除目录
        dirs[:] = [d for d in dirs if d not in ['.git', 'node_modules', '__pycache__',
                                                   'venv', 'env', 'dist', 'build',
                                                   'trash', 'backend_api_python/data',
                                                   'backend_api_python/logs']]

        for file in files:
            if file.endswith(('.md', '.py', '.js', '.ts', '.vue', 'json', 'txt')):
                filepath = os.path.join(root, file)
                try:
                    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        if pattern.search(content):
                            references.append(filepath)
                except:
                    pass

    return references

def main():
    md_files = sorted([f for f in os.listdir('.') if f.endswith('.md')])

    print("=" * 80)
    print("文档使用情况分析")
    print("=" * 80)

    # 分析每个文档
    potentially_unused = []
    used_docs = []

    for md_file in md_files:
        if md_file in CORE_DOCS:
            used_docs.append((md_file, '核心文档'))
            continue

        if md_file in GUIDE_DOCS:
            used_docs.append((md_file, '指南文档'))
            continue

        # 查找引用
        refs = find_references('.', md_file)

        # 检查是否被其他md文件引用（排除自引用）
        md_refs = [r for r in refs if r.endswith('.md') and not r.endswith(f'/{md_file}')]

        if len(md_refs) == 0 and len(refs) <= 1:  # 只有自引用或完全无引用
            potentially_unused.append((md_file, refs))
        else:
            used_docs.append((md_file, f'被 {len(md_refs)} 个文档引用'))

    # 输出结果
    print(f"\n[OK] Documents in use ({len(used_docs)} items):")
    print("-" * 80)
    for file, reason in sorted(used_docs):
        print(f"  {file:50s} - {reason}")

    print(f"\n[WARNING] Potentially unused documents ({len(potentially_unused)} items):")
    print("-" * 80)
    for file, refs in sorted(potentially_unused):
        if len(refs) == 0:
            print(f"  {file:50s} - 完全无引用")
        else:
            # 只被自己引用
            print(f"  {file:50s} - 仅有自引用")

    # 生成移动脚本
    if potentially_unused:
        print("\n" + "=" * 80)
        print("生成移动脚本...")
        print("=" * 80)

        with open('move_unused_docs.sh', 'w') as f:
            f.write('#!/bin/bash\n')
            f.write('# Move potentially unused documents to trash/archive_docs/\n\n')
            f.write('mkdir -p trash/archive_docs\n\n')
            for file, _ in potentially_unused:
                f.write(f'mv "{file}" trash/archive_docs/\n')
        print("[OK] Generated: move_unused_docs.sh")

        with open('move_unused_docs.bat', 'w') as f:
            f.write('@echo off\n')
            f.write('REM Move potentially unused documents to trash\\archive_docs\\\n\n')
            f.write('if not exist trash\\archive_docs mkdir trash\\archive_docs\n\n')
            for file, _ in potentially_unused:
                f.write(f'move "{file}" trash\\archive_docs\\\n')
        print("[OK] Generated: move_unused_docs.bat")

    print("\n" + "=" * 80)
    print(f"总计: {len(md_files)} 个 Markdown 文档")
    print(f"  - 使用中: {len(used_docs)} 个")
    print(f"  - 可能不需要: {len(potentially_unused)} 个")
    print("=" * 80)

if __name__ == '__main__':
    main()
