#!/usr/bin/env python3
"""
Phase 2c: Markdown Translator
Translates non-Chinese content to Simplified Chinese.
"""

import os
import re
import sys
from pathlib import Path
from dotenv import load_dotenv
import requests
import time
import json

# Configuration
INPUT_DIR = Path("books/Building with the Claude API/processed/_cleaned")
OUTPUT_DIR = Path("books/Building with the Claude API/processed/_translated")
API_KEY = os.getenv("ECHO_EPUB_OPEN_API_KEY")
API_BASE = os.getenv("ECHO_EPUB_OPEN_AI_BASE_URL", "https://api.siliconflow.cn/v1")
MODEL = os.getenv("ECHO_EPUB_VLM_MODEL", "Qwen/Qwen2.5-7B-Instruct")

# Load env
load_dotenv()

def is_chinese(text: str) -> bool:
    """Check if text contains Chinese characters."""
    chinese_chars = re.findall(r'[\u4e00-\u9fff]', text)
    return len(chinese_chars) > len(text) * 0.3

def translate_text(text: str) -> str:
    """Translate text to Chinese using LLM."""
    if not API_KEY:
        return text

    # Skip if already mostly Chinese
    if is_chinese(text):
        return text

    prompt = f"""请将以下英文内容翻译为简体中文。
规则：
1. 保持专业/学术语气
2. 技术术语（API、SDK、JSON、Python等）保持英文原文
3. 产品名/公司名保持英文（Google、OpenAI等）
4. 不要翻译代码块、变量名、函数名
5. 不要添加任何解释或注释
6. 保持原文的段落结构

原文：
{text}

翻译："""

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    data = {
        "model": MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 4000,
        "temperature": 0.3
    }

    try:
        response = requests.post(
            f"{API_BASE}/chat/completions",
            headers=headers,
            json=data,
            timeout=60
        )
        response.raise_for_status()
        result = response.json()
        return result["choices"][0]["message"]["content"].strip()
    except Exception as e:
        print(f"  Translation error: {e}")
        return text

def extract_prose_blocks(content: str) -> list:
    """Extract prose blocks that need translation, preserving code blocks."""
    blocks = []
    lines = content.split('\n')
    current_block = []
    in_code_block = False
    block_type = "prose"  # prose, code, quote, list

    i = 0
    while i < len(lines):
        line = lines[i]

        # Code block detection
        if line.strip().startswith('```'):
            if current_block:
                blocks.append(('\n'.join(current_block), block_type))
                current_block = []
            in_code_block = not in_code_block
            block_type = "code"
            current_block.append(line)
        elif in_code_block:
            current_block.append(line)
        # Quote block with Chinese marker (don't translate)
        elif line.strip().startswith('> 【') and ('图片描述' in line or '代码说明' in line or '表格说明' in line):
            if current_block:
                blocks.append(('\n'.join(current_block), block_type))
                current_block = []
            block_type = "chinese_quote"
            current_block.append(line)
        # Regular quote
        elif line.strip().startswith('>'):
            if current_block and block_type != "quote":
                blocks.append(('\n'.join(current_block), block_type))
                current_block = []
            block_type = "quote"
            current_block.append(line)
        # List item
        elif re.match(r'^\s*[-*+]\s', line) or re.match(r'^\s*\d+\.\s', line):
            if current_block and block_type != "list":
                blocks.append(('\n'.join(current_block), block_type))
                current_block = []
            block_type = "list"
            current_block.append(line)
        # Empty line
        elif line.strip() == '':
            if current_block:
                blocks.append(('\n'.join(current_block), block_type))
                current_block = []
            blocks.append((line, "empty"))
            block_type = "prose"
        # Heading
        elif line.startswith('#'):
            if current_block:
                blocks.append(('\n'.join(current_block), block_type))
                current_block = []
            block_type = "heading"
            current_block.append(line)
        else:
            if current_block and block_type not in ("prose", "heading", "list", "quote"):
                blocks.append(('\n'.join(current_block), block_type))
                current_block = []
            block_type = "prose"
            current_block.append(line)

        i += 1

    if current_block:
        blocks.append(('\n'.join(current_block), block_type))

    return blocks

def process_file(input_path: Path, output_path: Path) -> dict:
    """Process a single markdown file."""
    print(f"Processing: {input_path.name}")

    content = input_path.read_text(encoding="utf-8")

    # Skip video-only files
    if "本节为视频内容" in content:
        output_path.write_text(content, encoding="utf-8")
        return {"translated": 0, "skipped": 1}

    # Check if already Chinese
    chinese_ratio = len(re.findall(r'[\u4e00-\u9fff]', content)) / max(len(content), 1)
    if chinese_ratio > 0.5:
        print(f"  -> Already Chinese ({chinese_ratio:.0%}), skipping")
        # Fix image path and copy
        content = content.replace('./images/', '../images/')
        output_path.write_text(content, encoding="utf-8")
        return {"translated": 0, "skipped": 1}

    # Extract blocks
    blocks = extract_prose_blocks(content)

    # Translate prose blocks
    translated_blocks = []
    translated_count = 0

    for block_text, block_type in blocks:
        if block_type == "prose" and not is_chinese(block_text):
            translated = translate_text(block_text)
            translated_blocks.append(translated)
            translated_count += 1
        elif block_type == "heading" and not is_chinese(block_text):
            # Translate heading but preserve # marks
            match = re.match(r'^(#+)\s+(.+)$', block_text)
            if match:
                hashes, text = match.groups()
                translated_text = translate_text(text)
                translated_blocks.append(f"{hashes} {translated_text}")
                translated_count += 1
            else:
                translated_blocks.append(block_text)
        elif block_type == "list" and not is_chinese(block_text):
            # Translate list items
            translated = translate_text(block_text)
            translated_blocks.append(translated)
            translated_count += 1
        elif block_type == "quote" and not is_chinese(block_text) and '【' not in block_text:
            # Translate quote content
            translated = translate_text(block_text)
            translated_blocks.append(translated)
            translated_count += 1
        else:
            translated_blocks.append(block_text)

    # Join and fix image paths
    result = '\n'.join(translated_blocks)
    result = result.replace('./images/', '../images/')

    output_path.write_text(result, encoding="utf-8")
    print(f"  -> Translated {translated_count} blocks")
    return {"translated": translated_count, "skipped": 0}

def main():
    print("Phase 2c: Markdown Translator")
    print("=" * 40)

    if not API_KEY:
        print("Error: ECHO_EPUB_OPEN_API_KEY not set.")
        sys.exit(1)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    files = sorted(INPUT_DIR.glob("*.md"))
    # Skip report files
    chapter_files = [f for f in files if not f.name.endswith('_report.md')]

    print(f"Found {len(chapter_files)} chapter files to process.")

    start_time = time.time()
    total_stats = {"translated": 0, "skipped": 0}

    for f in chapter_files:
        stats = process_file(f, OUTPUT_DIR / f.name)
        total_stats["translated"] += stats["translated"]
        total_stats["skipped"] += stats["skipped"]

    duration = time.time() - start_time

    # Generate report
    report = f"""# 翻译处理报告

## 处理统计

- 处理时间：{time.strftime('%Y-%m-%d %H:%M:%S')}
- 处理章节：{len(chapter_files)} 章
- 翻译块数：{total_stats['translated']} 块
- 跳过文件：{total_stats['skipped']} 个（已为中文）
- 处理耗时：{duration:.2f} 秒

## 处理说明

1. **语言检测**：统计中文字符占比，> 50% 则跳过翻译
2. **保留内容**：代码块、变量名、技术术语、URL 等保持原文
3. **翻译内容**：英文散文段落、标题、列表项翻译为简体中文
4. **图片路径修正**：`./images/` → `../images/`

---

*报告生成时间: {time.strftime('%Y-%m-%d %H:%M:%S')}*
"""

    (OUTPUT_DIR / "translator_report.md").write_text(report, encoding="utf-8")

    print(f"\n✅ Phase 2c Complete!")
    print(f"   Processed {len(chapter_files)} files in {duration:.2f}s")
    print(f"   Translated: {total_stats['translated']} blocks")
    print(f"   Skipped (already Chinese): {total_stats['skipped']} files")
    print(f"   Output: {OUTPUT_DIR}")

if __name__ == "__main__":
    main()