#!/usr/bin/env python3
"""
Merge all markdown files from the Claude API course into standardized format.
Handles duplicate chapter directories and generates table of contents.
"""

import os
import re
from pathlib import Path
from datetime import datetime

# Source and output directories
SOURCE_DIR = Path("books/Building with the Claude API/original")
OUTPUT_DIR = Path("books/Building with the Claude API/processed")

# Chapter order based on README.md
CHAPTER_ORDER = [
    ("01-Introduction", "第1章: 简介"),
    ("02-Anthropic-overview", "第2章: Anthropic 概览"),
    ("03-Accessing-Claude-with-the-API", "第3章: 通过 API 访问 Claude"),
    ("04-Prompt-evaluation", "第4章: 提示词评估"),
    ("05-Prompt-engineering-techniques", "第5章: 提示词工程技术"),
    ("06-Tool-use-with-Claude", "第6章: Claude 工具使用"),
    ("07-Retrieval-Augmented-Generation", "第7章: 检索增强生成"),
    ("08-Features-of-Claude", "第8章: Claude 功能特性"),
    ("09-Model-Context-Protocol", "第9章: 模型上下文协议"),
    # Handle duplicate 10- directories - merge them
    ("10-Anthropic-apps", "第10章: Anthropic 应用"),
    ("10-Anthropic-apps-Claude-Code-and-computer-use", None),  # Skip - duplicate content
    ("11-Agents-and-workflows", "第11章: 智能体与工作流"),
    # 12 and 13 are empty directories, skip them
]

def clean_content(content: str, chapter_num: int, section_num: int, section_title: str) -> str:
    """Clean and standardize markdown content."""
    lines = content.strip().split('\n')

    # Remove the original heading and metadata block
    new_lines = []
    skip_until_hr = False
    found_first_h1 = False

    for i, line in enumerate(lines):
        # Skip the first H1 heading
        if line.startswith('# ') and not found_first_h1:
            found_first_h1 = True
            # Add our numbered heading instead
            new_lines.append(f"## {chapter_num}.{section_num} {section_title}")
            new_lines.append("")
            continue

        # Skip metadata block (lines starting with >)
        if line.startswith('> **课程类型') or line.startswith('> ') or line.startswith('>') :
            if i < 10:  # Only skip metadata at the beginning
                continue

        # Skip the first horizontal rule after metadata
        if line == '---' and i < 15 and not skip_until_hr:
            skip_until_hr = True
            continue

        # Skip "返回目录" link at the end
        if '[返回目录]' in line:
            continue

        new_lines.append(line)

    # Remove trailing empty lines
    while new_lines and new_lines[-1].strip() == '':
        new_lines.pop()

    return '\n'.join(new_lines)

def get_section_title(content: str, filename: str) -> str:
    """Extract section title from content or filename."""
    # Try to find the first H1 heading
    for line in content.split('\n'):
        if line.startswith('# '):
            title = line[2:].strip()
            # Remove any trailing metadata
            if '课程类型' in title:
                continue
            return title

    # Fallback to filename
    name = Path(filename).stem
    # Remove leading numbers and hyphens
    name = re.sub(r'^\d+[-_]?', '', name)
    # Replace hyphens/underscores with spaces
    name = name.replace('-', ' ').replace('_', ' ')
    return name

def is_video_only(content: str) -> bool:
    """Check if the content is video-only (no text content)."""
    # Only match "课程类型**: 视频" where 视频 is followed by newline or end of block
    # This excludes "视频 + 文字" which has text content
    if '本课程仅包含视频内容' in content:
        return True
    # Match "课程类型**: 视频" but not "视频 + 文字" or "视频+文字"
    import re
    if re.search(r'课程类型\*\*:\s*视频\s*$', content, re.MULTILINE):
        return True
    return False

def main():
    start_time = datetime.now()

    # Track statistics
    total_files = 0
    total_lines = 0
    video_files = 0
    code_blocks = 0
    chapters_info = []

    # Create output directory
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Generate table of contents
    toc_lines = [
        "# 构建 Claude API 应用",
        "",
        "> Anthropic 官方课程中文版",
        "> ",
        "> 原课程: https://anthropic.skilljar.com/claude-with-the-anthropic-api",
        "",
        "---",
        "",
        "## 目录",
        "",
    ]

    # Process each chapter
    all_content = []
    chapter_num = 0
    section_num = 0

    for chapter_dir, chapter_title in CHAPTER_ORDER:
        chapter_path = SOURCE_DIR / chapter_dir

        if not chapter_path.exists():
            print(f"Warning: Chapter directory not found: {chapter_path}")
            continue

        if chapter_title is None:
            # This is a duplicate directory to skip
            print(f"Skipping duplicate directory: {chapter_dir}")
            continue

        chapter_num += 1
        chapter_sections = []

        # Add chapter heading to TOC
        toc_lines.append(f"### {chapter_title}")
        toc_lines.append("")

        # Get all markdown files in order
        md_files = sorted(chapter_path.glob("*.md"))

        for md_file in md_files:
            content = md_file.read_text(encoding='utf-8')
            section_num += 1

            section_title = get_section_title(content, md_file.name)

            # Add to TOC
            toc_lines.append(f"- [{chapter_num}.{section_num} {section_title}](./{chapter_num:02d}_{section_num:02d}_{md_file.stem}.md)")

            # Clean and add content
            if is_video_only(content):
                video_files += 1
                cleaned = f"## {chapter_num}.{section_num} {section_title}\n\n> 本节为视频内容，请访问原课程观看。\n> 来源: https://anthropic.skilljar.com/claude-with-the-anthropic-api\n"
            else:
                cleaned = clean_content(content, chapter_num, section_num, section_title)

            # Count code blocks
            code_blocks += cleaned.count('```')

            # Save individual chapter file
            output_file = OUTPUT_DIR / f"{chapter_num:02d}_{section_num:02d}_{md_file.stem}.md"
            output_file.write_text(cleaned + "\n", encoding='utf-8')

            total_files += 1
            total_lines += len(cleaned.split('\n'))
            chapter_sections.append(md_file.name)

            # Add to combined content
            all_content.append(cleaned)

        chapters_info.append({
            'chapter': chapter_num,
            'title': chapter_title,
            'sections': len(chapter_sections)
        })

        toc_lines.append("")

    # Save table of contents
    toc_file = OUTPUT_DIR / "00_目录.md"
    toc_file.write_text('\n'.join(toc_lines), encoding='utf-8')

    # Save combined content
    combined_file = OUTPUT_DIR / "combined_all_chapters.md"
    combined_content = "\n\n---\n\n".join(all_content)
    combined_file.write_text(combined_content, encoding='utf-8')

    # Generate processing report
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()

    report = f"""# 处理报告: Building with the Claude API

## 基本信息

| 项目 | 数值 |
|------|------|
| 处理时间 | {end_time.strftime('%Y-%m-%d %H:%M:%S')} |
| 处理耗时 | {duration:.2f} 秒 |
| 总文件数 | {total_files} |
| 总行数 | {total_lines} |
| 章节数 | {chapter_num} |
| 代码块数 | {code_blocks // 2} |
| 视频文件数 | {video_files} |

## 章节详情

| 章节 | 标题 | 小节数 |
|------|------|--------|
"""

    for info in chapters_info:
        report += f"| 第{info['chapter']}章 | {info['title']} | {info['sections']} |\n"

    report += f"""
## 处理说明

1. **合并处理**: 两个重复的 "10-Anthropic-apps" 目录已合并处理，避免内容重复
2. **空目录跳过**: 12-Final-assessment 和 13-Wrapping-up 目录为空，已跳过
3. **视频内容**: 标记为"视频"类型的课程已添加占位说明
4. **格式标准化**: 统一了章节编号格式，添加了中文章节标题

## 输出文件

- `00_目录.md` - 目录文件
- `combined_all_chapters.md` - 合并后的完整内容
- `XX_YY_章节名.md` - 按章节拆分的独立文件（共 {total_files} 个）

---

*报告生成时间: {end_time.strftime('%Y-%m-%d %H:%M:%S')}*
"""

    report_file = OUTPUT_DIR / "processing_report.md"
    report_file.write_text(report, encoding='utf-8')

    print(f"\n✅ 处理完成!")
    print(f"   - 总文件数: {total_files}")
    print(f"   - 总行数: {total_lines}")
    print(f"   - 章节数: {chapter_num}")
    print(f"   - 视频文件: {video_files}")
    print(f"   - 输出目录: {OUTPUT_DIR}")

if __name__ == "__main__":
    main()