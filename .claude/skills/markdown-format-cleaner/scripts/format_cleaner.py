#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Markdown Format Cleaner

Clean up Markdown formatting issues:
1. Convert quote blocks that are actually code to ``` code blocks
2. Reconstruct tables from scattered quote lines
3. Standard formatting cleanup (whitespace, lists, etc.)

Usage:
  python format_cleaner.py <input_dir> [--output-dir <output_dir>]
"""

import re
import argparse
from pathlib import Path
from typing import Tuple, List, Optional


class FormatCleaner:
    """Clean up Markdown formatting issues."""

    # Java/programming keywords that indicate code
    CODE_KEYWORDS = [
        # Java
        r'\b(public|private|protected)\b',
        r'\b(static|final|abstract|native|synchronized)\b',
        r'\b(class|interface|enum|extends|implements)\b',
        r'\b(void|int|boolean|char|long|double|float|short|byte)\b',
        r'\b(return|new|this|super|instanceof)\b',
        r'\b(if|else|for|while|switch|case|default|break|continue)\b',
        r'\b(try|catch|finally|throw|throws)\b',
        r'\b(import|package)\b',
        r'@\w+',  # Annotations

        # Common types
        r'\b(String|Integer|Boolean|Long|Double|Float|Object)\b',
        r'\b(List|Map|Set|Collection|ArrayList|HashMap|HashSet)\b',
        r'\b(Optional|Stream|CompletableFuture)\b',

        # Method patterns
        r'\w+\s*\([^)]*\)\s*\{',
        r'\.\w+\([^)]*\)',

        # Code structure (removed problematic \{[\s\S]*\} pattern)
        r';\s*$',
        r'=\s*new\s+\w+',
    ]

    # Table header indicators
    TABLE_HEADER_PATTERNS = [
        r'^(Item|Chapter|Section|Parameter|Method|Class|Type|Name|Value|Description)',
        r'^[A-Z][a-z]+\s+[A-Z]',  # Two capitalized words
    ]

    def __init__(self):
        pass

    def convert_quote_code_blocks(self, content: str) -> str:
        """
        Convert quote blocks that are actually code to ``` blocks.

        Detection:
        - 3+ consecutive lines starting with '> '
        - Contains Java/programming keywords
        - Contains code patterns (braces, semicolons, annotations)
        """
        lines = content.split('\n')
        result = []
        i = 0

        while i < len(lines):
            line = lines[i]

            # Check if this starts a quote block
            if line.startswith('> '):
                # Collect consecutive quote lines
                quote_lines = []
                while i < len(lines) and lines[i].startswith('> '):
                    # Remove '> ' prefix
                    quote_lines.append(lines[i][2:])
                    i += 1

                # Check if this looks like code
                quote_content = '\n'.join(quote_lines)
                if self._is_code_content(quote_content):
                    # Detect language and convert to code block
                    language = self._detect_language(quote_content)
                    result.append(f'```{language}')
                    result.extend(quote_lines)
                    result.append('```')
                else:
                    # Keep as quote block
                    for ql in quote_lines:
                        result.append(f'> {ql}')
            else:
                result.append(line)
                i += 1

        return '\n'.join(result)

    def _is_code_content(self, content: str) -> bool:
        """Check if content looks like code."""
        # Count code indicators
        matches = 0
        matched_patterns = []
        for pattern in self.CODE_KEYWORDS:
            if re.search(pattern, content, re.MULTILINE):
                matches += 1
                matched_patterns.append(pattern)

        # Lower threshold for better detection of short code snippets
        if matches >= 2:
            return True

        # Check for structural code patterns
        # Semicolons at end of lines
        semicolon_count = len(re.findall(r';\s*$', content, re.MULTILINE))
        if semicolon_count >= 2:
            return True

        # Braces
        if '{' in content and '}' in content:
            # Check if braces are balanced-ish
            open_braces = content.count('{')
            close_braces = content.count('}')
            if open_braces > 0 and close_braces > 0:
                return True

        # Method definitions
        if re.search(r'\w+\s*\([^)]*\)\s*\{?', content):
            return True

        # Check for common code patterns that are clearly code
        # Method calls like .methodName()
        if re.search(r'\.\w+\([^)]*\)', content):
            return True

        # Variable assignments
        if re.search(r'\w+\s*=\s*\w+', content):
            return True

        # Class instantiation
        if re.search(r'new\s+\w+', content):
            return True

        # Import statements
        if re.search(r'\bimport\s+', content):
            return True

        # Package declarations
        if re.search(r'\bpackage\s+', content):
            return True

        # Single-line code with clear indicators
        # Check for type declarations
        if re.search(r'\b(class|interface|enum)\s+\w+', content):
            return True

        # Check for annotations
        if re.search(r'@\w+', content):
            return True

        return False

    def _detect_language(self, code: str) -> str:
        """Detect programming language from code content."""
        # Java
        if re.search(r'\b(public|private|protected)\s+(class|void|int|boolean|String)', code):
            return 'java'
        if re.search(r'@\w+', code) and re.search(r'\b(class|interface|void)\b', code):
            return 'java'

        # Python
        if re.search(r'\bdef\s+\w+\s*\(', code):
            return 'python'
        if re.search(r'\bself\b', code) and re.search(r'\bdef\b', code):
            return 'python'

        # JavaScript/TypeScript
        if re.search(r'\b(function|const|let|var)\s+\w+\s*[=\(]', code):
            return 'javascript'
        if re.search(r'=>\s*\{', code):
            return 'javascript'

        # SQL
        if re.search(r'\b(SELECT|INSERT|UPDATE|DELETE|FROM|WHERE)\b', code, re.IGNORECASE):
            return 'sql'

        return ''

    def reconstruct_tables(self, content: str) -> str:
        """
        Reconstruct tables from scattered quote lines.

        Pattern to detect:
        > Term
        > Example
        > Item
        > Parameterized type
        > List<String>
        > Item 26

        Becomes:
        | Term | Example | Item |
        |------|---------|------|
        | Parameterized type | List<String> | Item 26 |

        Also handles 3+ column tables by detecting repeating patterns.
        """
        lines = content.split('\n')
        result = []
        i = 0

        while i < len(lines):
            line = lines[i]

            # Look for patterns that might be scattered table rows
            if line.startswith('> ') and not line.startswith('> >'):
                # Collect consecutive single-item quote lines
                quote_items = []
                start_i = i

                while i < len(lines) and lines[i].startswith('> ') and not lines[i].startswith('> >'):
                    item = lines[i][2:].strip()
                    # Skip if this looks like code or a paragraph
                    if self._is_code_content(item) or len(item) > 100:
                        break
                    quote_items.append(item)
                    i += 1

                    # Stop after collecting a reasonable number of items
                    if len(quote_items) > 30:
                        break

                # Try to detect table structure
                if len(quote_items) >= 6:
                    # Check if items are short (table cells)
                    avg_len = sum(len(item) for item in quote_items) / len(quote_items)
                    if avg_len < 50:
                        # Try to detect column count by finding repeating pattern
                        col_count = self._detect_table_columns(quote_items)

                        if col_count and len(quote_items) % col_count == 0:
                            num_rows = len(quote_items) // col_count

                            # Check if first row looks like headers
                            headers = quote_items[:col_count]
                            if all(len(h) < 30 for h in headers):
                                # Build table
                                result.append('| ' + ' | '.join(headers) + ' |')
                                result.append('| ' + ' | '.join(['---'] * col_count) + ' |')

                                # Add data rows
                                for row_idx in range(1, num_rows):
                                    row_start = row_idx * col_count
                                    row_data = quote_items[row_start:row_start + col_count]
                                    result.append('| ' + ' | '.join(row_data) + ' |')

                                result.append('')
                                continue

                # Not a table, keep as is
                for item in quote_items:
                    result.append(f'> {item}')
            else:
                result.append(line)
                i += 1

        return '\n'.join(result)

    def _detect_table_columns(self, items: List[str]) -> Optional[int]:
        """
        Detect the number of columns in a potential table.

        Looks for repeating patterns in the first few items.
        Common patterns: 2, 3, or 4 columns.
        """
        if len(items) < 6:
            return None

        # Try different column counts
        for col_count in [3, 4, 2]:
            if len(items) % col_count != 0:
                continue

            num_rows = len(items) // col_count
            if num_rows < 2:
                continue

            # Check if headers (first row) look like table headers
            headers = items[:col_count]
            header_chars = sum(len(h) for h in headers)

            # Headers should be relatively short
            if header_chars > col_count * 25:
                continue

            # Check if subsequent rows have similar length pattern
            first_row_len = sum(len(items[col_count + j]) for j in range(col_count))

            # This looks like a valid table structure
            return col_count

        return None

    def fix_code_indentation(self, content: str) -> str:
        """
        Fix indentation in code blocks.

        EPUB/PDF conversion often loses indentation. This attempts to restore it.
        """
        result = []
        in_code_block = False
        code_lines = []
        code_lang = ''

        for line in content.split('\n'):
            if line.startswith('```'):
                if not in_code_block:
                    in_code_block = True
                    code_lang = line[3:].strip()
                    result.append(line)
                else:
                    # End of code block - fix indentation
                    fixed_code = self._fix_indentation('\n'.join(code_lines), code_lang)
                    result.extend(fixed_code.split('\n'))
                    result.append('```')
                    in_code_block = False
                    code_lines = []
            elif in_code_block:
                code_lines.append(line)
            else:
                result.append(line)

        return '\n'.join(result)

    def _fix_indentation(self, code: str, language: str) -> str:
        """Fix indentation in code based on language."""
        lines = code.split('\n')
        result = []
        indent_level = 0
        indent_size = 4

        for line in lines:
            stripped = line.strip()

            # Decrease indent for closing braces
            if stripped.startswith('}'):
                indent_level = max(0, indent_level - 1)

            # Add line with proper indent
            if stripped:
                result.append(' ' * (indent_level * indent_size) + stripped)
            else:
                result.append('')

            # Increase indent after opening braces
            open_count = stripped.count('{')
            close_count = stripped.count('}')
            indent_level = max(0, indent_level + open_count - close_count)

        return '\n'.join(result)

    def normalize_whitespace(self, content: str) -> str:
        """Normalize whitespace in the document."""
        # Compress multiple blank lines to maximum 2
        content = re.sub(r'\n{3,}', '\n\n', content)

        # Remove trailing whitespace
        content = re.sub(r'[ \t]+$', '', content, flags=re.MULTILINE)

        # Ensure single newline at end
        content = content.strip() + '\n'

        return content

    def clean(self, content: str) -> str:
        """Apply all cleaning transformations."""
        # Order matters: quote conversion before table reconstruction
        content = self.convert_quote_code_blocks(content)
        content = self.reconstruct_tables(content)
        content = self.fix_code_indentation(content)
        content = self.normalize_whitespace(content)
        return content


def process_file(input_path: Path, output_path: Optional[Path] = None) -> dict:
    """Process a single markdown file."""
    cleaner = FormatCleaner()

    content = input_path.read_text(encoding='utf-8')
    original_len = len(content)

    cleaned = cleaner.clean(content)

    stats = {
        'original_length': original_len,
        'cleaned_length': len(cleaned),
        'reduction': original_len - len(cleaned)
    }

    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(cleaned, encoding='utf-8')

    return stats


def process_directory(
    input_dir: Path,
    output_dir: Optional[Path] = None,
    fix_image_paths: bool = True
) -> dict:
    """Process all markdown files in a directory."""
    if output_dir is None:
        output_dir = input_dir / '_cleaned'

    output_dir.mkdir(parents=True, exist_ok=True)

    # Find all markdown files
    md_files = list(input_dir.glob('*.md'))
    md_files = [f for f in md_files if not f.name.startswith('00_') and '_report' not in f.name]

    total_stats = {
        'files_processed': 0,
        'total_reduction': 0
    }

    cleaner = FormatCleaner()

    for md_file in md_files:
        content = md_file.read_text(encoding='utf-8')
        cleaned = cleaner.clean(content)

        # Fix image paths if needed
        if fix_image_paths:
            cleaned = cleaned.replace('./images/', '../images/')

        # Write to output
        output_path = output_dir / md_file.name
        output_path.write_text(cleaned, encoding='utf-8')

        total_stats['files_processed'] += 1
        total_stats['total_reduction'] += len(content) - len(cleaned)

    # Copy images directory if exists
    images_src = input_dir / 'images'
    if images_src.exists():
        images_dst = output_dir / 'images'
        if not images_dst.exists():
            import shutil
            shutil.copytree(images_src, images_dst)

    # Copy TOC and report
    for extra_file in input_dir.glob('00_*.md'):
        shutil.copy(extra_file, output_dir / extra_file.name)

    for extra_file in input_dir.glob('*_report.md'):
        shutil.copy(extra_file, output_dir / extra_file.name)

    return total_stats


def main():
    parser = argparse.ArgumentParser(
        description='Clean up Markdown formatting issues'
    )
    parser.add_argument('input', help='Input file or directory')
    parser.add_argument('-o', '--output', help='Output file or directory')
    parser.add_argument('--no-image-path-fix', action='store_true',
                        help='Do not fix image paths')

    args = parser.parse_args()

    input_path = Path(args.input)

    if input_path.is_file():
        output_path = Path(args.output) if args.output else None
        stats = process_file(input_path, output_path)
        print(f"Processed: {input_path}")
        print(f"  Original: {stats['original_length']} chars")
        print(f"  Cleaned: {stats['cleaned_length']} chars")
        print(f"  Reduction: {stats['reduction']} chars")
    elif input_path.is_dir():
        output_path = Path(args.output) if args.output else None
        stats = process_directory(
            input_path,
            output_path,
            fix_image_paths=not args.no_image_path_fix
        )
        print(f"Processed {stats['files_processed']} files")
        print(f"Total reduction: {stats['total_reduction']} chars")
    else:
        print(f"Error: {input_path} not found")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())