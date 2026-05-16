#!/usr/bin/env python3
"""
清理脚本：删除根目录 data/ 下的本地测试缓存（图片、解析产物等）。

这个目录是 gitignored 的，不会被提交，但长期占磁盘空间。
建议每月跑一次，或空间不足时跑。
"""
import os
import shutil
import argparse

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')


def get_size(path: str) -> str:
    """返回人类可读的文件大小"""
    total = 0
    for dirpath, _, filenames in os.walk(path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            if os.path.exists(fp):
                total += os.path.getsize(fp)
    for unit in ['B', 'KB', 'MB', 'GB']:
        if total < 1024:
            return f"{total:.1f} {unit}"
        total /= 1024
    return f"{total:.1f} TB"


def main():
    parser = argparse.ArgumentParser(description='清理 data/ 本地测试缓存')
    parser.add_argument('--dry-run', action='store_true', help='只显示大小，不删除')
    parser.add_argument('--force', action='store_true', help='跳过确认直接删除')
    args = parser.parse_args()

    if not os.path.exists(DATA_DIR):
        print(f'目录不存在: {DATA_DIR}')
        return

    size = get_size(DATA_DIR)
    file_count = sum(len(files) for _, _, files in os.walk(DATA_DIR))
    print(f'data/ 目录: {DATA_DIR}')
    print(f'大小: {size}')
    print(f'文件数: {file_count}')

    if args.dry_run:
        print('\n[DRY RUN] 未做任何删除。加 --force 实际删除。')
        return

    if not args.force:
        ans = input(f'\n确认删除 data/ 目录（{size}，{file_count} 个文件）？[y/N] ')
        if ans.lower() != 'y':
            print('已取消')
            return

    shutil.rmtree(DATA_DIR)
    print(f'\n已删除: {DATA_DIR}')
    print('提示：data/ 已被 gitignore，不影响版本控制。')


if __name__ == '__main__':
    main()
