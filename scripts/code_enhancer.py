#!/usr/bin/env python3
"""
Phase 2a: Code Block Enhancer
Adds "【代码说明】" descriptions to code blocks in markdown files.
"""

import os
import re
import sys
from pathlib import Path
from dotenv import load_dotenv
import requests
import time

# Configuration
INPUT_DIR = Path("books/Building with the Claude API/processed")
OUTPUT_DIR = INPUT_DIR / "_enhanced"
API_KEY = os.getenv("ECHO_EPUB_OPEN_API_KEY")
API_BASE = os.getenv("ECHO_EPUB_OPEN_AI_BASE_URL", "https://api.siliconflow.cn/v1")
MODEL = os.getenv("ECHO_EPUB_VLM_MODEL", "Qwen/Qwen2.5-7B-Instruct") # Using text model for code

# Load env
load_dotenv()

def get_llm_description(code: str, context: str = "") -> str:
    """Call LLM to generate code description."""
    if not API_KEY:
        return "（API Key 未配置，跳过描述生成）"

    prompt = f"""请为以下代码片段生成一段简练的功能说明（1-2句话）。
要求：
1. 说明代码的功能目的（这段代码做了什么）
2. 说明关键实现逻辑（怎么实现的）
3. 使用中文
4. 不要使用markdown代码块包裹输出

代码上下文：
{context}

代码片段：
```
{code}
```

请直接输出说明文字："""

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    data = {
        "model": MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 150,
        "temperature": 0.3
    }

    try:
        response = requests.post(
            f"{API_BASE}/chat/completions",
            headers=headers,
            json=data,
            timeout=30
        )
        response.raise_for_status()
        result = response.json()
        return result["choices"][0]["message"]["content"].strip()
    except Exception as e:
        print(f"API Error: {e}")
        return f"（描述生成失败：{e}）"

def process_file(input_path: Path, output_path: Path):
    """Process a single markdown file."""
    print(f"Processing: {input_path.name}")

    content = input_path.read_text(encoding="utf-8")

    # Skip video-only files
    if "本节为视频内容" in content:
        output_path.write_text(content, encoding="utf-8")
        return

    lines = content.split('\n')
    new_lines = []
    i = 0
    code_block_count = 0

    while i < len(lines):
        line = lines[i]

        # Detect wrapped code blocks
        if line.strip().startswith('```'):
            code_block_start = i
            lang = line.strip()[3:].strip()
            code_lines = []
            i += 1

            # Collect code content
            while i < len(lines) and not lines[i].strip().startswith('```'):
                code_lines.append(lines[i])
                i += 1

            # Add code block to output
            new_lines.append(line) # ```lang
            new_lines.extend(code_lines)
            if i < len(lines):
                new_lines.append(lines[i]) # ```

            # Check if we should add description
            code_content = '\n'.join(code_lines)
            # Skip simple blocks (imports, config, <3 lines)
            is_simple = (
                len(code_lines) < 3 or
                (lang == "" and len(code_lines) < 5) or
                all('import' in l or 'from' in l for l in code_lines if l.strip()) or
                all(l.strip().startswith(('#', '//', '/*', '*')) for l in code_lines if l.strip())
            )

            if not is_simple and code_content.strip():
                code_block_count += 1
                # Generate description
                context = '\n'.join(new_lines[-20:-len(code_lines)-2]) # Lines before code
                desc = get_llm_description(code_content, context)

                # Add description block
                new_lines.append("")
                new_lines.append(f"> 【代码说明】{desc}")
        else:
            new_lines.append(line)

        i += 1

    output_path.write_text('\n'.join(new_lines), encoding="utf-8")
    print(f"  -> Added descriptions for {code_block_count} code blocks.")

def main():
    print("Phase 2a: Code Block Enhancer")
    print("=" * 40)

    if not API_KEY:
        print("Warning: ECHO_EPUB_OPEN_API_KEY not set. Descriptions will be skipped.")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    files = sorted(INPUT_DIR.glob("*.md"))
    # Skip non-chapter files like TOC and report
    chapter_files = [f for f in files if not f.name.startswith('00_') and not f.name.startswith('processing_')]

    print(f"Found {len(chapter_files)} chapter files to process.")

    start_time = time.time()

    for f in chapter_files:
        out_file = OUTPUT_DIR / f.name
        process_file(f, out_file)

    duration = time.time() - start_time
    print(f"\n✅ Phase 2a Complete!")
    print(f"   Processed {len(chapter_files)} files in {duration:.2f}s")
    print(f"   Output: {OUTPUT_DIR}")

if __name__ == "__main__":
    main()