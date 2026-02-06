#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EPUB content extractor for audiobook processing pipeline.
"""

import sys
from pathlib import Path
from typing import List, Tuple, Optional
try:
    from ebooklib import epub
except ImportError:
    print("Error: ebooklib not installed. Install with: pip install ebooklib")
    sys.exit(1)


class EPUBExtractor:
    """Extract content from EPUB files for processing."""

    def __init__(self, epub_path: str):
        """Initialize with EPUB file path."""
        self.epub_path = Path(epub_path)
        if not self.epub_path.exists():
            raise FileNotFoundError(f"EPUB file not found: {epub_path}")
        self.book = None
        self.metadata = {}

    def load(self) -> bool:
        """Load the EPUB file."""
        try:
            self.book = epub.read_epub(str(self.epub_path))
            self._extract_metadata()
            return True
        except Exception as e:
            print(f"Error loading EPUB: {e}")
            return False

    def _extract_metadata(self):
        """Extract metadata from EPUB."""
        if not self.book:
            return

        # Get basic metadata
        self.metadata['title'] = self.book.get_metadata('DC', 'title')
        self.metadata['author'] = self.book.get_metadata('DC', 'creator')
        self.metadata['publisher'] = self.book.get_metadata('DC', 'publisher')
        self.metadata['date'] = self.book.get_metadata('DC', 'date')
        self.metadata['language'] = self.book.get_metadata('DC', 'language')
        self.metadata['identifier'] = self.book.get_metadata('DC', 'identifier')

        # Extract first value from lists
        for key in self.metadata:
            if isinstance(self.metadata[key], list) and len(self.metadata[key]) > 0:
                self.metadata[key] = self.metadata[key][0][0] if isinstance(self.metadata[key][0], tuple) else self.metadata[key][0]

    def get_metadata(self) -> dict:
        """Get book metadata."""
        return self.metadata

    def get_toc(self) -> List[dict]:
        """Get table of contents."""
        if not self.book:
            return []

        toc = self.book.toc
        chapters = []

        def process_toc_item(item, level=0):
            if isinstance(item, tuple) and len(item) > 1:
                # (section, title, children)
                section = item[0]
                title = item[1] if len(item) > 1 else "Unknown"
                children = item[2] if len(item) > 2 else []

                if hasattr(section, 'href'):
                    chapters.append({
                        'level': level,
                        'title': str(title),
                        'href': str(section.href),
                        'file': section.get_name()
                    })

                for child in children:
                    process_toc_item(child, level + 1)

            elif isinstance(item, (epub.Link, epub.Section)):
                if hasattr(item, 'href'):
                    chapters.append({
                        'level': level,
                        'title': item.title if hasattr(item, 'title') else "Unknown",
                        'href': str(item.href),
                        'file': item.get_name() if hasattr(item, 'get_name') else str(item.href)
                    })

        for item in toc:
            process_toc_item(item)

        return chapters

    def extract_to_markdown(self, output_dir: Optional[str] = None) -> Tuple[str, List[Path]]:
        """Extract all content to markdown files.

        Returns:
            (output_directory, list_of_image_paths)
        """
        if not self.book:
            raise ValueError("EPUB not loaded. Call load() first.")

        import tempfile
        from bs4 import BeautifulSoup

        # Create output directory
        if output_dir:
            out_dir = Path(output_dir)
        else:
            out_dir = Path(tempfile.mkdtemp(prefix='epub_extract_'))

        out_dir.mkdir(parents=True, exist_ok=True)

        # Create images directory
        images_dir = out_dir / 'images'
        images_dir.mkdir(exist_ok=True)

        # Extract all items
        from ebooklib import ITEM_DOCUMENT, ITEM_IMAGE
        all_items = list(self.book.get_items())
        content_files = [item for item in all_items if item.get_type() == ITEM_DOCUMENT]
        image_items = [item for item in all_items if item.get_type() == ITEM_IMAGE]

        # Extract images with improved path handling and conflict resolution
        image_paths = []
        filename_counter = {}  # Track filename conflicts
        path_mapping = {}  # Map original path to new filename
        extraction_stats = {
            'success': 0,
            'failed': 0,
            'skipped': 0
        }

        print(f"\n  Extracting images from {len(image_items)} items...")

        for img in image_items:
            try:
                img_data = img.get_content()
                img_name = img.get_name()

                # Use just the filename (flatten directory structure)
                img_filename = Path(img_name).name
                img_base = Path(img_filename).stem
                img_ext = Path(img_filename).suffix

                # Handle filename conflicts
                if img_filename in filename_counter:
                    filename_counter[img_filename] += 1
                    new_filename = f"{img_base}_{filename_counter[img_filename]}{img_ext}"
                else:
                    filename_counter[img_filename] = 0
                    new_filename = img_filename

                img_path = images_dir / new_filename

                with open(img_path, 'wb') as f:
                    f.write(img_data)

                # Map original name to new filename for reference updating
                path_mapping[img_name] = new_filename
                image_paths.append(img_path)
                extraction_stats['success'] += 1

            except Exception as e:
                extraction_stats['failed'] += 1
                print(f"    ✗ Failed to extract image {img.get_name()}: {e}")

        # Log extraction statistics
        print(f"  ✓ Extracted {extraction_stats['success']} images")
        if extraction_stats['failed'] > 0:
            print(f"    ✗ Failed: {extraction_stats['failed']} images")

        # Extract and convert content to markdown
        markdown_content = []

        # Get TOC for ordering
        toc = self.get_toc()
        processed_files = set()
        seen_titles = set()  # Track seen titles to avoid duplicates

        # Add title and author only once at the beginning if not already in first TOC item
        if toc:
            # Check if first TOC item is the book title
            first_chapter = toc[0]
            if first_chapter['level'] == 0 and first_chapter['title'] == self.metadata.get('title'):
                # Don't add duplicate title - it will be added when processing the first chapter
                pass
            else:
                # Add title page
                markdown_content.append(f"# {self.metadata.get('title', 'Untitled')}\n\n")
                if self.metadata.get('author'):
                    markdown_content.append(f"**作者**: {self.metadata['author']}\n\n")
        else:
            # No TOC, add title and author at the beginning
            markdown_content.append(f"# {self.metadata.get('title', 'Untitled')}\n\n")
            if self.metadata.get('author'):
                markdown_content.append(f"**作者**: {self.metadata['author']}\n\n")

        # Process TOC items in order
        for chapter in toc:
            file_name = chapter['file']
            title = chapter['title']

            # Skip if we've already processed this file or this title
            if file_name in processed_files:
                continue
            if title in seen_titles:
                continue

            # Mark this title as seen
            seen_titles.add(title)

            # Skip title/cover pages (level 0 items that match the book title)
            if chapter['level'] == 0 and title == self.metadata.get('title'):
                # Still mark file as processed to avoid re-processing
                processed_files.add(file_name)
                continue

            # Find matching content item
            for item in content_files:
                if item.get_name() == file_name:
                    soup = BeautifulSoup(item.get_content(), 'html.parser')

                    # Convert HTML to markdown first
                    md_text = self._html_to_markdown(soup, images_dir, path_mapping)

                    # Only add chapter heading if the HTML doesn't already start with an H1
                    # and it's not the title page
                    if not (chapter['level'] == 0 and chapter['title'] == self.metadata.get('title')):
                        # Check if markdown already starts with this chapter heading
                        heading_marker = f"# {chapter['title']}"
                        if not md_text.lstrip().startswith(heading_marker):
                            level_prefix = '#' * (chapter['level'] + 1)
                            markdown_content.append(f"{level_prefix} {chapter['title']}\n\n")

                    markdown_content.append(md_text)
                    markdown_content.append("\n\n")

                    processed_files.add(file_name)
                    break

        # Process any remaining content files not in TOC
        for item in content_files:
            if item.get_name() not in processed_files:
                soup = BeautifulSoup(item.get_content(), 'html.parser')
                markdown_content.append(self._html_to_markdown(soup, images_dir, path_mapping))
                markdown_content.append("\n\n")
                processed_files.add(item.get_name())

        # Write combined markdown
        output_file = out_dir / 'content.md'
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(''.join(markdown_content))

        return str(output_file), image_paths

    def _html_to_markdown(self, soup, images_dir: Path, path_mapping: dict = None) -> str:
        """Convert HTML content to markdown."""
        from html2text import HTML2Text
        import re

        # Update image references with path mapping
        for img in soup.find_all('img'):
            src = img.get('src', '')
            if src:
                # Try to find the image in path_mapping
                # Normalize the src path for matching
                normalized_src = src.replace('\\', '/').lstrip('/')

                # Find matching path in mapping
                new_filename = None
                if path_mapping:
                    # Try exact match first
                    if normalized_src in path_mapping:
                        new_filename = path_mapping[normalized_src]
                    else:
                        # Try partial match (compare just filename)
                        src_filename = Path(normalized_src).name
                        for orig_path, new_file in path_mapping.items():
                            if Path(orig_path).name == src_filename:
                                new_filename = new_file
                                break

                # Use mapped filename or fall back to original filename
                if new_filename:
                    img['src'] = f"images/{new_filename}"
                else:
                    # Fallback: use original filename
                    img_name = Path(src).name
                    img['src'] = f"images/{img_name}"

        # Convert to markdown
        h = HTML2Text()
        h.ignore_links = False
        h.ignore_images = False
        h.ignore_emphasis = False
        h.body_width = 0  # Don't wrap lines
        h.unicode_snob = True
        h.skip_internal_links = False

        markdown_text = h.handle(str(soup))

        # Clean up excessive whitespace
        markdown_text = re.sub(r'\n{3,}', '\n\n', markdown_text)

        return markdown_text


def main():
    """CLI entry point."""
    if len(sys.argv) < 2:
        print("Usage: python epub_extractor.py <epub_file> [output_dir]")
        print("\nExample:")
        print("  python epub_extractor.py book.epub")
        print("  python epub_extractor.py book.epub ./extracted")
        sys.exit(1)

    epub_path = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else None

    print(f"Extracting EPUB: {epub_path}")

    extractor = EPUBExtractor(epub_path)

    if not extractor.load():
        print("Failed to load EPUB file")
        sys.exit(1)

    # Print metadata
    metadata = extractor.get_metadata()
    print("\n=== Book Metadata ===")
    for key, value in metadata.items():
        if value:
            print(f"{key.capitalize()}: {value}")

    # Print TOC
    toc = extractor.get_toc()
    print(f"\n=== Table of Contents ({len(toc)} chapters) ===")
    for i, chapter in enumerate(toc[:20], 1):  # Show first 20
        indent = "  " * chapter['level']
        print(f"{indent}{i}. {chapter['title']}")

    if len(toc) > 20:
        print(f"\n... and {len(toc) - 20} more chapters")

    # Extract to markdown
    print("\nExtracting content...")
    md_file, image_paths = extractor.extract_to_markdown(output_dir)

    print(f"\n✓ Extraction complete!")
    print(f"  - Markdown: {md_file}")
    print(f"  - Images: {len(image_paths)} files")

    return 0


if __name__ == "__main__":
    import ebooklib
    sys.exit(main())
