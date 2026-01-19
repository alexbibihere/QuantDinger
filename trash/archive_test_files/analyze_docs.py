#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
分析根目录文档的引用情况
"""
import os
import re
from pathlib import Path

# 被核心文档引用的文件（不应移动）
CORE_REFERENCED = {
    'README.md',
    'README_CN.md',
    'CLAUDE.md',
    'LICENSE',
    'CODE_OF_CONDUCT.md',
    'CONTRIBUTING.md',
    'SECURITY.md',
    'docker-compose.yml',
    'START_HERE.md',
    'COMPLETE_GUIDE.md',
    'TROUBLESHOOTING.md',
    'DEPLOYMENT_CHECKLIST.md',
    'DOCKER_DEPLOYMENT.md',
    'DEPLOY_STEP_BY_STEP.md'
}

# 应该保留在根目录的文档
KEEP_IN_ROOT = {
    'README.md',
    'README_CN.md',
    'README_JA.md',
    'README_KO.md',
    'README_TW.md',
    'CLAUDE.md',
    'LICENSE',
    'CODE_OF_CONDUCT.md',
    'CONTRIBUTING.md',
    'SECURITY.md',
    '.gitignore',
    'docker-compose.yml',
    'START_HERE.md',
    'QUICKSTART.md',
    'COMPLETE_GUIDE.md',
    'TROUBLESHOOTING.md',
    'DEPLOYMENT_CHECKLIST.md',
    'DOCKER_DEPLOYMENT.md',
    'DEPLOY_STEP_BY_STEP.md'
}

# docs 目录中已有的文档
DOCS_FOLDER = {
    'HAMA_MARKET_IMPLEMENTATION.md'
}

def find_references(directory, exclude_dirs=None):
    """在代码中查找文档引用"""
    if exclude_dirs is None:
        exclude_dirs = ['.git', 'node_modules', '__pycache__', 'venv', 'env',
                       'backend_api_python/data', 'backend_api_python/logs',
                       '.venv', '.env', 'dist', 'build']

    references = set()
    pattern = r'\[([^\]]+)\]\(([^)]+\.md)\)|["`]([^`"]+\.md)["`]'

    for root, dirs, files in os.walk(directory):
        # 排除特定目录
        dirs[:] = [d for d in dirs if d not in exclude_dirs and not d.startswith('.')]

        for file in files:
            if file.endswith(('.md', '.py', '.js', '.ts', '.vue', '.txt', 'json')):
                filepath = os.path.join(root, file)
                try:
                    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        # 查找 Markdown 链接引用
                        matches = re.findall(pattern, content)
                        for match in matches:
                            if len(match) == 3:
                                ref = match[1] or match[2]
                            else:
                                ref = match[0] if isinstance(match, str) else match[1]
                            # 只取文件名
                            ref_name = os.path.basename(ref)
                            if ref_name.endswith('.md'):
                                references.add(ref_name)
                except Exception as e:
                    pass

    return references

def main():
    root_dir = Path('.')
    md_files = [f for f in os.listdir('.') if f.endswith('.md')]

    # 查找所有引用
    referenced_files = find_references('.')

    # 分析每个文件
    to_move = []
    keep = []

    for md_file in md_files:
        if md_file in KEEP_IN_ROOT:
            keep.append((md_file, '核心文档，保留在根目录'))
            continue

        if md_file in DOCS_FOLDER:
            keep.append((md_file, '已在 docs 文件夹中'))
            continue

        if md_file in referenced_files:
            keep.append((md_file, '被代码或其他文档引用'))
        else:
            to_move.append(md_file)

    # 输出结果
    print("=" * 80)
    print("文档引用分析结果")
    print("=" * 80)

    print(f"\n[OK] Documents to keep in root ({len(keep)} items):")
    print("-" * 80)
    for file, reason in sorted(keep):
        print(f"  {file:50s} - {reason}")

    print(f"\n[TRASH] Documents to move to trash/ ({len(to_move)} items):")
    print("-" * 80)
    for file in sorted(to_move):
        print(f"  {file}")

    # 生成移动脚本
    if to_move:
        print("\n" + "=" * 80)
        print("Generating move scripts...")
        print("=" * 80)

        with open('move_to_trash.sh', 'w') as f:
            f.write('#!/bin/bash\n')
            f.write('# Move unreferenced documents to trash folder\n\n')
            f.write('mkdir -p trash/archive_docs\n\n')
            for file in to_move:
                f.write(f'mv "{file}" trash/archive_docs/\n')
        print("[OK] Generated move script: move_to_trash.sh")

        with open('move_to_trash.bat', 'w') as f:
            f.write('@echo off\n')
            f.write('REM Move unreferenced documents to trash folder\n\n')
            f.write('if not exist trash\\archive_docs mkdir trash\\archive_docs\n\n')
            for file in to_move:
                f.write(f'move "{file}" trash\\archive_docs\\\n')
        print("[OK] Generated move script: move_to_trash.bat")

    print("\n" + "=" * 80)
    print(f"总计: {len(md_files)} 个 Markdown 文档")
    print(f"  - 保留: {len(keep)} 个")
    print(f"  - 移动: {len(to_move)} 个")
    print("=" * 80)

if __name__ == '__main__':
    main()
