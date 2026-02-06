#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Audio-Optimized EPUB Generator - Main Entry Point
"""

import os
import sys
import re
import tempfile
from pathlib import Path
from typing import Optional, List, Tuple, Dict
from datetime import datetime

# Add parent directory to path for imports
script_dir = Path(__file__).parent
sys.path.insert(0, str(script_dir))

from markdown_processor import MarkdownProcessor, EbookMetadata, Chapter, Section, filter_blank_pages
from audio_rewriter import AudioRewriter, RewriteResult
from epub_generator import EPUBGenerator, create_epub_from_markdown
from generate_report import scan_ebook
from image_descriptor import ImageDescriptor, describe_images_in_markdown

# Translation module
try:
    from translate_content import translate_markdown_file
    TRANSLATION_AVAILABLE = True
except ImportError:
    TRANSLATION_AVAILABLE = False
    print("Warning: Translation module not available. Translation features disabled.")


class ProcessingStats:
    """Track processing statistics."""
    def __init__(self):
        self.input_type = None
        self.input_file = None
        self.total_chapters = 0
        self.total_images = 0
        self.images_described = 0
        self.translated_paragraphs = 0
        self.skipped_paragraphs = 0  # Paragraphs skipped due to technical terms or Chinese content
        self.protected_terms_count = 0  # Technical terms preserved
        self.translation_applied = False
        self.sentences_split = 0
        self.lists_converted = 0
        self.tables_converted = 0
        self.glossary_items = []
        self.errors = []
        self.warnings = []

    def to_dict(self) -> Dict:
        return {
            'input_type': self.input_type,
            'input_file': self.input_file,
            'total_chapters': self.total_chapters,
            'total_images': self.total_images,
            'images_described': self.images_described,
            'translated_paragraphs': self.translated_paragraphs,
            'skipped_paragraphs': self.skipped_paragraphs,
            'protected_terms_count': self.protected_terms_count,
            'translation_applied': self.translation_applied,
            'sentences_split': self.sentences_split,
            'lists_converted': self.lists_converted,
            'tables_converted': self.tables_converted,
            'glossary_count': len(self.glossary_items),
            'errors': self.errors,
            'warnings': self.warnings
        }


class AudioEPUBGenerator:
    """Main generator for audiobook-optimized EPUB files."""

    def __init__(
        self,
        style: str = "moderate",
        language: str = "zh-CN",
        work_dir: Optional[str] = None,
        keep_blank_pages: bool = False
    ):
        """Initialize the generator."""
        self.style = style
        self.language = language
        self.work_dir = Path(work_dir) if work_dir else Path(tempfile.mkdtemp())
        self.keep_blank_pages = keep_blank_pages
        self.stats = ProcessingStats()
        self.metadata_title = None
        self.metadata_author = None
        self.blank_pages_removed = 0

    def process_pdf(
        self,
        pdf_path: str,
        output_path: str,
        title: Optional[str] = None,
        author: Optional[str] = None,
        enable_translation: bool = True
    ) -> Tuple[bool, str]:
        """Process a PDF file and generate audiobook-optimized EPUB."""
        self.stats.input_type = "PDF"
        self.stats.input_file = pdf_path

        pdf_file = Path(pdf_path)
        if not pdf_file.exists():
            return False, f"PDF file not found: {pdf_path}"

        print(f"Processing PDF: {pdf_path}")

        # Step 1: Convert PDF to Markdown
        print("\n[1/6] Converting PDF to Markdown...")
        md_path, images_dir = self._convert_pdf_to_md(pdf_file)

        if not md_path:
            return False, "Failed to convert PDF to Markdown"

        print(f"  - Markdown: {md_path}")
        if images_dir:
            print(f"  - Images: {images_dir}")
            self.stats.total_images = len(list(Path(images_dir).glob("*.png")))
            print(f"  - Extracted {self.stats.total_images} images")

        # Step 2: Translation workflow (if enabled)
        processed_md = md_path
        if enable_translation and TRANSLATION_AVAILABLE:
            print("\n[2/6] Running translation workflow...")
            translated_md = self._perform_translation(md_path)
            if translated_md != md_path:
                md_path = translated_md
        else:
            print("\n[2/6] Skipping translation (disabled or unavailable)")

        # Step 3: Process Markdown
        print("\n[3/6] Processing content...")
        final_md = self._process_markdown(md_path, images_dir)

        # Step 4: Apply audio-friendly transformations
        print("\n[4/6] Applying audio-friendly transformations...")
        audio_md = self._apply_audio_rewrites(final_md)

        # Step 4.5: Filter blank pages
        print("\n[4.5/6] Filtering blank pages...")
        audio_md, removed_count = filter_blank_pages(audio_md, self.keep_blank_pages)
        self.blank_pages_removed = removed_count
        if removed_count > 0:
            print(f"  ✓ Removed {removed_count} blank page(s)")
        else:
            print(f"  ✓ No blank pages found")

        # Step 5: Generate EPUB
        print("\n[5/6] Generating EPUB file...")
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        success = self._generate_epub(audio_md, str(output_file), title, author, images_dir)
        if not success:
            return False, "Failed to generate EPUB"

        # Step 6: Generate processing report
        print("\n[6/6] Generating processing report...")
        report_path = self._generate_report(str(output_file))

        print(f"\n✓ EPUB generated successfully: {output_file}")
        print(f"  - Processing report: {report_path}")

        return True, str(output_file)

    def process_epub(
        self,
        epub_path: str,
        output_path: str,
        title: Optional[str] = None,
        author: Optional[str] = None,
        enable_translation: bool = True
    ) -> Tuple[bool, str]:
        """Process an EPUB file and generate audiobook-optimized EPUB."""
        self.stats.input_type = "EPUB"
        self.stats.input_file = epub_path

        epub_file = Path(epub_path)
        if not epub_file.exists():
            return False, f"EPUB file not found: {epub_path}"

        print(f"Processing EPUB: {epub_path}")

        # Import epub_extractor
        try:
            from epub_extractor import EPUBExtractor
        except ImportError:
            return False, "epub_extractor module not found"

        # Step 1: Extract EPUB to Markdown
        print("\n[1/6] Extracting EPUB content...")
        extractor = EPUBExtractor(epub_path)

        if not extractor.load():
            return False, "Failed to load EPUB file"

        # Get metadata
        metadata = extractor.get_metadata()
        if not title and metadata.get('title'):
            title = metadata['title']
        if not author and metadata.get('author'):
            author = metadata['author']

        self.metadata_title = title
        self.metadata_author = author

        print(f"  - Title: {title}")
        print(f"  - Author: {author}")

        # Extract content
        md_path, images = extractor.extract_to_markdown(str(self.work_dir))

        print(f"  - Markdown: {md_path}")
        print(f"  - Images: {len(images)} files")
        self.stats.total_images = len(images)

        # Determine images directory
        images_dir = Path(md_path).parent / 'images'

        # Step 2: Translation workflow (if enabled)
        if enable_translation and TRANSLATION_AVAILABLE:
            print("\n[2/6] Running translation workflow...")
            translated_md = self._perform_translation(md_path)
            if translated_md != md_path:
                md_path = translated_md
        else:
            print("\n[2/6] Skipping translation (already in Chinese)")

        # Step 3: Process Markdown
        print("\n[3/6] Processing content...")
        final_md = self._process_markdown(md_path, str(images_dir))

        # Step 4: Apply audio-friendly transformations
        print("\n[4/6] Applying audio-friendly transformations...")
        audio_md = self._apply_audio_rewrites(final_md)

        # Step 4.5: Filter blank pages
        print("\n[4.5/6] Filtering blank pages...")
        audio_md, removed_count = filter_blank_pages(audio_md, self.keep_blank_pages)
        self.blank_pages_removed = removed_count
        if removed_count > 0:
            print(f"  ✓ Removed {removed_count} blank page(s)")
        else:
            print(f"  ✓ No blank pages found")

        # Step 5: Generate EPUB
        print("\n[5/6] Generating EPUB file...")
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        success = self._generate_epub(audio_md, str(output_file), title, author, str(images_dir))
        if not success:
            return False, "Failed to generate EPUB"

        # Step 6: Generate processing report
        print("\n[6/6] Generating processing report...")
        report_path = self._generate_report(str(output_file))

        print(f"\n✓ EPUB generated successfully: {output_file}")
        print(f"  - Processing report: {report_path}")

        return True, str(output_file)

    def process_markdown(
        self,
        md_path: str,
        output_path: str,
        title: Optional[str] = None,
        author: Optional[str] = None,
        images_dir: Optional[str] = None,
        enable_translation: bool = True
    ) -> Tuple[bool, str]:
        """Process a Markdown file and generate audiobook-optimized EPUB."""
        self.stats.input_type = "Markdown"
        self.stats.input_file = md_path

        md_file = Path(md_path)
        if not md_file.exists():
            return False, f"Markdown file not found: {md_path}"

        print(f"Processing Markdown: {md_path}")

        # Step 1: Translation workflow (if enabled)
        if enable_translation and TRANSLATION_AVAILABLE:
            print("\n[1/4] Running translation workflow...")
            translated_md = self._perform_translation(md_path)
            if translated_md != md_path:
                md_path = translated_md
        else:
            print("\n[1/4] Skipping translation (disabled or unavailable)")

        # Step 2: Process Markdown
        print("\n[2/4] Processing content...")
        final_md = self._process_markdown(md_path, images_dir)

        # Step 3: Apply audio-friendly transformations
        print("\n[3/4] Applying audio-friendly transformations...")
        audio_md = self._apply_audio_rewrites(final_md)

        # Step 4: Generate EPUB
        print("\n[4/4] Generating EPUB file...")
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        success = self._generate_epub(audio_md, str(output_file), title, author, images_dir)
        if not success:
            return False, "Failed to generate EPUB"

        # Generate processing report
        print("\nGenerating processing report...")
        report_path = self._generate_report(str(output_file))

        print(f"\n✓ EPUB generated successfully: {output_file}")
        print(f"  - Processing report: {report_path}")

        return True, str(output_file)

    def _convert_pdf_to_md(self, pdf_path: str) -> Tuple[Optional[str], Optional[str]]:
        """Convert PDF to Markdown using PyMuPDF."""
        try:
            import fitz  # PyMuPDF
        except ImportError:
            print("Error: PyMuPDF not installed. Install with: pip install PyMuPDF")
            return None, None

        pdf_file = Path(pdf_path)
        base_name = pdf_file.stem

        # Output paths
        md_path = self.work_dir / f"{base_name}.md"
        images_dir = self.work_dir / f"{base_name}_images"

        images_dir.mkdir(parents=True, exist_ok=True)

        print(f"  Extracting text and images...")

        try:
            doc = fitz.open(str(pdf_file))

            # Extract PDF metadata for title and author
            metadata = doc.metadata
            title = metadata.get("title", base_name)
            authors = metadata.get("author", "")

            # Store for later use
            self.metadata_title = title
            self.metadata_author = authors

            markdown_lines = []
            markdown_lines.append(f"# {title}\n\n")
            if authors:
                markdown_lines.append(f"**作者**: {authors}\n\n")

            image_count = 0
            page_content = []

            for page_num in range(len(doc)):
                page = doc[page_num]

                # Extract text
                text = page.get_text("text")

                # Detect headers (larger font, all caps, or at top of page)
                lines = text.split('\n')
                for line in lines:
                    line = line.strip()
                    if not line:
                        continue

                    # Simple header detection
                    if len(line) < 80 and line.isupper():
                        markdown_lines.append(f"## {line}\n\n")
                    elif len(line) < 80 and line.replace('.', '').isalnum():
                        # Could be a header
                        if page_num == 0 and len(page_content) < 3:
                            markdown_lines.append(f"## {line}\n\n")
                        else:
                            page_content.append(line)
                    else:
                        page_content.append(line)

                # Combine page content
                if page_content:
                    markdown_lines.extend(page_content)
                    markdown_lines.append("\n\n")
                    page_content = []

                # Extract images
                image_list = page.get_images()
                if image_list:
                    for img_index, img in enumerate(image_list):
                        xref = img[0]
                        image_count += 1

                        try:
                            base_image = doc.extract_image(xref)
                            image_bytes = base_image["image"]
                            image_ext = base_image["ext"]

                            # Save image
                            image_filename = f"image_{image_count:03d}.png"
                            image_path = images_dir / image_filename

                            if image_ext != "png":
                                try:
                                    from PIL import Image
                                    import io
                                    img_pil = Image.open(io.BytesIO(image_bytes))
                                    img_pil.save(str(image_path), "PNG")
                                except ImportError:
                                    image_filename = f"image_{image_count:03d}.{image_ext}"
                                    image_path = images_dir / image_filename
                                    with open(image_path, "wb") as f:
                                        f.write(image_bytes)
                            else:
                                with open(image_path, "wb") as f:
                                    f.write(image_bytes)

                            # Add image reference
                            markdown_lines.append(f"![Image {image_count}](./{base_name}_images/{image_filename})\n\n")

                        except Exception as e:
                            self.stats.warnings.append(f"Failed to extract image {image_count}: {e}")

            doc.close()

            # Write markdown
            md_content = "".join(markdown_lines)
            with open(md_path, 'w', encoding='utf-8') as f:
                f.write(md_content)

            self.stats.total_images = image_count
            print(f"  - Extracted {image_count} images")

            return str(md_path), str(images_dir)

        except Exception as e:
            self.stats.errors.append(f"PDF conversion error: {e}")
            print(f"Error converting PDF: {e}")
            return None, None

    def _perform_translation(self, md_path: str) -> str:
        """Perform translation workflow on markdown file."""
        if not TRANSLATION_AVAILABLE:
            print("  Translation module not available, skipping translation")
            return md_path

        print(f"\n[Translation] Processing: {md_path}")

        md_file = Path(md_path)
        output_dir = md_file.parent

        # Generate output path for translated markdown
        translated_md = output_dir / f"{md_file.stem}_translated.md"

        # Translate using the simplified approach
        success, message = translate_markdown_file(
            str(md_path),
            str(translated_md)
        )

        if success:
            self.stats.translation_applied = True
            try:
                self.stats.translated_paragraphs = int(message.split()[0])
            except (ValueError, IndexError):
                self.stats.translated_paragraphs = 0
            print(f"  ✓ Translation complete: {translated_md}")
            print(f"  - {message}")
            return str(translated_md)
        else:
            self.stats.errors.append(f"Translation failed: {message}")
            return str(md_path)

    def _process_markdown(self, md_path: str, images_dir: Optional[str] = None) -> str:
        """Process markdown with AI-generated image descriptions."""
        md_file = Path(md_path)
        with open(md_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # Only process if images directory is provided
        if images_dir:
            # Check if we should use AI or just smart fallback
            # If SILICONFLOW_API_KEY is not set, use smart fallback only
            use_ai = os.environ.get('SILICONFLOW_API_KEY') and getattr(self, 'use_ai', True)

            if use_ai:
                print(f"  Generating AI image descriptions...")
                descriptor = ImageDescriptor(
                    rules_path=str(Path(__file__).parent.parent / "references" / "image_description_rules.md")
                )
            else:
                print(f"  Using smart fallback mode (no AI)...")
                descriptor = None

            # Use smart fallback mode (default: True)
            # This generates placeholder descriptions for important images when AI fails
            smart_fallback = getattr(self, 'smart_fallback', True)

            processed_content, img_stats = describe_images_in_markdown(
                content,
                images_dir,
                descriptor,
                smart_fallback=smart_fallback
            )

            self.stats.total_images += img_stats['total_images']
            self.stats.images_described += img_stats['described']

            # Track fallback descriptions
            if 'fallback_generated' in img_stats:
                self.stats.warnings.append(f"智能筛选：为{img_stats['fallback_generated']}张重要图片生成了占位描述")

            # Track failed images
            if 'failed_images' in img_stats:
                for img_path, reason in img_stats['failed_images']:
                    self.stats.warnings.append(f"图片描述失败: {img_path} - {reason}")

            print(f"  - Described {img_stats['described']}/{img_stats['total_images']} images")
            if img_stats.get('fallback_generated', 0) > 0:
                print(f"  ⚠ Smart fallback: {img_stats['fallback_generated']} placeholder descriptions")
            if img_stats['failed'] > 0:
                print(f"  ⚠ Failed: {img_stats['failed']} images (see report)")

            return processed_content
        else:
            # No images directory, return original content
            return content

    def _apply_audio_rewrites(self, md_content: str) -> str:
        """Apply audio-friendly transformations."""
        rewriter = AudioRewriter(style=self.style)
        chapters = re.split(r'\n(?=# )', md_content)
        processed_chapters = []

        for chapter in chapters:
            if not chapter.strip():
                continue

            result = rewriter.rewrite_chapter(chapter)
            self.stats.sentences_split += result.stats.get('sentences_split', 0)
            self.stats.lists_converted += result.stats.get('lists_converted', 0)
            self.stats.tables_converted += result.stats.get('tables_converted', 0)

            self.stats.glossary_items.extend(result.glossary_items)
            processed_chapters.append(result.content)

        return '\n\n'.join(processed_chapters)

    def _generate_epub(
        self,
        md_content: str,
        output_path: str,
        title: Optional[str] = None,
        author: Optional[str] = None,
        images_dir: Optional[str] = None
    ) -> bool:
        """Generate EPUB from processed markdown."""
        try:
            # Use extracted metadata if available
            if not title and self.metadata_title:
                title = self.metadata_title
            if not author and self.metadata_author:
                author = self.metadata_author

            # Create metadata
            metadata = EbookMetadata()
            metadata.language = self.language

            # Extract title from content or use provided
            if not title:
                title_match = re.search(r'^# (.+)$', md_content, re.MULTILINE)
                if title_match:
                    title = title_match.group(1).strip()
            metadata.title = title or "Untitled"

            if author:
                metadata.author = author

            # Generate EPUB
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)

            return create_epub_from_markdown(
                markdown_content=md_content,
                output_path=str(output_file),
                title=title,
                author=author,
                base_path=str(Path(images_dir).parent.resolve()) if images_dir else None
            )

        except Exception as e:
            self.stats.errors.append(f"EPUB generation error: {e}")
            print(f"Error generating EPUB: {e}")
            return False

    def _generate_report(self, epub_path: str) -> str:
        """Generate processing report."""
        epub_file = Path(epub_path)
        report_path = epub_file.parent / f"{epub_file.stem}_report.md"

        stats = self.stats.to_dict()

        report = [
            "# Audio-Optimized EPUB Processing Report\n",
            f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n",
            f"**Input Type**: {stats['input_type']}\n",
            f"**Input File**: {stats['input_file']}\n",
            f"**Output File**: {epub_path}\n",
            "",
            "## Processing Statistics\n",
            f"- **Total Images**: {stats['total_images']}\n",
            f"- **Images with Descriptions**: {stats['images_described']}\n",
            f"- **Blank Pages Removed**: {self.blank_pages_removed}\n",
            f"- **Translation Applied**: {stats['translation_applied']}\n",
            f"- **Translated Paragraphs**: {stats['translated_paragraphs']}\n",
            f"- **Sentences Split**: {stats['sentences_split']}\n",
            f"- **Lists Converted**: {stats['lists_converted']}\n",
            f"- **Tables Converted**: {stats['tables_converted']}\n",
            f"- **Glossary Count**: {stats['glossary_count']}\n",
            "",
            "## Translation Workflow\n",
            "- **Translation Method**: Simplified using Claude subagents\n",
            "- **Target Language**: Simplified Chinese (zh-CN)\n",
            "- **Term Preservation**: Automatic by Claude\n",
            "",
            "## Known Limitations\n",
            "- Image descriptions may be placeholders if VLM API fails\n",
            "- Translation currently shows original text - needs Claude integration\n",
            "- Author extraction uses PDF metadata - may be empty\n",
            "- Blank page detection uses character threshold (50 chars by default)\n",
        ]

        # Add warnings if any
        if stats['warnings']:
            report.append("\n## Warnings\n")
            # Show first 50 warnings to avoid huge reports
            for warning in stats['warnings'][:50]:
                report.append(f"- {warning}\n")
            if len(stats['warnings']) > 50:
                report.append(f"- ... and {len(stats['warnings']) - 50} more warnings\n")
            report.append("")

        # Add errors if any
        if stats['errors']:
            report.append("## Errors\n")
            for error in stats['errors']:
                report.append(f"- {error}\n")
            report.append("")
        else:
            report.append("\n## Errors\n")
            report.append("No errors encountered.\n")

        # Write report
        with open(report_path, 'w', encoding='utf-8') as f:
            f.writelines(report)

        return str(report_path)


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: python main.py <input_file> [output_file] [options]")
        print("\nOptions:")
        print("  --style STYLE          Reading style: formal, moderate, conversational")
        print("  --title TITLE          Book title (auto-detected if not specified)")
        print("  --author AUTHOR        Author name")
        print("  --no-translation       Disable translation workflow")
        print("  --keep-blank-pages     Keep blank pages (default: remove them)")
        print("\nExamples:")
        print("  python main.py document.epub")
        print("  python main.py document.pdf")
        print("  python main.py document.md book.epub")
        print("  python main.py document.epub book_audio.epub --style conversational")
        print("  python main.py document.md --no-translation")
        print("  python main.py document.epub --keep-blank-pages")
        sys.exit(1)

    input_path = sys.argv[1]

    # Parse optional arguments
    output_path = None
    style = "moderate"
    title = None
    author = None
    enable_translation = True
    keep_blank_pages = False

    i = 2
    while i < len(sys.argv):
        arg = sys.argv[i]
        if arg == '--style' and i + 1 < len(sys.argv):
            style = sys.argv[i + 1]
            i += 2
        elif arg == '--title' and i + 1 < len(sys.argv):
            title = sys.argv[i + 1]
            i += 2
        elif arg == '--author' and i + 1 < len(sys.argv):
            author = sys.argv[i + 1]
            i += 2
        elif arg == '--no-translation':
            enable_translation = False
            i += 1
        elif arg == '--keep-blank-pages':
            keep_blank_pages = True
            i += 1
        elif not arg.startswith('--'):
            output_path = arg
            i += 1
        else:
            i += 1

    # Generate default output path
    if not output_path:
        input_file = Path(input_path)
        output_path = str(input_file.parent / f"{input_file.stem}_audio.epub")

    # Create generator and process
    generator = AudioEPUBGenerator(style=style, keep_blank_pages=keep_blank_pages)

    input_ext = Path(input_path).suffix.lower()

    if input_ext == '.pdf':
        success, message = generator.process_pdf(
            input_path,
            output_path,
            title,
            author,
            enable_translation
        )
    elif input_ext == '.epub':
        success, message = generator.process_epub(
            input_path,
            output_path,
            title,
            author,
            enable_translation
        )
    elif input_ext in ('.md', '.markdown'):
        success, message = generator.process_markdown(
            input_path,
            output_path,
            title,
            author,
            None,
            enable_translation
        )
    else:
        print(f"Error: Unsupported input format: {input_ext}")
        print("Supported formats: EPUB, PDF, Markdown (.md)")
        sys.exit(1)

    if success:
        print(f"\nProcessing complete: {message}")
        sys.exit(0)
    else:
        print(f"\nProcessing failed: {message}")
        sys.exit(1)


if __name__ == "__main__":
    main()
