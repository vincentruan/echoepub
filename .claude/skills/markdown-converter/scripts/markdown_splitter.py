#!/usr/bin/env python3
"""
Markdown Splitter - Convert Markdown files/folders to standard multi-file format.

Usage:
    python markdown_splitter.py <input> [output-dir]
    
    input: Markdown file path or folder path
    output-dir: Optional, defaults to input file's directory
"""

import os
import sys
import re
import shutil
from datetime import datetime
from pathlib import Path

# Optional: Pillow for image conversion
try:
    from PIL import Image
    HAS_PILLOW = True
except ImportError:
    HAS_PILLOW = False


def sanitize_filename(title: str) -> str:
    """Convert title to safe filename."""
    # Remove/replace invalid characters
    title = re.sub(r'[<>:"/\\|?*]', '', title)
    title = re.sub(r'\s+', '_', title.strip())
    return title[:50] if len(title) > 50 else title


def extract_h1_title(content: str) -> str:
    """Extract first H1 title from markdown content."""
    match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
    if match:
        return match.group(1).strip()
    return None


def split_by_headers(content: str, level: int = 1) -> list:
    """
    Split markdown content by header level.
    Returns list of (title, content) tuples.
    """
    header_pattern = f'^{"#" * level}\\s+(.+)$'
    parts = re.split(f'({header_pattern})', content, flags=re.MULTILINE)
    
    chapters = []
    preamble = parts[0].strip() if parts else ""
    
    if preamble:
        chapters.append(("前言", preamble))
    
    i = 1
    while i < len(parts):
        if re.match(header_pattern, parts[i], re.MULTILINE):
            title = re.match(header_pattern, parts[i], re.MULTILINE).group(1).strip()
            content_part = parts[i + 1] if i + 1 < len(parts) else ""
            full_content = f"# {title}\n\n{content_part.strip()}"
            chapters.append((title, full_content))
            i += 2
        else:
            i += 1
    
    return chapters


def find_index_file(folder: Path) -> tuple:
    """
    Find index/summary file in folder.
    Returns (file_path, file_type) or (None, None).
    """
    priority_files = [
        ('SUMMARY.md', 'summary'),
        ('summary.md', 'summary'),
        ('_sidebar.md', 'summary'),
        ('toc.md', 'toc'),
        ('目录.md', 'toc'),
        ('README.md', 'readme'),
        ('readme.md', 'readme'),
        ('index.md', 'readme'),
    ]
    
    for filename, file_type in priority_files:
        filepath = folder / filename
        if filepath.exists():
            return filepath, file_type
    
    return None, None


def parse_summary_links(content: str) -> list:
    """
    Parse SUMMARY.md style links.
    Returns list of (title, path) tuples.
    """
    links = []
    pattern = r'\[([^\]]+)\]\(([^)]+)\)'
    
    for match in re.finditer(pattern, content):
        title = match.group(1).strip()
        path = match.group(2).strip()
        if path.endswith('.md'):
            links.append((title, path))
    
    return links


def collect_markdown_files(folder: Path, exclude_dirs: set = None) -> list:
    """
    Collect all markdown files from folder.
    Returns sorted list of file paths.
    """
    if exclude_dirs is None:
        exclude_dirs = {'node_modules', '.git', 'build', 'dist', '__pycache__', '.venv', 'venv'}
    
    md_files = []
    
    for root, dirs, files in os.walk(folder):
        # Filter out excluded directories
        dirs[:] = [d for d in dirs if d not in exclude_dirs and not d.startswith('.')]
        
        for f in files:
            if f.endswith('.md') and not f.startswith('.'):
                md_files.append(Path(root) / f)
    
    # Sort by natural order (handle numeric prefixes)
    def sort_key(p):
        name = p.stem
        match = re.match(r'^(\d+)', name)
        if match:
            return (0, int(match.group(1)), name)
        return (1, 0, name)
    
    return sorted(md_files, key=sort_key)


def process_images(content: str, source_dir: Path, output_images_dir: Path, chapter_num: str) -> tuple:
    """
    Process images in markdown content.
    Copy images to output directory and update paths.
    Returns (updated_content, image_count).
    """
    chapter_images_dir = output_images_dir / chapter_num
    chapter_images_dir.mkdir(parents=True, exist_ok=True)
    
    image_pattern = r'!\[([^\]]*)\]\(([^)]+)\)'
    image_count = 0
    
    def replace_image(match):
        nonlocal image_count
        alt_text = match.group(1)
        img_path = match.group(2)
        
        # Skip URLs
        if img_path.startswith(('http://', 'https://', 'data:')):
            return match.group(0)
        
        # Resolve image path
        if img_path.startswith('/'):
            source_img = Path(img_path)
        else:
            source_img = source_dir / img_path
        
        if not source_img.exists():
            return match.group(0)
        
        # Determine output filename
        image_count += 1
        ext = source_img.suffix.lower()
        
        # Convert if needed
        if HAS_PILLOW and ext in ['.webp', '.gif', '.bmp']:
            output_name = f"image_{image_count:03d}.jpg"
            output_path = chapter_images_dir / output_name
            try:
                with Image.open(source_img) as img:
                    if img.mode in ('RGBA', 'LA', 'P'):
                        bg = Image.new('RGB', img.size, (255, 255, 255))
                        if img.mode == 'P':
                            img = img.convert('RGBA')
                        bg.paste(img, mask=img.split()[-1] if 'A' in img.mode else None)
                        img = bg
                    elif img.mode != 'RGB':
                        img = img.convert('RGB')
                    img.save(output_path, 'JPEG', quality=90)
            except Exception:
                shutil.copy2(source_img, chapter_images_dir / source_img.name)
                output_name = source_img.name
        else:
            output_name = f"image_{image_count:03d}{ext}"
            output_path = chapter_images_dir / output_name
            shutil.copy2(source_img, output_path)
        
        return f"![{alt_text}](./images/{chapter_num}/{output_name})"
    
    updated_content = re.sub(image_pattern, replace_image, content)
    return updated_content, image_count


def convert_single_file(input_path: Path, output_dir: Path) -> dict:
    """Convert a single markdown file to standard format."""
    with open(input_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Determine split level
    has_h1 = bool(re.search(r'^#\s+', content, re.MULTILINE))
    split_level = 1 if has_h1 else 2
    
    chapters = split_by_headers(content, split_level)
    
    if not chapters:
        chapters = [("内容", content)]
    
    # Create output directory
    base_name = input_path.stem
    output_folder = output_dir / f"{base_name}_markdown"
    output_folder.mkdir(parents=True, exist_ok=True)
    images_dir = output_folder / "images"
    
    report = {
        'input_type': '单文件',
        'input_path': str(input_path),
        'timestamp': datetime.now().isoformat(),
        'chapters': [],
        'total_images': 0,
        'converted_images': 0,
    }
    
    # Generate table of contents
    toc_lines = [f"# {base_name}", "", "> 来源：单文件转换", "", "## 目录", ""]
    
    for idx, (title, chapter_content) in enumerate(chapters):
        chapter_num = f"{idx:02d}"
        safe_title = sanitize_filename(title)
        filename = f"{chapter_num}_{safe_title}.md"
        
        # Process images
        processed_content, img_count = process_images(
            chapter_content, input_path.parent, images_dir, chapter_num
        )
        report['total_images'] += img_count
        
        # Write chapter file
        chapter_path = output_folder / filename
        with open(chapter_path, 'w', encoding='utf-8') as f:
            f.write(processed_content)
        
        # Skip preamble in TOC if empty
        if idx > 0 or chapter_content.strip():
            toc_lines.append(f"{idx}. [{title}](./{filename})")
            report['chapters'].append({
                'num': chapter_num,
                'title': title,
                'source': str(input_path),
                'chars': len(chapter_content),
            })
    
    # Write TOC file
    toc_path = output_folder / "00_目录.md"
    with open(toc_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(toc_lines))
    
    # Write report
    write_report(output_folder, base_name, report)
    
    return report


def convert_folder(input_path: Path, output_dir: Path) -> dict:
    """Convert a folder of markdown files to standard format."""
    base_name = input_path.name
    output_folder = output_dir / f"{base_name}_markdown"
    output_folder.mkdir(parents=True, exist_ok=True)
    images_dir = output_folder / "images"
    
    report = {
        'input_type': '文件夹',
        'input_path': str(input_path),
        'timestamp': datetime.now().isoformat(),
        'chapters': [],
        'total_images': 0,
        'converted_images': 0,
    }
    
    # Check for index file
    index_file, index_type = find_index_file(input_path)
    
    if index_file and index_type == 'summary':
        # Use SUMMARY.md order
        with open(index_file, 'r', encoding='utf-8') as f:
            summary_content = f.read()
        links = parse_summary_links(summary_content)
        md_files = []
        for title, path in links:
            file_path = input_path / path
            if file_path.exists():
                md_files.append((title, file_path))
    else:
        # Collect all markdown files
        all_files = collect_markdown_files(input_path)
        md_files = [(f.stem, f) for f in all_files]
    
    # Generate chapters
    toc_lines = [f"# {base_name}", "", "> 来源：文件夹转换", "", "## 目录", ""]
    
    for idx, (title, file_path) in enumerate(md_files, start=1):
        chapter_num = f"{idx:02d}"
        safe_title = sanitize_filename(title)
        filename = f"{chapter_num}_{safe_title}.md"
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Process images
        processed_content, img_count = process_images(
            content, file_path.parent, images_dir, chapter_num
        )
        report['total_images'] += img_count
        
        # Write chapter file
        chapter_path = output_folder / filename
        with open(chapter_path, 'w', encoding='utf-8') as f:
            f.write(processed_content)
        
        toc_lines.append(f"{idx}. [{title}](./{filename})")
        report['chapters'].append({
            'num': chapter_num,
            'title': title,
            'source': str(file_path),
            'chars': len(content),
        })
    
    # Write TOC file
    toc_path = output_folder / "00_目录.md"
    with open(toc_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(toc_lines))
    
    # Write report
    write_report(output_folder, base_name, report)
    
    return report


def write_report(output_folder: Path, base_name: str, report: dict):
    """Write processing report."""
    report_lines = [
        "# Markdown 转换报告",
        "",
        "## 基本信息",
        f"- 输入类型：{report['input_type']}",
        f"- 输入路径：{report['input_path']}",
        f"- 转换时间：{report['timestamp']}",
        f"- 章节数量：{len(report['chapters'])}",
        "",
        "## 章节列表",
        "",
        "| 序号 | 章节标题 | 源文件 | 字数 |",
        "|------|----------|--------|------|",
    ]
    
    for ch in report['chapters']:
        source_name = Path(ch['source']).name
        report_lines.append(f"| {ch['num']} | {ch['title']} | {source_name} | {ch['chars']} |")
    
    report_lines.extend([
        "",
        "## 图片处理",
        f"- 处理图片：{report['total_images']} 张",
        f"- 格式转换：{report['converted_images']} 张",
        "",
        "## 备注",
        "- 转换完成",
    ])
    
    report_path = output_folder / f"{base_name}_report.md"
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(report_lines))


def main():
    if len(sys.argv) < 2:
        print("Usage: python markdown_splitter.py <input> [output-dir]")
        print("  input: Markdown file path or folder path")
        print("  output-dir: Optional, defaults to input's parent directory")
        sys.exit(1)
    
    input_path = Path(sys.argv[1]).resolve()
    output_dir = Path(sys.argv[2]).resolve() if len(sys.argv) > 2 else input_path.parent
    
    if not input_path.exists():
        print(f"Error: Input path does not exist: {input_path}")
        sys.exit(1)
    
    if input_path.is_file():
        print(f"Processing single file: {input_path}")
        report = convert_single_file(input_path, output_dir)
    else:
        print(f"Processing folder: {input_path}")
        report = convert_folder(input_path, output_dir)
    
    print(f"\nConversion complete!")
    print(f"  Chapters: {len(report['chapters'])}")
    print(f"  Images: {report['total_images']}")
    print(f"  Output: {output_dir / f'{input_path.stem}_markdown'}")


if __name__ == "__main__":
    main()
