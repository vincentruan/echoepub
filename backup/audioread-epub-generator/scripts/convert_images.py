# -*- coding: utf-8 -*-
"""
图片格式转换脚本

功能：
- 将 webp/gif/bmp 等格式转换为 jpg
- 保持原始 jpg/png 格式不变
- 备份原始文件到 bak/ 目录
- 更新 markdown 文件中的图片引用路径

使用方法：
    python convert_images.py <电子书目录>

示例：
    python convert_images.py "趋势与周期3-货币债务与投资时钟"
"""

import os
import re
import sys
import glob
import shutil
from pathlib import Path

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    print("警告：未安装 Pillow 库，无法进行图片格式转换")
    print("请运行：pip install Pillow")


def get_chapter_name(md_filename):
    """从 markdown 文件名提取章节名称"""
    basename = os.path.basename(md_filename)
    name, _ = os.path.splitext(basename)
    return name


def scan_images_in_markdown(md_file):
    """扫描 markdown 文件中的图片引用"""
    with open(md_file, 'r', encoding='utf-8') as f:
        content = f.read()

    images = []

    # 匹配 ![alt](path) 格式
    pattern1 = r'!\[([^\]]*)\]\(([^)]+)\)'
    for match in re.finditer(pattern1, content):
        alt, path = match.groups()
        images.append({
            'alt': alt,
            'path': path,
            'match': match.group(0),
            'start': match.start(),
            'end': match.end()
        })

    # 匹配 <img src="path"> 格式
    pattern2 = r'<img[^>]+src=["\']([^"\']+)["\'][^>]*>'
    for match in re.finditer(pattern2, content):
        path = match.group(1)
        images.append({
            'alt': '',
            'path': path,
            'match': match.group(0),
            'start': match.start(),
            'end': match.end(),
            'is_html': True
        })

    return images


def convert_image(input_path, output_path):
    """转换图片格式为 jpg"""
    if not PIL_AVAILABLE:
        return False

    try:
        with Image.open(input_path) as img:
            # 处理透明通道
            if img.mode in ('RGBA', 'LA', 'P'):
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                if img.mode in ('RGBA', 'LA'):
                    alpha = img.split()[-1]
                    background.paste(img, mask=alpha)
                else:
                    background.paste(img)
                img = background
            elif img.mode != 'RGB':
                img = img.convert('RGB')

            img.save(output_path, 'JPEG', quality=90, optimize=True)
        return True
    except Exception as e:
        print(f"  转换失败: {e}")
        return False


def process_chapter(md_file, ebook_dir):
    """处理单个章节的图片"""
    chapter_name = get_chapter_name(md_file)
    chapter_dir = md_file.replace('.md', '')

    # 检查是否有旧的图片目录
    old_images_dir = f"{chapter_dir}_images"
    if os.path.exists(old_images_dir):
        source_images_dir = old_images_dir
    else:
        # 查找其他可能的图片目录
        source_images_dir = None

    # 创建新的图片目录结构
    new_images_dir = os.path.join(ebook_dir, 'images', chapter_name)
    bak_dir = os.path.join(new_images_dir, 'bak')
    os.makedirs(new_images_dir, exist_ok=True)
    os.makedirs(bak_dir, exist_ok=True)

    # 读取 markdown 内容
    with open(md_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # 扫描图片引用
    images = scan_images_in_markdown(md_file)
    if not images:
        return {'processed': 0, 'converted': 0, 'errors': 0}

    processed = 0
    converted = 0
    errors = 0

    # 收集所有替换
    replacements = []

    for img_info in images:
        img_path = img_info['path']

        # 处理相对路径
        if img_path.startswith('./'):
            full_path = os.path.join(ebook_dir, img_path[2:])
        elif img_path.startswith('../'):
            full_path = os.path.normpath(os.path.join(ebook_dir, img_path))
        elif img_path.startswith('http'):
            # 跳过网络图片
            continue
        else:
            full_path = os.path.join(os.path.dirname(md_file), img_path)

        if not os.path.exists(full_path):
            print(f"  图片不存在: {img_path}")
            errors += 1
            continue

        filename = os.path.basename(full_path)
        name, ext = os.path.splitext(filename)
        ext = ext.lower()

        # 判断是否需要转换
        needs_conversion = ext not in ['.jpg', '.jpeg', '.png']

        if needs_conversion:
            # 备份原文件
            bak_path = os.path.join(bak_dir, filename)
            shutil.copy2(full_path, bak_path)

            # 转换为 jpg
            new_filename = f"{name}.jpg"
            new_path = os.path.join(new_images_dir, new_filename)

            if convert_image(full_path, new_path):
                converted += 1
                # 删除原文件
                if full_path != bak_path:
                    os.remove(full_path)
            else:
                errors += 1
                # 转换失败，直接移动原文件
                new_path = os.path.join(new_images_dir, filename)
                shutil.move(full_path, new_path)
                new_filename = filename
        else:
            # 直接移动文件
            new_filename = filename
            new_path = os.path.join(new_images_dir, new_filename)
            if full_path != new_path:
                shutil.move(full_path, new_path)

        # 记录新路径替换
        new_rel_path = f"./images/{chapter_name}/{new_filename}"
        replacements.append((img_info['match'], new_rel_path, img_info.get('alt', ''), img_info.get('is_html', False)))
        processed += 1

    # 执行替换
    for old_match, new_path, alt, is_html in replacements:
        if is_html:
            new_tag = f'<img src="{new_path}" alt="{alt}">'
        else:
            new_tag = f'![{alt}]({new_path})'
        content = content.replace(old_match, new_tag, 1)

    # 写回文件
    with open(md_file, 'w', encoding='utf-8') as f:
        f.write(content)

    # 清理空的旧图片目录
    if source_images_dir and os.path.exists(source_images_dir):
        try:
            if not os.listdir(source_images_dir):
                os.rmdir(source_images_dir)
        except:
            pass

    return {'processed': processed, 'converted': converted, 'errors': errors}


def main(ebook_dir):
    """主函数"""
    if not os.path.exists(ebook_dir):
        print(f"错误：目录不存在 - {ebook_dir}")
        return

    print(f"处理电子书目录: {ebook_dir}")
    print("-" * 50)

    # 扫描 markdown 文件
    md_files = glob.glob(os.path.join(ebook_dir, '*.md'))
    chapter_files = [f for f in md_files if re.match(r'^\d+_', os.path.basename(f))]
    chapter_files.sort(key=lambda f: int(re.match(r'^(\d+)_', os.path.basename(f)).group(1)))

    if not chapter_files:
        print("未找到章节文件")
        return

    print(f"找到 {len(chapter_files)} 个章节文件")
    print()

    total_processed = 0
    total_converted = 0
    total_errors = 0

    for md_file in chapter_files:
        chapter_name = get_chapter_name(md_file)
        print(f"处理: {chapter_name}")

        result = process_chapter(md_file, ebook_dir)
        total_processed += result['processed']
        total_converted += result['converted']
        total_errors += result['errors']

        if result['processed'] > 0:
            print(f"  处理: {result['processed']} | 转换: {result['converted']} | 错误: {result['errors']}")

    print()
    print("-" * 50)
    print(f"总计: 处理 {total_processed} | 转换 {total_converted} | 错误 {total_errors}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("使用方法: python convert_images.py <电子书目录>")
        sys.exit(1)

    ebook_dir = sys.argv[1]
    main(ebook_dir)
