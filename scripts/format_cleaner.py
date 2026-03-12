#!/usr/bin/env python3
"""
Phase 2b: Markdown Format Cleaner
Cleans formatting issues in markdown files.
"""

import re
from pathlib import Path
from datetime import datetime

# Configuration
INPUT_DIR = Path("books/Building with the Claude API/processed/_enhanced")
OUTPUT_DIR = Path("books/Building with the Claude API/processed/_cleaned")

def clean_file(content: str) -> tuple[str, dict]:
    """Clean formatting issues and return stats."""
    stats = {
        "blank_lines_compressed": 0,
        "trailing_whitespace": 0,
        "empty_paragraphs": 0,
        "code_blocks_fixed": 0,
        "heading_fixed": 0,
        "list_fixed": 0,
    }

    lines = content.split('\n')
    new_lines = []
    i = 0

    while i < len(lines):
        line = lines[i]

        # 1. Clean trailing whitespace
        if line.rstrip() != line:
            line = line.rstrip()
            stats["trailing_whitespace"] += 1

        # 2. Compress multiple blank lines
        if line.strip() == '':
            blank_count = 0
            while i < len(lines) and lines[i].strip() == '':
                blank_count += 1
                i += 1
            # Keep at most 2 blank lines
            if blank_count > 2:
                stats["blank_lines_compressed"] += blank_count - 2
                blank_count = 2
            new_lines.extend([''] * blank_count)
            continue

        # 3. Fix heading format (ensure space after #)
        if line.startswith('#'):
            match = re.match(r'^(#{1,6})([^\s#])', line)
            if match:
                line = match.group(1) + ' ' + line[match.end()-1:]
                stats["heading_fixed"] += 1

        # 4. Unify list markers
        if re.match(r'^[\*\+]\s', line):
            line = '-' + line[1:]
            stats["list_fixed"] += 1

        # 5. Handle code blocks - ensure blank lines before/after
        if line.strip().startswith('```'):
            # Check if previous line is blank
            if new_lines and new_lines[-1].strip() != '':
                new_lines.append('')
                stats["code_blocks_fixed"] += 1

        new_lines.append(line)
        i += 1

    # Remove leading blank lines
    while new_lines and new_lines[0].strip() == '':
        new_lines.pop(0)
        stats["empty_paragraphs"] += 1

    # Ensure single trailing newline
    while len(new_lines) > 1 and new_lines[-1].strip() == '':
        new_lines.pop()
        stats["empty_paragraphs"] += 1

    # Join and add final newline
    result = '\n'.join(new_lines)
    if not result.endswith('\n'):
        result += '\n'

    return result, stats

def process_file(input_path: Path, output_path: Path) -> dict:
    """Process a single markdown file."""
    content = input_path.read_text(encoding="utf-8")
    cleaned, stats = clean_file(content)

    # Fix image paths for subdirectory output
    cleaned = cleaned.replace('./images/', '../images/')

    output_path.write_text(cleaned, encoding="utf-8")
    return stats

def main():
    print("Phase 2b: Markdown Format Cleaner")
    print("=" * 40)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    files = sorted(INPUT_DIR.glob("*.md"))
    # Skip combined file
    chapter_files = [f for f in files if not f.name.startswith('combined_')]

    total_stats = {
        "blank_lines_compressed": 0,
        "trailing_whitespace": 0,
        "empty_paragraphs": 0,
        "code_blocks_fixed": 0,
        "heading_fixed": 0,
        "list_fixed": 0,
    }

    print(f"Found {len(chapter_files)} chapter files to process.")

    for f in chapter_files:
        stats = process_file(f, OUTPUT_DIR / f.name)
        for k, v in stats.items():
            total_stats[k] += v

    # Generate report
    report_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    report = f"""# Format Cleaner 处理报告

## 处理统计

- 处理时间：{report_time}
- 处理章节：{len(chapter_files)} 章
- 空行压缩：{total_stats['blank_lines_compressed']} 处
- 行尾清理：{total_stats['trailing_whitespace']} 处
- 空白段落删除：{total_stats['empty_paragraphs']} 处
- 代码块格式修复：{total_stats['code_blocks_fixed']} 处
- 标题格式修复：{total_stats['heading_fixed']} 处
- 列表格式修复：{total_stats['list_fixed']} 处

## 处理说明

1. **空行规范化**：连续 3 行及以上空行压缩为 2 行
2. **行尾清理**：删除行尾多余空格和制表符
3. **标题格式**：确保 `#` 后有空格
4. **列表格式**：统一使用 `-` 作为无序列表标记
5. **代码块格式**：确保代码块前后有空行
6. **图片路径修正**：`./images/` → `../images/`

---

*报告生成时间: {report_time}*
"""

    (OUTPUT_DIR / "format_cleaner_report.md").write_text(report, encoding="utf-8")

    print(f"\n✅ Phase 2b Complete!")
    print(f"   Processed {len(chapter_files)} files")
    print(f"   Output: {OUTPUT_DIR}")
    for k, v in total_stats.items():
        if v > 0:
            print(f"   - {k}: {v}")

if __name__ == "__main__":
    main()