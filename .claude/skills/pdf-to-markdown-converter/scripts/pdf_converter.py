#!/usr/bin/env python3
"""
PDF to Markdown Converter using PyMuPDF

Converts PDF files to Markdown format with image extraction.
Fast and lightweight alternative to Docling.
"""

import sys
import os
from pathlib import Path

try:
    import fitz  # PyMuPDF
except ImportError:
    print("Error: PyMuPDF is not installed. Install it with: pip install PyMuPDF")
    sys.exit(1)


def fix_latex_umlauts(text: str) -> str:
    """
    Fix LaTeX-style umlauts that are incorrectly encoded.
    Converts ¨a, ¨o, ¨u, ¨A, ¨O, ¨U to proper German umlauts.
    Also converts ß to ss (Swiss German style).
    Also fixes other common LaTeX encoding issues.
    
    Args:
        text: Input text with potential LaTeX encoding issues
        
    Returns:
        Text with corrected umlauts and Swiss German conventions
    """
    # Fix umlauts
    replacements = {
        '¨a': 'ä',
        '¨o': 'ö',
        '¨u': 'ü',
        '¨A': 'Ä',
        '¨O': 'Ö',
        '¨U': 'Ü',
        # Also handle cases where the diaeresis might be separated
        '¨ a': 'ä',
        '¨ o': 'ö',
        '¨ u': 'ü',
        '¨ A': 'Ä',
        '¨ O': 'Ö',
        '¨ U': 'Ü',
        # Swiss German: Replace ß with ss
        'ß': 'ss',
        # Handle other common LaTeX issues
        '``': '"',  # LaTeX opening quotes
        "''": '"',  # LaTeX closing quotes
    }
    
    for old, new in replacements.items():
        text = text.replace(old, new)
    
    return text


def convert_pdf_to_markdown(pdf_path: str, output_dir: str = None):
    """
    Convert PDF to Markdown using PyMuPDF.
    
    Args:
        pdf_path: Path to the input PDF file
        output_dir: Directory for output files (default: current directory)
    
    Returns:
        tuple: (markdown_path, images_dir) or (None, None) on error
    """
    # Validate input
    pdf_file = Path(pdf_path)
    if not pdf_file.exists():
        print(f"Error: PDF file not found: {pdf_path}")
        return None, None
    
    if not pdf_file.suffix.lower() == '.pdf':
        print(f"Error: File is not a PDF: {pdf_path}")
        return None, None
    
    # Set up output directory
    if output_dir is None:
        output_dir = Path.cwd()
    else:
        output_dir = Path(output_dir)
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Prepare output paths
    base_name = pdf_file.stem
    md_path = output_dir / f"{base_name}.md"
    images_dir = output_dir / f"{base_name}_images"
    
    print(f"Converting: {pdf_path}")
    print(f"Output: {md_path}")
    
    try:
        # Open PDF document
        doc = fitz.open(str(pdf_file))
        
        # Build markdown content
        markdown_lines = []
        markdown_lines.append(f"# {base_name}\n\n")
        
        image_count = 0
        
        # Process each page
        for page_num in range(len(doc)):
            page = doc[page_num]
            
            # Add page header
            markdown_lines.append(f"## Page {page_num + 1}\n\n")
            
            # Extract text with layout preservation
            text = page.get_text("text")
            if text.strip():
                # Fix LaTeX umlauts and encoding issues
                text = fix_latex_umlauts(text)
                markdown_lines.append(text)
                markdown_lines.append("\n\n")
            
            # Extract images from page
            image_list = page.get_images()
            
            if image_list:
                images_dir.mkdir(parents=True, exist_ok=True)
                
                for img_index, img in enumerate(image_list):
                    xref = img[0]
                    image_count += 1
                    
                    # Extract image
                    base_image = doc.extract_image(xref)
                    image_bytes = base_image["image"]
                    image_ext = base_image["ext"]
                    
                    # Save image as PNG
                    image_filename = f"image_{image_count:03d}.png"
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
                            image_filename = f"image_{image_count:03d}.{image_ext}"
                            image_path = images_dir / image_filename
                            with open(image_path, "wb") as img_file:
                                img_file.write(image_bytes)
                    else:
                        with open(image_path, "wb") as img_file:
                            img_file.write(image_bytes)
                    
                    # Add image reference to markdown (use ./ prefix for consistency)
                    relative_path = f"./{base_name}_images/{image_filename}"
                    markdown_lines.append(f"![Image {image_count}]({relative_path})\n\n")
        
        doc.close()
        
        # Write markdown file
        markdown_content = "".join(markdown_lines)
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        
        print(f"✓ Markdown file created: {md_path}")
        
        if image_count > 0:
            print(f"✓ Extracted {image_count} images to: {images_dir}")
            return str(md_path), str(images_dir)
        else:
            print("ℹ No images found in PDF")
            return str(md_path), None
    
    except Exception as e:
        print(f"Error during conversion: {str(e)}")
        import traceback
        traceback.print_exc()
        return None, None


def main():
    if len(sys.argv) < 2:
        print("Usage: python pdf_converter.py <input.pdf> [output_dir]")
        print("\nExample: python pdf_converter.py document.pdf ./output")
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else None
    
    md_path, images_dir = convert_pdf_to_markdown(pdf_path, output_dir)
    
    if md_path:
        print("\n=== Conversion Complete ===")
        print(f"Markdown: {md_path}")
        if images_dir:
            print(f"Images: {images_dir}")
    else:
        print("\nConversion failed.")
        sys.exit(1)


if __name__ == "__main__":
    main()