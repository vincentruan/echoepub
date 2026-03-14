#!/usr/bin/env python3
"""
Ebook Pre-converter: Non-EPUB → EPUB using Calibre's ebook-convert.

Supported input formats (via Calibre):
  MOBI, AZW3, CBZ, CBR, CHM, DJVU, FB2, LIT, LRF, ODT, PRC, PDB, PML, RB, RTF, SNB, TCR, TXT

Usage:
  python ebook_preconvert.py <input-file> [output-epub-path]

If output path is omitted, creates a temporary EPUB and prints its path.
"""

import sys
import os
import subprocess
import shutil
import tempfile
from pathlib import Path

# Formats that Calibre can convert to EPUB (excluding EPUB itself and PDF which has its own skill)
CALIBRE_INPUT_FORMATS = {
    '.mobi', '.azw3', '.azw', '.cbz', '.cbr', '.chm', '.djvu',
    '.fb2', '.lit', '.lrf', '.odt', '.prc', '.pdb', '.pml',
    '.rb', '.rtf', '.snb', '.tcr', '.txt',
}


def find_ebook_convert():
    """
    Locate Calibre's ebook-convert executable.

    Returns:
        str: Path to ebook-convert

    Raises:
        SystemExit: If not found
    """
    path = shutil.which('ebook-convert')

    # macOS fallback
    if not path and sys.platform == 'darwin':
        macos_path = '/Applications/calibre.app/Contents/MacOS/ebook-convert'
        if os.path.exists(macos_path):
            path = macos_path

    if not path:
        print("Error: Calibre's ebook-convert not found.")
        print("\nInstall Calibre:")
        print("  macOS:   brew install --cask calibre")
        print("  Linux:   sudo apt-get install calibre")
        print("  Windows: https://calibre-ebook.com/download")
        sys.exit(1)

    return path


def is_supported_format(file_path: str) -> bool:
    """Check if the file format is supported for pre-conversion."""
    return Path(file_path).suffix.lower() in CALIBRE_INPUT_FORMATS


def convert_to_epub(input_path: str, output_path: str = None) -> str:
    """
    Convert an ebook file to EPUB using Calibre.

    Args:
        input_path: Path to the input ebook file
        output_path: Optional output EPUB path. If None, uses a temp directory.

    Returns:
        str: Path to the generated EPUB file

    Raises:
        SystemExit: On conversion failure
    """
    input_file = Path(input_path).resolve()

    if not input_file.exists():
        print(f"Error: File not found: {input_path}")
        sys.exit(1)

    if input_file.suffix.lower() not in CALIBRE_INPUT_FORMATS:
        print(f"Error: Unsupported format: {input_file.suffix}")
        print(f"Supported: {', '.join(sorted(CALIBRE_INPUT_FORMATS))}")
        sys.exit(1)

    ebook_convert = find_ebook_convert()

    if output_path is None:
        temp_dir = tempfile.mkdtemp(prefix='ebook_preconvert_')
        output_path = str(Path(temp_dir) / f"{input_file.stem}.epub")

    print(f"Converting {input_file.suffix.upper()[1:]} to EPUB: {input_file.name}")
    try:
        subprocess.run(
            [ebook_convert, str(input_file), output_path],
            capture_output=True,
            text=True,
            check=True,
        )
        print(f"✓ EPUB created: {output_path}")
        return output_path
    except subprocess.CalledProcessError as e:
        print(f"Error during conversion:\n{e.stderr}")
        sys.exit(1)


def main():
    if len(sys.argv) < 2:
        print("Usage: python ebook_preconvert.py <input-file> [output.epub]")
        print(f"\nSupported formats: {', '.join(sorted(CALIBRE_INPUT_FORMATS))}")
        sys.exit(1)

    input_path = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 else None
    result = convert_to_epub(input_path, output_path)
    print(result)


if __name__ == "__main__":
    main()
