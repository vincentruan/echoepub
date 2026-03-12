#!/usr/bin/env python3
"""
Phase 3: Generate EPUB from translated markdown files.
"""

import sys
from pathlib import Path
from datetime import datetime

# Add skill scripts to path
skill_path = Path(__file__).parent.parent / ".claude/skills/markdown-to-epub/scripts"
sys.path.insert(0, str(skill_path.resolve()))

from epub_generator import create_epub_from_markdown, EPUBGenerator, EbookMetadata
from markdown_processor import MarkdownProcessor

# Configuration
INPUT_DIR = Path("books/Building with the Claude API/processed/_translated")
OUTPUT_PATH = Path("books/Building with the Claude API/构建Claude API应用.epub")
TITLE = "构建 Claude API 应用"
AUTHOR = "Anthropic"
LANGUAGE = "zh-CN"

def main():
    print("Phase 3: Generate EPUB")
    print("=" * 40)

    # Read all translated markdown files
    files = sorted(INPUT_DIR.glob("*.md"))
    # Skip report files
    chapter_files = [f for f in files if not f.name.endswith('_report.md')]

    print(f"Found {len(chapter_files)} chapter files")

    # Merge all chapters
    chapters_content = []
    for f in chapter_files:
        content = f.read_text(encoding="utf-8")
        chapters_content.append(content)

    # Join with section dividers
    merged_content = "\n\n---\n\n".join(chapters_content)

    # Create a combined file for reference
    combined_path = INPUT_DIR / "combined_translated.md"
    combined_path.write_text(merged_content, encoding="utf-8")
    print(f"Combined markdown saved to: {combined_path}")

    # Generate EPUB
    print(f"\nGenerating EPUB: {OUTPUT_PATH}")
    print(f"  Title: {TITLE}")
    print(f"  Author: {AUTHOR}")
    print(f"  Language: {LANGUAGE}")

    success = create_epub_from_markdown(
        markdown_content=merged_content,
        output_path=str(OUTPUT_PATH),
        title=TITLE,
        author=AUTHOR,
        base_path=str(INPUT_DIR),
        generate_cover=False  # Will create programmatic cover later
    )

    if success:
        print(f"\n✅ EPUB generated successfully!")
        print(f"   Output: {OUTPUT_PATH}")
        print(f"   Size: {OUTPUT_PATH.stat().st_size / 1024:.1f} KB")
    else:
        print(f"\n❌ EPUB generation failed")
        sys.exit(1)

    # Generate programmatic cover
    print("\nGenerating programmatic cover...")
    generate_programmatic_cover()

def generate_programmatic_cover():
    """Generate a simple programmatic cover."""
    try:
        from PIL import Image, ImageDraw, ImageFont

        # Create cover image
        width, height = 800, 1200
        img = Image.new('RGB', (width, height), color='#1a365d')  # Dark blue
        draw = ImageDraw.Draw(img)

        # Try to use a nice font, fallback to default
        # Increased font sizes for better Chinese character visibility
        try:
            title_font = ImageFont.truetype("/System/Library/Fonts/PingFang.ttc", 72)
            subtitle_font = ImageFont.truetype("/System/Library/Fonts/PingFang.ttc", 42)
            author_font = ImageFont.truetype("/System/Library/Fonts/PingFang.ttc", 36)
        except:
            title_font = ImageFont.load_default()
            subtitle_font = ImageFont.load_default()
            author_font = ImageFont.load_default()

        # Draw title
        title = "构建 Claude API 应用"
        # Center the title
        bbox = draw.textbbox((0, 0), title, font=title_font)
        title_width = bbox[2] - bbox[0]
        x = (width - title_width) // 2
        draw.text((x, 400), title, fill='white', font=title_font)

        # Draw author
        author = "Anthropic"
        bbox = draw.textbbox((0, 0), author, font=author_font)
        author_width = bbox[2] - bbox[0]
        x = (width - author_width) // 2
        draw.text((x, 500), author, fill='#a0aec0', font=author_font)

        # Draw subtitle
        subtitle = "Anthropic 官方课程"
        bbox = draw.textbbox((0, 0), subtitle, font=subtitle_font)
        subtitle_width = bbox[2] - bbox[0]
        x = (width - subtitle_width) // 2
        draw.text((x, 700), subtitle, fill='#a0aec0', font=subtitle_font)

        # Save cover
        cover_path = INPUT_DIR.parent / "cover.jpg"
        img.save(cover_path, 'JPEG', quality=95)
        print(f"   Cover saved to: {cover_path}")

        # Now regenerate EPUB with cover
        regenerate_with_cover(cover_path)

    except ImportError:
        print("   Warning: PIL not installed, skipping cover generation")
    except Exception as e:
        print(f"   Warning: Cover generation failed: {e}")

def regenerate_with_cover(cover_path: Path):
    """Regenerate EPUB with cover."""
    # Read merged content
    merged_path = INPUT_DIR / "combined_translated.md"
    merged_content = merged_path.read_text(encoding="utf-8")

    # Generate EPUB with cover
    success = create_epub_from_markdown(
        markdown_content=merged_content,
        output_path=str(OUTPUT_PATH),
        title=TITLE,
        author=AUTHOR,
        base_path=str(INPUT_DIR),
        cover_path=str(cover_path),
        generate_cover=False
    )

    if success:
        print(f"\n✅ EPUB with cover generated!")
        print(f"   Output: {OUTPUT_PATH}")
        print(f"   Size: {OUTPUT_PATH.stat().st_size / 1024:.1f} KB")

if __name__ == "__main__":
    main()