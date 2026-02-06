#!/usr/bin/env python3
"""
Audioread Processor - Transform Markdown to audio-friendly format.

Usage:
    python audioread_processor.py <input> [--no-translate] [--no-intro] [--no-summary]
    
    input: Markdown file or folder path (standard format from converters)
"""

import os
import sys
import re
from datetime import datetime
from pathlib import Path

# Import processing modules
try:
    from image_descriptor import describe_image, should_skip_image
except ImportError:
    describe_image = None
    should_skip_image = None

try:
    from translate_content import translate_paragraph, is_non_chinese
except ImportError:
    translate_paragraph = None
    is_non_chinese = None

try:
    from audio_rewriter import rewrite_for_audio
except ImportError:
    rewrite_for_audio = None

try:
    from technical_term_detector import detect_terms, build_glossary
except ImportError:
    detect_terms = None
    build_glossary = None

try:
    from text_optimizer import optimize_text
except ImportError:
    optimize_text = None


class AudioreadProcessor:
    """Process Markdown files for audio-friendly reading."""
    
    def __init__(self, config: dict = None):
        self.config = config or {}
        self.stats = {
            'images_described': 0,
            'paragraphs_translated': 0,
            'tables_converted': 0,
            'lists_converted': 0,
            'chapters_with_intro': 0,
            'chapters_with_summary': 0,
        }
        self.glossary = {}
    
    def process_folder(self, folder_path: Path) -> dict:
        """Process a standard Markdown folder."""
        folder_path = Path(folder_path)
        
        # Find all chapter files
        chapter_files = sorted([
            f for f in folder_path.glob('*.md')
            if f.name != '00_目录.md' 
            and not f.name.endswith('_report.md')
            and not f.name == 'glossary.md'
        ])
        
        print(f"Found {len(chapter_files)} chapter files")
        
        for chapter_file in chapter_files:
            print(f"Processing: {chapter_file.name}")
            self.process_chapter(chapter_file)
        
        # Generate glossary
        if self.glossary:
            self.write_glossary(folder_path / 'glossary.md')
        
        # Update report
        self.update_report(folder_path)
        
        return self.stats
    
    def process_chapter(self, file_path: Path):
        """Process a single chapter file."""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Step 1: Process images
        content = self.process_images(content, file_path.parent)
        
        # Step 2: Translate non-Chinese content
        if self.config.get('translate', True):
            content = self.translate_content(content)
        
        # Step 3: Convert tables to audio format
        content = self.convert_tables(content)
        
        # Step 4: Convert lists to audio format
        content = self.convert_lists(content)
        
        # Step 5: Add chapter intro and summary
        if self.config.get('add_intro', True):
            content = self.add_chapter_intro(content)
        if self.config.get('add_summary', True):
            content = self.add_chapter_summary(content)
        
        # Step 6: Optimize sentences
        content = self.optimize_sentences(content)
        
        # Write back
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
    
    def process_images(self, content: str, base_path: Path) -> str:
        """Add descriptions to images."""
        if describe_image is None:
            # Fallback: add placeholder descriptions
            return self.add_placeholder_image_descriptions(content)
        
        def replace_image(match):
            full_match = match.group(0)
            alt_text = match.group(1)
            img_path = match.group(2)
            
            # Skip URLs
            if img_path.startswith(('http://', 'https://')):
                return full_match
            
            # Check if should skip
            if should_skip_image and should_skip_image(img_path, alt_text):
                return full_match
            
            # Generate description
            try:
                full_path = base_path / img_path if not img_path.startswith('/') else Path(img_path)
                description = describe_image(str(full_path), alt_text)
                if description:
                    self.stats['images_described'] += 1
                    return f"{full_match}\n\n{description}"
            except Exception as e:
                print(f"Warning: Failed to describe image {img_path}: {e}")
            
            return full_match
        
        pattern = r'!\[([^\]]*)\]\(([^)]+)\)'
        return re.sub(pattern, replace_image, content)
    
    def add_placeholder_image_descriptions(self, content: str) -> str:
        """Add placeholder descriptions when AI is not available."""
        
        def replace_image(match):
            full_match = match.group(0)
            alt_text = match.group(1)
            img_path = match.group(2)
            
            # Skip certain image types
            skip_keywords = ['二维码', 'qr', 'logo', 'icon', '表情', 'emoji', '封面', 'cover']
            combined = (alt_text + img_path).lower()
            if any(kw in combined for kw in skip_keywords):
                return full_match
            
            # Detect image type
            img_type = "示意图"
            if any(kw in combined for kw in ['架构', 'arch', 'structure']):
                img_type = "架构图"
            elif any(kw in combined for kw in ['流程', 'flow', 'process']):
                img_type = "流程图"
            elif any(kw in combined for kw in ['chart', 'graph', '图表', '趋势']):
                img_type = "数据图表"
            elif any(kw in combined for kw in ['截图', 'screen', 'ui']):
                img_type = "界面截图"
            
            description = f"""
> **图片说明**：这是一张{img_type}。
> **核心内容**：{alt_text or '展示相关内容'}
> **关键元素**：请查看原图片获取详细信息
>
> **要点总结**：
> - 第一，该图片为重要示意图，建议查看原图。
> - 第二，图片包含关键信息，有助于理解正文内容。
> - 第三，AI图片描述功能暂未启用或分析失败。
"""
            self.stats['images_described'] += 1
            return f"{full_match}\n{description}"
        
        pattern = r'!\[([^\]]*)\]\(([^)]+)\)'
        return re.sub(pattern, replace_image, content)
    
    def translate_content(self, content: str) -> str:
        """Translate non-Chinese paragraphs."""
        if translate_paragraph is None or is_non_chinese is None:
            return content
        
        paragraphs = content.split('\n\n')
        translated = []
        
        for para in paragraphs:
            if is_non_chinese(para) and len(para.strip()) > 50:
                try:
                    translated_para = translate_paragraph(para)
                    translated.append(translated_para)
                    self.stats['paragraphs_translated'] += 1
                except Exception:
                    translated.append(para)
            else:
                translated.append(para)
        
        return '\n\n'.join(translated)
    
    def convert_tables(self, content: str) -> str:
        """Convert tables to audio-friendly format."""
        # Find markdown tables
        table_pattern = r'(\|[^\n]+\|\n\|[-:| ]+\|\n(?:\|[^\n]+\|\n)+)'
        
        def replace_table(match):
            table = match.group(0)
            lines = table.strip().split('\n')
            
            if len(lines) < 3:
                return table
            
            # Parse header
            headers = [h.strip() for h in lines[0].split('|')[1:-1]]
            
            # Parse rows
            rows = []
            for line in lines[2:]:
                cells = [c.strip() for c in line.split('|')[1:-1]]
                rows.append(cells)
            
            # Build audio-friendly description
            desc_parts = ["\n**表格内容说明**：\n"]
            
            for row in rows:
                for i, cell in enumerate(row):
                    if i < len(headers) and cell:
                        desc_parts.append(f"关于{headers[i]}：{cell}。\n")
            
            desc_parts.append("\n> 原始表格数据见上。\n")
            
            self.stats['tables_converted'] += 1
            return table + '\n' + ''.join(desc_parts)
        
        return re.sub(table_pattern, replace_table, content)
    
    def convert_lists(self, content: str) -> str:
        """Convert lists to audio-friendly format."""
        # Find unordered lists (3+ items)
        list_pattern = r'((?:^[-*+]\s+.+\n){3,})'
        
        def replace_list(match):
            list_text = match.group(0)
            items = re.findall(r'^[-*+]\s+(.+)$', list_text, re.MULTILINE)
            
            if len(items) < 3:
                return list_text
            
            ordinal_words = ['第一', '第二', '第三', '第四', '第五', '第六', '第七', '第八', '第九', '第十']
            audio_items = []
            
            for i, item in enumerate(items):
                if i < len(ordinal_words):
                    audio_items.append(f"{ordinal_words[i]}，{item}。")
            
            self.stats['lists_converted'] += 1
            return list_text + f"\n以下是{len(items)}个要点：\n" + '\n'.join(audio_items) + '\n'
        
        return re.sub(list_pattern, replace_list, content, flags=re.MULTILINE)
    
    def add_chapter_intro(self, content: str) -> str:
        """Add chapter introduction."""
        # Extract title
        title_match = re.match(r'^#\s+(.+)$', content, re.MULTILINE)
        if not title_match:
            return content
        
        title = title_match.group(1)
        
        # Generate simple intro
        intro = f"\n\n本章将介绍"{title}"相关内容。让我们开始学习。\n"
        
        # Insert after title
        self.stats['chapters_with_intro'] += 1
        return re.sub(r'^(#\s+.+)$', r'\1' + intro, content, count=1, flags=re.MULTILINE)
    
    def add_chapter_summary(self, content: str) -> str:
        """Add chapter summary."""
        summary = "\n\n---\n\n**本章小结**：以上就是本章的主要内容。建议读者回顾要点，加深理解。\n"
        self.stats['chapters_with_summary'] += 1
        return content + summary
    
    def optimize_sentences(self, content: str) -> str:
        """Optimize sentence structure for listening."""
        if optimize_text:
            return optimize_text(content)
        return content
    
    def write_glossary(self, output_path: Path):
        """Write glossary file."""
        if not self.glossary:
            return
        
        lines = ["# 术语表", "", "| 术语 | 原文 | 解释 |", "|------|------|------|"]
        for term, (original, explanation) in self.glossary.items():
            lines.append(f"| {term} | {original} | {explanation} |")
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
    
    def update_report(self, folder_path: Path):
        """Update processing report."""
        # Find existing report
        report_files = list(folder_path.glob('*_report.md'))
        if not report_files:
            return
        
        report_path = report_files[0]
        
        with open(report_path, 'r', encoding='utf-8') as f:
            report_content = f.read()
        
        # Add audioread section
        audioread_section = f"""

## Audioread 处理

- 处理时间：{datetime.now().isoformat()}
- 图片描述：{self.stats['images_described']} 张
- 翻译段落：{self.stats['paragraphs_translated']} 段
- 表格转换：{self.stats['tables_converted']} 个
- 列表转换：{self.stats['lists_converted']} 个
- 章节导语：{self.stats['chapters_with_intro']} 章
- 章节总结：{self.stats['chapters_with_summary']} 章
"""
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report_content + audioread_section)


def main():
    if len(sys.argv) < 2:
        print("Usage: python audioread_processor.py <input> [options]")
        print("  input: Markdown file or folder path")
        print("  --no-translate: Skip translation")
        print("  --no-intro: Skip chapter introductions")
        print("  --no-summary: Skip chapter summaries")
        sys.exit(1)
    
    input_path = Path(sys.argv[1]).resolve()
    
    config = {
        'translate': '--no-translate' not in sys.argv,
        'add_intro': '--no-intro' not in sys.argv,
        'add_summary': '--no-summary' not in sys.argv,
    }
    
    if not input_path.exists():
        print(f"Error: Input path does not exist: {input_path}")
        sys.exit(1)
    
    processor = AudioreadProcessor(config)
    
    if input_path.is_file():
        print(f"Processing single file: {input_path}")
        processor.process_chapter(input_path)
    else:
        print(f"Processing folder: {input_path}")
        processor.process_folder(input_path)
    
    print("\nProcessing complete!")
    print(f"  Images described: {processor.stats['images_described']}")
    print(f"  Paragraphs translated: {processor.stats['paragraphs_translated']}")
    print(f"  Tables converted: {processor.stats['tables_converted']}")
    print(f"  Lists converted: {processor.stats['lists_converted']}")


if __name__ == "__main__":
    main()
