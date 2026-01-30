# -*- coding: utf-8 -*-
"""
处理报告生成脚本

功能：
- 扫描电子书目录
- 统计处理结果
- 生成 Markdown 格式的处理报告

使用方法：
    python generate_report.py <电子书目录>
"""

import os
import re
import sys
import glob
from datetime import datetime


def scan_ebook(directory):
    """扫描电子书目录"""
    result = {
        'name': os.path.basename(directory),
        'chapters': [],
        'images': {
            'total': 0,
            'converted': 0,
            'by_chapter': {}
        },
        'files': {
            'md_count': 0,
            'has_toc': False,
            'has_combined': False,
            'has_epub': False
        }
    }

    # 扫描 markdown 文件
    md_files = glob.glob(os.path.join(directory, '*.md'))

    for md_file in md_files:
        basename = os.path.basename(md_file)

        if '目录' in basename:
            result['files']['has_toc'] = True
        elif '合集' in basename:
            result['files']['has_combined'] = True
        elif re.match(r'^\d+_', basename):
            result['chapters'].append(basename)
            result['files']['md_count'] += 1

    result['chapters'].sort(key=lambda x: int(re.match(r'^(\d+)_', x).group(1)))

    # 扫描 epub 文件
    epub_files = glob.glob(os.path.join(directory, '*.epub'))
    if epub_files:
        result['files']['has_epub'] = True
        result['files']['epub_file'] = os.path.basename(epub_files[0])

    # 扫描图片
    images_dir = os.path.join(directory, 'images')
    if os.path.exists(images_dir):
        for chapter_dir in os.listdir(images_dir):
            chapter_path = os.path.join(images_dir, chapter_dir)
            if os.path.isdir(chapter_path):
                # 统计图片
                images = [f for f in os.listdir(chapter_path)
                         if f.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.webp'))
                         and not os.path.isdir(os.path.join(chapter_path, f))]

                # 统计备份图片（已转换的）
                bak_dir = os.path.join(chapter_path, 'bak')
                converted = 0
                if os.path.exists(bak_dir):
                    converted = len([f for f in os.listdir(bak_dir)
                                   if not os.path.isdir(os.path.join(bak_dir, f))])

                result['images']['by_chapter'][chapter_dir] = {
                    'count': len(images),
                    'converted': converted
                }
                result['images']['total'] += len(images)
                result['images']['converted'] += converted

    return result


def generate_report(directory):
    """生成处理报告"""
    data = scan_ebook(directory)

    report = []
    report.append(f"# 电子书处理报告\n")
    report.append(f"\n## 基本信息\n")
    report.append(f"- **电子书名称**：{data['name']}\n")
    report.append(f"- **生成时间**：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    report.append(f"- **章节数量**：{len(data['chapters'])}\n")

    report.append(f"\n## 文件状态\n")
    report.append(f"| 项目 | 状态 |\n")
    report.append(f"|------|------|\n")
    report.append(f"| 章节文件 | {data['files']['md_count']} 个 |\n")
    report.append(f"| 目录文件 | {'✓ 存在' if data['files']['has_toc'] else '✗ 未找到'} |\n")
    report.append(f"| 合集文件 | {'✓ 存在' if data['files']['has_combined'] else '✗ 未找到'} |\n")
    report.append(f"| EPUB 电子书 | {'✓ ' + data['files'].get('epub_file', '') if data['files']['has_epub'] else '✗ 未生成'} |\n")

    report.append(f"\n## 图片处理\n")
    report.append(f"- **总图片数**：{data['images']['total']}\n")
    report.append(f"- **已转换数**：{data['images']['converted']}\n")

    if data['images']['by_chapter']:
        report.append(f"\n### 各章节图片统计\n")
        report.append(f"| 章节 | 图片数 | 已转换 |\n")
        report.append(f"|------|--------|--------|\n")
        for chapter, stats in sorted(data['images']['by_chapter'].items()):
            report.append(f"| {chapter} | {stats['count']} | {stats['converted']} |\n")

    report.append(f"\n## 章节列表\n")
    for i, chapter in enumerate(data['chapters'], 1):
        report.append(f"{i}. {chapter}\n")

    report.append(f"\n## 待完成项\n")
    todos = []
    if not data['files']['has_toc']:
        todos.append("- [ ] 生成目录文件")
    if not data['files']['has_combined']:
        todos.append("- [ ] 生成合集文件")
    if not data['files']['has_epub']:
        todos.append("- [ ] 生成 EPUB 电子书")
    if data['images']['total'] == 0 and data['files']['md_count'] > 0:
        todos.append("- [ ] 处理图片资源")

    if todos:
        report.extend(todos)
        report.append("\n")
    else:
        report.append("所有项目已完成！\n")

    return ''.join(report)


def main():
    if len(sys.argv) < 2:
        print("使用方法: python generate_report.py <电子书目录>")
        sys.exit(1)

    directory = sys.argv[1]
    if not os.path.exists(directory):
        print(f"错误：目录不存在 - {directory}")
        sys.exit(1)

    report = generate_report(directory)

    # 输出到控制台
    print(report)

    # 保存到文件
    report_path = os.path.join(directory, 'processing_report.md')
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)

    print(f"\n报告已保存至: {report_path}")


if __name__ == "__main__":
    main()
