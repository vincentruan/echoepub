#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Code Image OCR: Extract code from screenshot images using vision model.

Use vision model to recognize and extract code text from code screenshot images,
replacing the image reference with proper ```java code block.

Usage:
  from code_image_ocr import ocr_code_image

  code = ocr_code_image("path/to/screenshot.png", context="surrounding text")
"""

import os
import base64
import re
from typing import Optional, Tuple
from pathlib import Path


class CodeImageOCR:
    """OCR for code screenshot images using vision model."""

    # Minimum file size for code screenshots (larger than typical icons)
    MIN_FILE_SIZE = 5000  # 5KB

    # Aspect ratios typical for code screenshots (width/height)
    # Code is usually wider than tall
    MIN_ASPECT_RATIO = 0.5  # Not too tall
    MAX_ASPECT_RATIO = 20.0  # Code can be very wide (single line code)

    # Patterns that suggest this is NOT a code screenshot
    SKIP_PATTERNS = [
        r'二维码|qr|qrcode',
        r'封面|cover|书皮|title.?page',
        r'作者|author|portrait|头像',
        r'logo|icon|图标|徽章',
        r'decoration|装饰|背景',
        r'emoji|表情',
    ]

    # Aspect ratios typical for covers/portraits (should skip)
    # Covers are usually portrait (aspect < 0.85)
    # Code is usually landscape (aspect > 1.0)
    COVER_MAX_ASPECT_RATIO = 0.85  # Portrait images are likely covers

    # Minimum aspect ratio for code (code is usually wider)
    CODE_MIN_ASPECT_RATIO = 1.0

    # Patterns that suggest this IS a code screenshot
    CODE_INDICATORS = [
        # Programming keywords visible in screenshots
        r'\b(public|private|class|void|return|if|else|for|while)\b',
        r'\b(import|package|from|import)\b',
        r'\b(function|def|var|let|const)\b',
        r'@\w+',  # Annotations
        r'\{.*\}',  # Braces
        r'\b(true|false|null|None|True|False)\b',
        # Code structure
        r'function\s*\(',
        r'class\s+\w+',
        r'def\s+\w+',
        r'=>\s*\{',  # Arrow functions
        r'->\s*\w+',  # Return type annotations
    ]

    def __init__(self):
        pass

    def is_likely_code_screenshot(self, image_path: str, context: str = "") -> Tuple[bool, str]:
        """
        Determine if an image is likely a code screenshot.

        Returns:
            (is_code, reason) tuple
        """
        path = Path(image_path)

        if not path.exists():
            return False, "File not found"

        # Check file size
        file_size = os.path.getsize(image_path)
        if file_size < self.MIN_FILE_SIZE:
            return False, f"File too small ({file_size} bytes < {self.MIN_FILE_SIZE})"

        # Check for skip patterns in filename
        filename = path.stem.lower()
        for pattern in self.SKIP_PATTERNS:
            if re.search(pattern, filename, re.IGNORECASE):
                return False, f"Skip pattern matched: {pattern}"

        # Check aspect ratio
        try:
            from PIL import Image
            with Image.open(image_path) as img:
                width, height = img.size
                aspect_ratio = width / height if height > 0 else 0

                # Skip portrait images (likely covers)
                if aspect_ratio < self.COVER_MAX_ASPECT_RATIO:
                    return False, f"Portrait image, likely cover ({aspect_ratio:.2f} < {self.COVER_MAX_ASPECT_RATIO})"

                # Code screenshots should be landscape (wider than tall)
                if aspect_ratio < self.CODE_MIN_ASPECT_RATIO:
                    return False, f"Aspect ratio not typical for code ({aspect_ratio:.2f} < {self.CODE_MIN_ASPECT_RATIO})"

                if aspect_ratio > self.MAX_ASPECT_RATIO:
                    return False, f"Aspect ratio too wide ({aspect_ratio:.2f})"
        except Exception as e:
            return False, f"Could not read image dimensions: {e}"

        # Check context for code indicators
        context_lower = context.lower()
        code_context_indicators = [
            '代码', 'code', '程序', 'program', '函数', 'function',
            '方法', 'method', '类', 'class', '实现', 'implementation',
            'example', '示例', 'listing', '清单'
        ]

        has_code_context = any(ind in context_lower for ind in code_context_indicators)
        if has_code_context:
            return True, "Context indicates code"

        # By default, require landscape aspect ratio for code
        return False, "No code indicators found in context"

    def ocr_code_image(
        self,
        image_path: str,
        context: str = "",
        language: Optional[str] = None,
        max_retries: int = 2,
        retry_delay: int = 1
    ) -> Tuple[Optional[str], Optional[str]]:
        """
        Extract code from a screenshot image using vision model.

        Args:
            image_path: Path to the code screenshot
            context: Surrounding markdown text for context
            language: Force specific language (auto-detect if None)
            max_retries: Maximum retry attempts
            retry_delay: Delay between retries in seconds

        Returns:
            (code_block, failure_reason) tuple
            - code_block: Extracted code wrapped in ``` or None on failure
            - failure_reason: Reason for failure, None on success
        """
        try:
            import requests
            import time
        except ImportError:
            return None, "requests library not installed"

        path = Path(image_path)
        if not path.exists():
            return None, "Image file not found"

        valid_formats = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'}
        img_ext = path.suffix.lower()
        if img_ext not in valid_formats:
            return None, f"Unsupported format: {img_ext}"

        # Check if this looks like a code screenshot
        is_code, reason = self.is_likely_code_screenshot(image_path, context)
        if not is_code:
            return None, f"Not a code screenshot: {reason}"

        # Get API configuration
        api_key = os.getenv("ECHO_EPUB_OPEN_API_KEY")
        if not api_key:
            return None, "ECHO_EPUB_OPEN_API_KEY not set"

        api_base = os.getenv(
            "ECHO_EPUB_OPEN_AI_BASE_URL",
            "https://api.siliconflow.cn/v1"
        )
        vlm_model = os.getenv(
            "ECHO_EPUB_VLM_MODEL",
            "Pro/Qwen/Qwen2.5-VL-7B-Instruct"
        )

        # Read and encode image
        try:
            with open(image_path, 'rb') as f:
                image_data = f.read()
            image_base64 = base64.b64encode(image_data).decode('utf-8')
        except Exception as e:
            return None, f"Failed to read image: {e}"

        # Build OCR prompt
        prompt = """Extract the code from this image. Return ONLY the code text, no explanations or formatting instructions.

Rules:
1. Output only the code - no markdown, no backticks, no explanations
2. Preserve the exact code structure, indentation, and formatting from the image
3. If you see comments, preserve them
4. If the code is incomplete (cut off), extract what you can see
5. Do not add any text before or after the code"""

        if context:
            # Add context hint for language detection
            prompt += f"\n\nContext from surrounding text (for language detection):\n{context[:300]}"

        last_error = None
        for attempt in range(max_retries + 1):
            try:
                response = requests.post(
                    f"{api_base}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": vlm_model,
                        "messages": [{
                            "role": "user",
                            "content": [
                                {"type": "text", "text": prompt},
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": f"data:image/{img_ext.lstrip('.')};base64,{image_base64}"
                                    }
                                }
                            ]
                        }],
                        "temperature": 0.1,  # Low temperature for accuracy
                        "max_tokens": 4096
                    },
                    timeout=120
                )
                response.raise_for_status()
                result = response.json()

                if "choices" in result and len(result["choices"]) > 0:
                    code = result["choices"][0]["message"]["content"].strip()

                    # Clean up potential markdown wrapping from model output
                    code = self._clean_model_output(code)

                    if code and len(code) > 10:
                        # Detect language if not specified
                        if not language:
                            language = self._detect_language(code)

                        # Wrap in code block
                        return f"```{language}\n{code}\n```", None
                    else:
                        last_error = "Model returned insufficient code"
                else:
                    last_error = f"Invalid response: {result}"

            except requests.exceptions.Timeout:
                last_error = "Request timeout"
                if attempt < max_retries:
                    print(f"  Timeout, retrying ({attempt + 1}/{max_retries})...")
                    time.sleep(retry_delay)

            except requests.exceptions.RequestException as e:
                last_error = str(e)
                if attempt < max_retries:
                    print(f"  API error: {e}, retrying ({attempt + 1}/{max_retries})...")
                    time.sleep(retry_delay)

        return None, f"OCR failed: {last_error}"

    def _clean_model_output(self, code: str) -> str:
        """Clean potential markdown wrapping from model output."""
        # Remove surrounding ``` blocks if model added them
        code = re.sub(r'^```\w*\n', '', code)
        code = re.sub(r'\n```$', '', code)

        # Remove "Here is the code:" type prefixes
        code = re.sub(r'^(Here is the code:|The code is:|Code:)\s*\n', '', code, flags=re.IGNORECASE)

        return code.strip()

    def _detect_language(self, code: str) -> str:
        """Detect programming language from code content."""
        # Java
        if re.search(r'\b(public|private|protected)\s+(class|interface|enum|void)', code):
            return "java"
        if re.search(r'@\w+\s*(public|private|protected)', code):
            return "java"
        if re.search(r'\bSystem\.(out|err)\.print', code):
            return "java"

        # Python
        if re.search(r'\bdef\s+\w+\s*\(', code):
            return "python"
        if re.search(r'\bimport\s+\w+', code) and re.search(r'\bself\b', code):
            return "python"
        if re.search(r'if\s+__name__\s*==\s*["\']__main__["\']', code):
            return "python"

        # JavaScript/TypeScript
        if re.search(r'\b(function|const|let|var)\s+\w+\s*[=\(]', code):
            return "javascript"
        if re.search(r'=>\s*\{', code):
            return "javascript"
        if re.search(r'\binterface\s+\w+\s*\{', code):
            return "typescript"

        # SQL
        if re.search(r'\b(SELECT|INSERT|UPDATE|DELETE|CREATE|ALTER)\b', code, re.IGNORECASE):
            return "sql"

        # C/C++
        if re.search(r'#include\s*<', code):
            return "cpp"
        if re.search(r'\b(printf|scanf|malloc|free)\s*\(', code):
            return "c"

        # Go
        if re.search(r'\bfunc\s+\w+\s*\(', code):
            return "go"
        if re.search(r'package\s+\w+', code):
            return "go"

        # Rust
        if re.search(r'\bfn\s+\w+\s*\(', code):
            return "rust"
        if re.search(r'\blet\s+mut\b', code):
            return "rust"

        # Default
        return ""


# Singleton instance
_ocr_instance = None


def get_ocr_instance() -> CodeImageOCR:
    """Get or create singleton OCR instance."""
    global _ocr_instance
    if _ocr_instance is None:
        _ocr_instance = CodeImageOCR()
    return _ocr_instance


def ocr_code_image(image_path: str, context: str = "", language: Optional[str] = None) -> Tuple[Optional[str], Optional[str]]:
    """
    Convenience function to OCR a code image.

    Args:
        image_path: Path to the code screenshot
        context: Surrounding markdown text
        language: Force specific language

    Returns:
        (code_block, failure_reason) tuple
    """
    ocr = get_ocr_instance()
    return ocr.ocr_code_image(image_path, context, language)


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python code_image_ocr.py <image_path>")
        print("\nExtract code from a screenshot image using vision model.")
        sys.exit(1)

    image_path = sys.argv[1]
    code, error = ocr_code_image(image_path)

    if code:
        print("Extracted code:")
        print(code)
    else:
        print(f"Failed: {error}")