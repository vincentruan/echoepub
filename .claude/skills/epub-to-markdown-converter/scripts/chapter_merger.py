#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Chapter Merger: Merge duplicate/short chapters from Calibre MOBI conversion.

Problem: Calibre MOBI→EPUB conversion often creates many duplicate chapters
(e.g., "Effective Java" had 456 fake chapters from chapter marks in the MOBI).

Solution: Merge consecutive chapters that are:
1. Too short (< 100 words)
2. Have identical or near-identical titles
3. Content chapters (100+ words) are preserved

Usage:
  python chapter_merger.py <markdown_dir> [--output-dir <output_dir>]

Output:
  Creates merged chapter files in specified output directory or original directory with _merged suffix.
"""

import re
import argparse
from pathlib import Path
from typing import List, Tuple, Optional
from dataclasses import dataclass


@dataclass
class Chapter:
    """Represents a chapter file."""
    path: Path
    title: str
    content: str
    word_count: int
    chapter_num: int


def extract_title(content: str) -> str:
    """Extract title from markdown content (first H1 heading)."""
    match = re.match(r'^#\s+(.+)$', content, re.MULTILINE)
    if match:
        return match.group(1).strip()
    return ""


def count_words(content: str) -> int:
    """Count Chinese characters and English words."""
    # Remove code blocks
    text = re.sub(r'```[\s\S]*?```', '', content)
    # Remove inline code
    text = re.sub(r'`[^`]+`', '', text)
    # Remove images
    text = re.sub(r'!\[.*?\]\(.*?\)', '', text)
    # Remove links
    text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)
    # Remove markdown syntax
    text = re.sub(r'[#*_`~>|-]', '', text)
    # Count Chinese characters
    chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
    # Count English words
    english_words = len(re.findall(r'[a-zA-Z]+', text))
    return chinese_chars + english_words


def normalize_title(title: str) -> str:
    """Normalize title for comparison (remove chapter numbers, extra spaces)."""
    # Remove leading chapter numbers like "1.", "01_", "Chapter 1:", etc.
    title = re.sub(r'^(\d+[._]|\d+\.\s*|Chapter\s*\d+[:：]?\s*)', '', title, flags=re.IGNORECASE)
    # Remove extra whitespace
    title = ' '.join(title.split())
    # Lowercase for comparison
    return title.lower().strip()


def are_similar_titles(title1: str, title2: str) -> bool:
    """Check if two titles are similar (for merging duplicates)."""
    norm1 = normalize_title(title1)
    norm2 = normalize_title(title2)

    # Exact match after normalization
    if norm1 == norm2:
        return True

    # One is a prefix of the other
    if norm1.startswith(norm2) or norm2.startswith(norm1):
        return True

    # Similarity ratio (simple)
    if len(norm1) > 0 and len(norm2) > 0:
        common = sum(1 for a, b in zip(norm1, norm2) if a == b)
        ratio = common / max(len(norm1), len(norm2))
        if ratio > 0.8:
            return True

    return False


def load_chapters(markdown_dir: Path) -> List[Chapter]:
    """Load all chapter files from directory."""
    chapters = []

    # Find all markdown files (excluding TOC and report)
    md_files = sorted(markdown_dir.glob('*.md'))
    md_files = [f for f in md_files if not f.name.startswith('00_') and '_report' not in f.name]

    for i, md_file in enumerate(md_files):
        content = md_file.read_text(encoding='utf-8')
        title = extract_title(content)
        word_count = count_words(content)

        # Extract chapter number from filename
        match = re.match(r'^(\d+)_', md_file.name)
        chapter_num = int(match.group(1)) if match else i + 1

        chapters.append(Chapter(
            path=md_file,
            title=title,
            content=content,
            word_count=word_count,
            chapter_num=chapter_num
        ))

    return chapters


def merge_chapters(chapters: List[Chapter], min_words: int = 100) -> List[Tuple[Chapter, ...]]:
    """
    Group chapters for merging.

    Strategy:
    1. Chapters with >= min_words are kept as-is
    2. Consecutive short chapters are merged together
    3. Chapters with similar/duplicate titles are merged

    Returns:
        List of tuples, each containing chapters to merge
    """
    if not chapters:
        return []

    groups = []
    current_group = [chapters[0]]

    for i in range(1, len(chapters)):
        prev = chapters[i - 1]
        curr = chapters[i]

        should_merge = False

        # Case 1: Current chapter is too short
        if curr.word_count < min_words:
            should_merge = True

        # Case 2: Similar/duplicate titles
        elif are_similar_titles(prev.title, curr.title):
            should_merge = True

        # Case 3: Previous chapter was short and current starts without a proper heading
        elif prev.word_count < min_words:
            should_merge = True

        if should_merge:
            current_group.append(curr)
        else:
            groups.append(tuple(current_group))
            current_group = [curr]

    # Add the last group
    if current_group:
        groups.append(tuple(current_group))

    return groups


def create_merged_content(chapters: Tuple[Chapter, ...], keep_first_title: bool = True) -> str:
    """Create merged content from multiple chapters."""
    if len(chapters) == 1:
        return chapters[0].content

    parts = []
    first_title = chapters[0].title

    for i, chapter in enumerate(chapters):
        content = chapter.content

        if i == 0:
            # Keep first chapter's title
            parts.append(content)
        else:
            # Remove title from subsequent chapters if same as first
            title_to_remove = chapter.title
            if title_to_remove and (title_to_remove == first_title or
                                    are_similar_titles(title_to_remove, first_title)):
                # Remove the H1 heading
                content = re.sub(r'^#\s+.+\n', '', content, count=1)

            # Add separator if there's content
            if content.strip():
                parts.append("\n\n---\n\n" + content.strip())

    return '\n'.join(parts)


def process_directory(
    markdown_dir: Path,
    output_dir: Optional[Path] = None,
    min_words: int = 100,
    dry_run: bool = False
) -> dict:
    """
    Process a markdown directory and merge chapters.

    Args:
        markdown_dir: Directory containing chapter markdown files
        output_dir: Output directory (default: markdown_dir with _merged suffix)
        min_words: Minimum words for a chapter to be kept separate
        dry_run: If True, only report what would be done

    Returns:
        Statistics dictionary
    """
    if output_dir is None:
        output_dir = markdown_dir.parent / f"{markdown_dir.name}_merged"

    chapters = load_chapters(markdown_dir)
    groups = merge_chapters(chapters, min_words)

    stats = {
        'original_chapters': len(chapters),
        'merged_chapters': len(groups),
        'short_chapters_merged': 0,
        'duplicate_titles_merged': 0,
        'output_dir': str(output_dir)
    }

    if dry_run:
        print(f"Would merge {len(chapters)} chapters into {len(groups)} chapters")
        print(f"Output directory: {output_dir}")
        print("\nMerge plan:")
        for i, group in enumerate(groups):
            if len(group) > 1:
                titles = [f"'{c.title}' ({c.word_count} words)" for c in group]
                print(f"  {i+1}. Merge: {' + '.join(titles)}")
            else:
                print(f"  {i+1}. Keep: '{group[0].title}' ({group[0].word_count} words)")
        return stats

    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)

    # Copy images directory if exists
    images_src = markdown_dir / 'images'
    if images_src.exists():
        images_dst = output_dir / 'images'
        if not images_dst.exists():
            import shutil
            shutil.copytree(images_src, images_dst)

    # Write merged chapters
    for i, group in enumerate(groups):
        chapter_num = str(i + 1).zfill(2)
        first_chapter = group[0]

        # Generate filename
        safe_title = first_chapter.title.replace('/', '-').replace('\\', '-')[:50]
        safe_title = re.sub(r'[<>:"|?*]', '', safe_title)
        filename = f"{chapter_num}_{safe_title}.md"

        # Create merged content
        merged_content = create_merged_content(group)

        # Fix image paths if output is in a different directory
        if output_dir != markdown_dir:
            merged_content = merged_content.replace('./images/', '../images/')

        # Write file
        output_path = output_dir / filename
        output_path.write_text(merged_content, encoding='utf-8')

        if len(group) > 1:
            stats['short_chapters_merged'] += sum(1 for c in group if c.word_count < min_words)
            titles = [c.title for c in group]
            # Count duplicates
            normalized_titles = [normalize_title(t) for t in titles]
            unique_titles = set(normalized_titles)
            stats['duplicate_titles_merged'] += len(titles) - len(unique_titles)

    # Copy TOC and report if they exist
    toc_src = markdown_dir / '00_目录.md'
    if toc_src.exists():
        toc_dst = output_dir / '00_目录.md'
        toc_content = toc_src.read_text(encoding='utf-8')
        # Update chapter references in TOC (simplified - just copy)
        toc_dst.write_text(toc_content, encoding='utf-8')

    report_src = list(markdown_dir.glob('*_report.md'))
    if report_src:
        import shutil
        shutil.copy(report_src[0], output_dir / report_src[0].name)

    return stats


def main():
    parser = argparse.ArgumentParser(
        description='Merge duplicate/short chapters from Calibre MOBI conversion'
    )
    parser.add_argument('markdown_dir', help='Directory containing chapter markdown files')
    parser.add_argument('-o', '--output-dir', help='Output directory')
    parser.add_argument('--min-words', type=int, default=100,
                        help='Minimum words for a chapter to be kept separate (default: 100)')
    parser.add_argument('--dry-run', action='store_true',
                        help='Show what would be done without making changes')

    args = parser.parse_args()

    markdown_dir = Path(args.markdown_dir)
    if not markdown_dir.exists():
        print(f"Error: Directory not found: {markdown_dir}")
        return 1

    output_dir = Path(args.output_dir) if args.output_dir else None

    stats = process_directory(
        markdown_dir,
        output_dir,
        args.min_words,
        args.dry_run
    )

    if not args.dry_run:
        print(f"✓ Merged {stats['original_chapters']} chapters into {stats['merged_chapters']} chapters")
        print(f"  Short chapters merged: {stats['short_chapters_merged']}")
        print(f"  Duplicate titles merged: {stats['duplicate_titles_merged']}")
        print(f"  Output: {stats['output_dir']}")

    return 0


if __name__ == "__main__":
    exit(main())