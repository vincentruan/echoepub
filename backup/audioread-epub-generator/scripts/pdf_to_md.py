#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PDF to Markdown Converter with Academic Paper Support

Converts PDF files to Markdown using PyMuPDF with support for:
- Two-column academic paper layouts (ArXiv style)
- Citation and reference link conversion
- Math formula preservation
- Code block detection
Automatically creates a subdirectory named after the source file for all outputs.
"""

import sys
import re
from pathlib import Path
from typing import List, Tuple, Optional, Dict

try:
    import fitz  # PyMuPDF
except ImportError:
    print("Error: PyMuPDF not installed. Install with: pip install PyMuPDF")
    sys.exit(1)


class AcademicPDFConverter:
    """Converter for academic PDFs with two-column layouts."""

    # Patterns for detecting special content
    ABSTRACT_PATTERN = re.compile(r'^Abstract\s*$', re.IGNORECASE | re.MULTILINE)
    REFERENCE_PATTERN = re.compile(r'^References?\s*$', re.IGNORECASE | re.MULTILINE)
    NOTE_PATTERN = re.compile(r'^(Note|Comment|Remark|WARNING|TODO|注|注释|备注)\s*:', re.IGNORECASE | re.MULTILINE)
    CITATION_PATTERN = re.compile(r'\[(\d+[,\s\d]*)\]')  # [1], [1,2], [1-3]
    MATH_PATTERN = re.compile(r'\$[^$]+\$')  # Inline math $...$
    DISPLAY_MATH_PATTERN = re.compile(r'\$\$[^$]+\$\$')  # Display math $$...$$

    def __init__(self, pdf_path: str, output_dir: str = None):
        """Initialize converter."""
        self.pdf_path = Path(pdf_path)
        self.output_dir = Path(output_dir) if output_dir else self.pdf_path.parent / self.pdf_path.stem
        self.base_name = self.pdf_path.stem
        self.image_count = 0
        self.citation_links: Dict[str, str] = {}  # citation_id -> anchor

    def is_two_column_layout(self, page) -> bool:
        """Detect if page has two-column layout."""
        try:
            # Get text blocks
            blocks = page.get_text("dict")["blocks"]

            # Filter text blocks
            text_blocks = [b for b in blocks if b.get("type") == 0]  # type 0 = text

            if len(text_blocks) < 2:
                return False

            # Get x positions of text blocks
            x_positions = [b["bbox"][0] for b in text_blocks]

            # Check if there's a clear gap (indicating columns)
            x_positions.sort()
            gaps = []
            for i in range(len(x_positions) - 1):
                gap = x_positions[i + 1] - x_positions[i]
                if gap > 50:  # Significant gap
                    gaps.append(gap)

            # If we have one or more significant gaps, likely multi-column
            return len(gaps) >= 1

        except Exception:
            return False

    def extract_column_text(self, page) -> List[Tuple[float, float, str]]:
        """
        Extract text organized by columns.
        Returns list of (x0, y0, text) tuples sorted by column then by row.
        """
        try:
            # Get text blocks with their positions
            blocks = page.get_text("dict")["blocks"]

            # Filter text blocks
            text_blocks = []
            for b in blocks:
                if b.get("type") == 0:  # text
                    # Extract text from lines
                    block_text = ""
                    for line in b.get("lines", []):
                        for span in line.get("spans", []):
                            block_text += span.get("text", "")
                        block_text += "\n"

                    if block_text.strip():
                        x0 = b["bbox"][0]
                        y0 = b["bbox"][1]
                        text_blocks.append((x0, y0, block_text.strip()))

            if not text_blocks:
                return []

            # Detect columns by clustering x positions
            x_positions = [x for x, _, _ in text_blocks]
            if not x_positions:
                return []

            # Sort x positions
            unique_x = sorted(set(x_positions))

            # Group into columns (allowing for small variations in x position)
            columns = []
            if len(unique_x) >= 2:
                # Check for gap between positions
                median_x = unique_x[len(unique_x) // 2]
                left_col = [t for t in text_blocks if t[0] < median_x]
                right_col = [t for t in text_blocks if t[0] >= median_x]

                if left_col and right_col:
                    # Sort each column by y position (top to bottom)
                    left_col.sort(key=lambda t: t[1])
                    right_col.sort(key=lambda t: t[1])
                    columns = [left_col, right_col]
                else:
                    # Single column
                    text_blocks.sort(key=lambda t: t[1])
                    columns = [text_blocks]
            else:
                # Single column
                text_blocks.sort(key=lambda t: t[1])
                columns = [text_blocks]

            # Flatten: all left column blocks first, then right column
            result = []
            for col in columns:
                result.extend(col)

            return result

        except Exception as e:
            print(f"Warning: Error extracting columns: {e}")
            return []

    def process_citations(self, text: str) -> Tuple[str, List[str]]:
        """
        Convert citations to markdown links.
        Returns (processed_text, list_of_citation_ids).
        """
        citations_found = []

        def replace_citation(match):
            citation_content = match.group(1)
            # Parse citation content: [1], [1,2], [1-3]
            # Extract individual numbers
            ids = re.findall(r'\d+', citation_content)
            if ids:
                citations_found.extend(ids)
                # Create markdown links
                links = " ".join([f"[{id}](#ref-{id})" for id in ids])
                return links
            return match.group(0)

        # Find all citations first
        for match in self.CITATION_PATTERN.finditer(text):
            citation_content = match.group(1)
            ids = re.findall(r'\d+', citation_content)
            citations_found.extend(ids)

        # Replace citations with links
        processed_text = self.CITATION_PATTERN.sub(replace_citation, text)

        return processed_text, citations_found

    def _detect_code_language(self, text: str) -> str:
        """Detect programming language from code content."""
        text_lower = text.lower()

        # Check for language-specific patterns
        if 'def ' in text or 'class ' in text or 'import ' in text:
            return 'python'
        elif 'function' in text and ('{' in text or '=>' in text):
            return 'javascript'
        elif 'public class' in text or 'private ' in text or 'void main(' in text:
            return 'java'
        elif 'int main(' in text or '#include <' in text:
            return 'c'
        elif 'fn ' in text and ('->' in text or 'match' in text):
            return 'rust'
        else:
            return 'text'

    def detect_code_blocks(self, text: str) -> str:
        """
        Detect and mark code blocks using common patterns.
        Looks for keywords like "Algorithm", pseudocode markers, or monospace font indicators.
        """
        lines = text.split('\n')
        result = []
        in_code = False
        code_content = []
        current_index = 0

        while current_index < len(lines):
            line = lines[current_index]
            stripped = line.strip()

            # Detect code block start
            if not in_code:
                # Keywords that often indicate pseudocode
                if re.match(r'^(Algorithm|Pseudocode|Code|Listing)\s*\d*', stripped, re.I):
                    # Collect next few lines for language detection
                    code_content = []
                    for j in range(current_index + 1, min(current_index + 10, len(lines))):
                        if lines[j].strip():
                            code_content.append(lines[j].strip())
                        else:
                            break

                    # Detect language from collected content
                    sample_text = '\n'.join(code_content[:5])
                    language = self._detect_code_language(sample_text)

                    result.append(f'```{language}')
                    in_code = True
                # Monospace indicators (PyMuPDF may use Courier)
                elif 'Courier' in str(line) or 'monospace' in str(line).lower():
                    # Collect next few lines for language detection
                    code_content = []
                    for j in range(current_index + 1, min(current_index + 10, len(lines))):
                        if lines[j].strip():
                            code_content.append(lines[j].strip())
                        else:
                            break

                    # Detect language from collected content
                    sample_text = '\n'.join(code_content[:5])
                    language = self._detect_code_language(sample_text)

                    result.append(f'```{language}')
                    in_code = True
                    result.append(line)
                    current_index += 1
                    continue

            # Detect code block end
            if in_code:
                if stripped == '' or (not stripped and line.startswith('  ')):
                    # Empty line or indentation might end code
                    if not any(l.strip() for l in lines[current_index+1:current_index+3]):
                        result.append('```')
                        in_code = False
                elif re.match(r'^(Figure|Table|Algorithm)\s*\d*\.', stripped, re.I):
                    result.append('```')
                    in_code = False

            result.append(line)
            current_index += 1

        if in_code:
            result.append('```')

        return '\n'.join(result)

    def preserve_math(self, text: str) -> str:
        """
        Preserve math formulas by wrapping in code blocks.
        """
        # First preserve display math $$...$$
        text = self.DISPLAY_MATH_PATTERN.sub(lambda m: f'\n```\n{m.group(0)[2:-2]}\n```\n', text)

        # Then inline math $...$
        text = self.MATH_PATTERN.sub(lambda m: f'`{m.group(0)[1:-1]}`', text)

        return text

    def convert(self) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """
        Convert PDF to Markdown with academic paper optimizations.

        Returns:
            tuple: (markdown_path, images_dir, output_dir) or (None, None, None) on error
        """
        if not self.pdf_path.exists():
            print(f"Error: PDF file not found: {self.pdf_path}")
            return None, None, None

        if self.pdf_path.suffix.lower() != '.pdf':
            print(f"Error: File is not a PDF: {self.pdf_path}")
            return None, None, None

        # Create output directories
        self.output_dir.mkdir(parents=True, exist_ok=True)
        md_path = self.output_dir / f"{self.base_name}.md"
        images_dir = self.output_dir / f"{self.base_name}_images"

        print(f"Converting: {self.pdf_path}")
        print(f"Output directory: {self.output_dir}")

        try:
            doc = fitz.open(str(self.pdf_path))

            markdown_lines = []
            markdown_lines.append(f"# {self.base_name}\n\n")

            all_citations = []

            for page_num in range(len(doc)):
                page = doc[page_num]
                is_two_col = self.is_two_column_layout(page)

                page_text = ""

                if is_two_col:
                    # Extract by columns
                    column_blocks = self.extract_column_text(page)
                    for _, _, text in column_blocks:
                        page_text += text + "\n\n"
                else:
                    # Standard extraction
                    page_text = page.get_text("text")

                # Skip empty pages
                if not page_text.strip():
                    continue

                # Detect sections
                if self.ABSTRACT_PATTERN.search(page_text):
                    # Wrap abstract in blockquote
                    abstract_text = self.ABSTRACT_PATTERN.sub('', page_text).strip()
                    # Split at first non-abstract content
                    lines = abstract_text.split('\n')
                    abstract_lines = []
                    for line in lines:
                        if line.strip() and not line.startswith('#'):
                            abstract_lines.append(line)
                        elif abstract_lines:
                            break

                    if abstract_lines:
                        markdown_lines.append("## 摘要\n\n")
                        markdown_lines.append("> " + '\n> '.join(abstract_lines))
                        markdown_lines.append("\n\n")

                elif self.NOTE_PATTERN.search(page_text):
                    # Wrap margin notes and comments in blockquote
                    note_match = self.NOTE_PATTERN.search(page_text)
                    if note_match:
                        note_text = page_text[note_match.end():].strip()
                        # Extract note content (stop at next section or empty line)
                        note_lines = []
                        for line in note_text.split('\n'):
                            if line.strip() and not line.startswith('#'):
                                note_lines.append(line.strip())
                            elif note_lines:
                                break

                        if note_lines:
                            note_type = note_match.group(1)
                            markdown_lines.append(f"\n> **{note_type}**: " + ' '.join(note_lines) + "\n\n")

                elif self.REFERENCE_PATTERN.search(page_text):
                    # References section - preserve as-is
                    markdown_lines.append("## 参考文献\n\n")
                    ref_text = self.REFERENCE_PATTERN.sub('', page_text).strip()
                    markdown_lines.append(ref_text)
                    markdown_lines.append("\n\n")

                else:
                    # Regular content
                    # Process citations
                    processed_text, citations = self.process_citations(page_text)
                    all_citations.extend(citations)

                    # Preserve math formulas
                    processed_text = self.preserve_math(processed_text)

                    # Detect code blocks
                    processed_text = self.detect_code_blocks(processed_text)

                    markdown_lines.append(processed_text)
                    markdown_lines.append("\n\n")

                # Extract images from page
                image_list = page.get_images()

                if image_list:
                    images_dir.mkdir(parents=True, exist_ok=True)

                    for img_index, img in enumerate(image_list):
                        xref = img[0]
                        self.image_count += 1

                        # Extract image
                        base_image = doc.extract_image(xref)
                        image_bytes = base_image["image"]
                        image_ext = base_image["ext"]

                        # Save image as PNG (preserve original quality)
                        image_filename = f"image_{self.image_count:03d}.png"
                        image_path = images_dir / image_filename

                        # If not PNG, convert via PIL
                        if image_ext != "png":
                            try:
                                from PIL import Image
                                import io
                                img_pil = Image.open(io.BytesIO(image_bytes))
                                img_pil.save(str(image_path), "PNG")
                            except ImportError:
                                # Fallback: save as original format
                                image_filename = f"image_{self.image_count:03d}.{image_ext}"
                                image_path = images_dir / image_filename
                                with open(image_path, "wb") as img_file:
                                    img_file.write(image_bytes)
                        else:
                            with open(image_path, "wb") as img_file:
                                img_file.write(image_bytes)

                        # Add image reference to markdown (relative to markdown file)
                        relative_path = f"{self.base_name}_images/{image_filename}"
                        markdown_lines.append(f"\n![Image {self.image_count}]({relative_path})\n\n")

            doc.close()

            # Write markdown file
            markdown_content = "".join(markdown_lines)
            with open(md_path, 'w', encoding='utf-8') as f:
                f.write(markdown_content)

            print(f"✓ Markdown file created: {md_path}")
            print(f"✓ Detected {len(set(all_citations))} unique citations")

            if self.image_count > 0:
                print(f"✓ Extracted {self.image_count} images to: {images_dir}")
                return str(md_path), str(images_dir), str(self.output_dir)
            else:
                print("ℹ No images found in PDF")
                return str(md_path), None, str(self.output_dir)

        except Exception as e:
            print(f"Error during conversion: {str(e)}")
            import traceback
            traceback.print_exc()
            return None, None, None


def convert_pdf_to_markdown(pdf_path: str, output_dir: str = None):
    """
    Convert PDF to Markdown using PyMuPDF.

    Args:
        pdf_path: Path to input PDF file
        output_dir: Directory for output files (default: creates subdirectory next to PDF)

    Returns:
        tuple: (markdown_path, images_dir, output_dir) or (None, None, None) on error
    """
    # Use new converter
    converter = AcademicPDFConverter(pdf_path, output_dir)
    return converter.convert()


def main():
    if len(sys.argv) < 2:
        print("Usage: python pdf_to_md.py <input.pdf> [output_dir]")
        print("\nIf output_dir is not specified, creates a subdirectory named after the PDF file.")
        print("\nExample: python pdf_to_md.py document.pdf")
        print("         python pdf_to_md.py document.pdf ./output")
        sys.exit(1)

    pdf_path = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else None

    md_path, images_dir, base_output_dir = convert_pdf_to_markdown(pdf_path, output_dir)

    if md_path:
        print("\n=== Conversion Complete ===")
        print(f"Output directory: {base_output_dir}")
        print(f"Markdown: {md_path}")
        if images_dir:
            print(f"Images: {images_dir}")
    else:
        print("\nConversion failed.")
        sys.exit(1)


if __name__ == "__main__":
    main()
