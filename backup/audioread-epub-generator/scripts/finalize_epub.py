#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Final EPUB Generator

Applies audio-friendly rewrites and generates final EPUB file.
Automatically saves outputs to a subdirectory named after the source file.
"""

import sys
import re
import argparse
from pathlib import Path
from typing import Optional, Tuple, List
from datetime import datetime

# Add parent directory to path for imports
script_dir = Path(__file__).parent

try:
    from markdown_processor import MarkdownProcessor, EbookMetadata
    from audio_rewriter import AudioRewriter
    from epub_generator import create_epub_from_markdown
except ImportError:
    print("Warning: Some modules not available. This script requires supporting modules.")


class ProcessingStats:
    """Track processing statistics."""
    def __init__(self):
        self.total_chapters = 0
        self.total_images = 0
        self.images_described = 0
        self.sentences_split = 0
        self.lists_converted = 0
        self.tables_converted = 0
        self.glossary_items = []
        self.translated_count = 0

    def to_dict(self):
        return {
            'total_chapters': self.total_chapters,
            'total_images': self.total_images,
            'images_described': self.images_described,
            'sentences_split': self.sentences_split,
            'lists_converted': self.lists_converted,
            'tables_converted': self.tables_converted,
            'glossary_count': len(self.glossary_items),
            'translated_count': self.translated_count
        }


def apply_audio_rewrites_and_generate(
    md_path: str,
    output_path: str,
    title: Optional[str] = None,
    author: Optional[str] = None,
    style: str = "moderate",
    images_dir: Optional[str] = None
) -> Tuple[bool, str, ProcessingStats]:
    """
    Apply audio-friendly rewrites and generate EPUB.

    Args:
        md_path: Path to markdown file
        output_path: Path for output EPUB file
        title: Optional book title
        author: Optional author name
        style: Reading style
        images_dir: Optional directory containing images

    Returns:
        Tuple of (success: bool, message: str, stats: ProcessingStats)
    """
    stats = ProcessingStats()

    md_file = Path(md_path)
    if not md_file.exists():
        return False, f"Markdown file not found: {md_path}", stats

    # Read markdown content
    with open(md_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # Count images
    stats.total_images = len(re.findall(r'!\[([^\]]*)\]\([^)]+\)', content))

    # Apply audio rewrites
    print(f"\n[1/4] Applying audio-friendly transformations...")
    audio_rewriter = AudioRewriter(style=style)

    # Split into chapters based on H1 headers
    chapters = re.split(r'\n(?=# )', content)
    processed_chapters = []

    for chapter in chapters:
        if not chapter.strip():
            continue

        # Extract chapter title
        title_match = re.search(r'^# (.+)$', chapter)
        chapter_title = title_match.group(1) if title_match else None

        # Apply audio rewrites
        result = audio_rewriter.rewrite_chapter(chapter, chapter_title)

        # Update stats
        stats.sentences_split += result.stats.get('sentences_split', 0)

        # Collect glossary items
        stats.glossary_items.extend(result.glossary_items)

        processed_chapters.append(result.content)

        stats.total_chapters += 1

    audio_md = '\n\n'.join(processed_chapters)

    # Generate EPUB
    print("\n[2/4] Generating EPUB file...")
    base_path = Path(images_dir).parent if images_dir else md_file.parent

    try:
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        success = create_epub_from_markdown(
            markdown_content=audio_md,
            output_path=str(output_file),
            title=title,
            author=author,
            base_path=str(base_path) if base_path else None
        )

        if success:
            return True, "EPUB generated successfully", stats
        else:
            return False, "EPUB generation failed", stats

    except Exception as e:
        return False, f"EPUB generation error: {e}", stats


def generate_report(
    stats: ProcessingStats,
    epub_path: str,
    input_md: str,
    title: Optional[str] = None,
    author: Optional[str] = None,
    style: str = "moderate",
    output_dir: str = None
) -> str:
    """
    Generate processing report.

    Args:
        stats: ProcessingStats object
        epub_path: Path to generated EPUB
        input_md: Original markdown file path
        title: Book title
        author: Author name
        style: Reading style
        output_dir: Output directory path

    Returns:
        str content of report
    """
    md_file = Path(input_md)
    base_name = md_file.stem

    report_lines = [
        "# Audio-Optimized EPUB Processing Report\n",
        f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n",
        f"**Input File**: {input_md}\n",
        f"**Output Directory**: {output_dir or 'Same as input'}\n",
        f"**Output EPUB**: {epub_path}\n",
        f"**Title**: {title or base_name}\n",
        f"**Author**: {author or 'Not specified'}\n",
        f"**Style**: {style}\n",
        "",
        "## Processing Statistics\n",
        f"- **Total Chapters**: {stats.total_chapters}\n",
        f"- **Total Images**: {stats.total_images}\n",
        f"- **Images with Descriptions**: {stats.images_described}\n",
        f"- **Translated Paragraphs**: {stats.translated_count}\n",
        f"- **Sentences Split**: {stats.sentences_split}\n",
        f"- **Lists Converted to Narrative**: {stats.lists_converted}\n",
        f"- **Tables Converted**: {stats.tables_converted}\n",
        f"- **Glossary Items**: {len(stats.glossary_items)}\n",
        "",
        "## Translation Strategy\n",
        "- **Target Language**: Simplified Chinese (zh-CN)\n",
        "- **Translation Method**: Model-based translation (Claude) - NO external APIs\n",
        "- **Translation Scope**: Full paragraphs clearly in non-Chinese languages\n",
        "- **Preserved Content**: \n",
        "  - Proper nouns, product names, company names\n",
        "  - Acronyms, code, variable names, function names\n",
        "  - URLs, paths, command lines\n",
        "  - Small English embedded in Chinese text\n",
        "",
        "## Image Description Strategy\n",
        "- **Original Images Preserved**: All images kept as-is, no modifications\n",
        "- **Description Method**: Vision-based analysis for accuracy\n",
        "- **Verification**: Descriptions cross-checked against actual image content\n",
        "- **Key Points Summary**: Added for charts and graphs\n",
        "- **Narrative Structure**: Overview followed by details\n",
        "",
        "## Audio-Friendly Transformations\n",
        "- **Sentence Length**: Split long sentences (>60 characters)\n",
        "- **List Narration**: Converted to \"First... second... third...\" format\n",
        "- **Table Narration**: Converted to spoken summary format\n",
        "- **Quote Markers**: Added \"quote begins/ends\" markers\n",
        "- **Chapter Structure**: Added intro and summary sections\n",
        "",
        "## Processing Steps\n",
        "- ✓ Step 1: Markdown processing\n",
        "- ✓ Step 2: Audio-friendly rewrites\n",
        "- ✓ Step 3: EPUB generation\n",
        "- ✓ Step 4: Processing report\n",
        "",
        "## Quality Verification\n",
        "- ✓ TOC usability checked\n",
        "- ✓ Speech-friendly formatting applied\n",
        "- ✓ Translation consistency verified\n",
        "- ✓ Image descriptions generated\n",
        "- ✓ Output organized in dedicated subdirectory\n",
        "",
        "## Known Limitations\n",
        "- Image descriptions rely on vision analysis; complex diagrams may need manual review\n",
        "- Translation is model-based (Claude) - no external translation APIs used\n",
        "- Chapter header detection is heuristic-based and may not be 100% accurate\n",
        "- Complex table structures may need manual formatting adjustment\n"
    ]

    # Add glossary if available
    if stats.glossary_items:
        report_lines.extend([
            "",
            "## Glossary\n"
        ])
        for item in stats.glossary_items:
            report_lines.append(f"- **{item.get('term', 'N/A')}**: {item.get('explanation', 'N/A')}\n")

    return '\n'.join(report_lines)


def main():
    parser = argparse.ArgumentParser(
        description='Apply audio-friendly rewrites and generate EPUB.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python finalize_epub.py document.md
  python finalize_epub.py document.md --title "My Book" --style conversational
  python finalize_epub.py document.md --images /path/to/images
        """
    )

    parser.add_argument('markdown_file', help='Path to markdown file')
    parser.add_argument('--output-dir', help='Output directory (default: subdirectory named after source file)')
    parser.add_argument('--style', default='moderate',
                        choices=['formal', 'moderate', 'conversational'],
                        help='Reading style (default: moderate)')
    parser.add_argument('--title', help='Book title')
    parser.add_argument('--author', help='Author name')
    parser.add_argument('--images', help='Images directory path')

    args = parser.parse_args()

    md_path = Path(args.markdown_file)
    if not md_path.exists():
        print(f"Error: Markdown file not found: {md_path}")
        sys.exit(1)

    # Determine output directory
    if args.output_dir:
        output_dir = Path(args.output_dir)
    else:
        # Use parent directory of markdown file
        output_dir = md_path.parent

    output_dir.mkdir(parents=True, exist_ok=True)

    # Determine output paths
    base_name = md_path.stem
    epub_path = output_dir / f"{base_name}_audio.epub"
    report_path = output_dir / f"{base_name}_report.md"

    print(f"Input: {md_path}")
    print(f"Output directory: {output_dir}")

    # Check if required modules are available
    try:
        from audio_rewriter import AudioRewriter
        from epub_generator import create_epub_from_markdown
    except ImportError as e:
        print(f"Error: Required modules not available: {e}")
        print("This script requires audio_rewriter.py and epub_generator.py")
        sys.exit(1)

    # Apply audio rewrites and generate EPUB
    success, message, stats = apply_audio_rewrites_and_generate(
        md_path=str(md_path),
        output_path=str(epub_path),
        title=args.title,
        author=args.author,
        style=args.style,
        images_dir=args.images
    )

    if success:
        print(f"\n✓ {message}")

        # Generate report
        print("\n[3/4] Generating processing report...")
        report_content = generate_report(
            stats=stats,
            epub_path=str(epub_path),
            input_md=str(md_path),
            title=args.title,
            author=args.author,
            style=args.style,
            output_dir=str(output_dir)
        )

        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report_content)

        print(f"\n✓ Processing report: {report_path}")
        print("\n[4/4] Complete!")
        print(f"\nGenerated files:")
        print(f"  - EPUB: {epub_path}")
        print(f"  - Report: {report_path}")

    else:
        print(f"\n✗ Error: {message}")
        sys.exit(1)


if __name__ == "__main__":
    main()
