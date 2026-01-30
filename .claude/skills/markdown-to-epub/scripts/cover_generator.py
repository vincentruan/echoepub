"""
EPUB cover image generation module.

This module generates book cover images using SiliconFlow's image generation API
based on the book title and table of contents.
"""

import os
import re
import requests
import tempfile
from pathlib import Path
from typing import Optional, List, Tuple


class CoverGenerator:
    """Generate book cover images using AI image generation API."""

    API_URL = "https://api.siliconflow.cn/v1/images/generations"
    DEFAULT_MODEL = "Qwen/Qwen-Image"
    DEFAULT_SIZE = "768x1024"  # Standard book cover aspect ratio (3:4)

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize cover generator.

        Args:
            api_key: SiliconFlow API key. If not provided, reads from
                     environment variable SILICONFLOW_API_KEY.
        """
        self.api_key = api_key or os.environ.get("SILICONFLOW_API_KEY")
        if not self.api_key:
            raise ValueError(
                "SiliconFlow API key is required. "
                "Set SILICONFLOW_API_KEY environment variable or pass api_key parameter."
            )

    def generate_cover(
        self,
        title: str,
        chapters: Optional[List[str]] = None,
        author: Optional[str] = None,
        output_path: Optional[str] = None,
        style: str = "modern",
        image_size: str = None
    ) -> Tuple[bool, str]:
        """
        Generate a book cover image.

        Args:
            title: Book title
            chapters: List of chapter titles for context
            author: Author name (optional)
            output_path: Where to save the generated image.
                        If None, saves to a temp file.
            style: Cover style ('modern', 'classic', 'minimalist', 'artistic')
            image_size: Image size in "widthxheight" format

        Returns:
            Tuple of (success: bool, image_path: str or error_message: str)
        """
        # Build the prompt
        prompt = self._build_prompt(title, chapters, author, style)

        # Generate the image
        try:
            image_url = self._call_api(prompt, image_size or self.DEFAULT_SIZE)
        except Exception as e:
            return False, f"API call failed: {str(e)}"

        # Download the image
        try:
            image_path = self._download_image(image_url, output_path, title)
            return True, image_path
        except Exception as e:
            return False, f"Image download failed: {str(e)}"

    def _build_prompt(
        self,
        title: str,
        chapters: Optional[List[str]] = None,
        author: Optional[str] = None,
        style: str = "modern"
    ) -> str:
        """
        Build the image generation prompt based on book metadata.

        Args:
            title: Book title
            chapters: List of chapter titles
            author: Author name
            style: Cover style

        Returns:
            Prompt string for image generation
        """
        # Analyze title and chapters to extract themes
        themes = self._extract_themes(title, chapters)

        # Style-specific prompt templates
        style_prompts = {
            "modern": (
                "A modern, professional book cover design with clean lines and "
                "contemporary aesthetics. Subtle gradient background with elegant typography area. "
            ),
            "classic": (
                "A classic, timeless book cover design with traditional elegance. "
                "Rich textures, ornate borders, and sophisticated color palette. "
            ),
            "minimalist": (
                "A minimalist book cover design with maximum whitespace. "
                "Single focal element, clean typography, limited color palette. "
            ),
            "artistic": (
                "An artistic, creative book cover design with expressive visuals. "
                "Abstract elements, bold colors, and unique artistic interpretation. "
            ),
        }

        base_prompt = style_prompts.get(style, style_prompts["modern"])

        # Build the complete prompt
        prompt_parts = [
            base_prompt,
            f"Theme: {', '.join(themes)}. ",
            "Professional book cover suitable for e-books. ",
            "High quality, detailed, visually appealing. ",
            "Leave space at the top for book title. ",
            "No text or letters in the image. ",
        ]

        # Add author context if provided
        if author:
            prompt_parts.append(f"Suitable for an author named {author}. ")

        return "".join(prompt_parts)

    def _extract_themes(
        self,
        title: str,
        chapters: Optional[List[str]] = None
    ) -> List[str]:
        """
        Extract themes from title and chapter titles.

        Args:
            title: Book title
            chapters: List of chapter titles

        Returns:
            List of extracted themes
        """
        themes = []

        # Combine all text for analysis
        all_text = title
        if chapters:
            all_text += " " + " ".join(chapters[:5])  # Use first 5 chapters

        # Common theme keywords mapping
        theme_keywords = {
            "economics": ["经济", "金融", "货币", "债务", "投资", "资产", "财富",
                         "GDP", "通胀", "通缩", "房价", "楼市", "股市"],
            "history": ["历史", "朝代", "改革", "变法", "古代", "王朝", "皇帝",
                       "年代", "事件", "战争", "革命"],
            "technology": ["技术", "科技", "互联网", "AI", "人工智能", "数字",
                          "编程", "软件", "硬件", "创新"],
            "business": ["商业", "企业", "管理", "创业", "公司", "市场", "营销",
                        "战略", "领导", "团队"],
            "philosophy": ["哲学", "思想", "思维", "认知", "人生", "价值观",
                          "智慧", "道理", "逻辑"],
            "crisis": ["危机", "风险", "泡沫", "崩盘", "衰退", "周期",
                      "波动", "不确定"],
            "growth": ["增长", "发展", "成长", "进步", "上升", "趋势",
                      "机会", "潜力"],
        }

        for theme, keywords in theme_keywords.items():
            for keyword in keywords:
                if keyword in all_text:
                    themes.append(theme)
                    break

        # Default themes if none found
        if not themes:
            themes = ["knowledge", "learning", "insight"]

        return themes[:4]  # Limit to 4 themes

    def _call_api(self, prompt: str, image_size: str) -> str:
        """
        Call the SiliconFlow image generation API.

        Args:
            prompt: Image generation prompt
            image_size: Image size in "widthxheight" format

        Returns:
            URL of the generated image

        Raises:
            Exception: If API call fails
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": self.DEFAULT_MODEL,
            "prompt": prompt,
            "image_size": image_size,
            "batch_size": 1,
            "num_inference_steps": 25,
        }

        response = requests.post(
            self.API_URL,
            headers=headers,
            json=payload,
            timeout=120
        )

        if response.status_code != 200:
            raise Exception(
                f"API returned status {response.status_code}: {response.text}"
            )

        result = response.json()

        if "images" not in result or not result["images"]:
            raise Exception(f"No images in API response: {result}")

        return result["images"][0]["url"]

    def _download_image(
        self,
        url: str,
        output_path: Optional[str],
        title: str
    ) -> str:
        """
        Download the generated image.

        Args:
            url: Image URL
            output_path: Desired output path
            title: Book title (for filename generation)

        Returns:
            Path to the downloaded image
        """
        response = requests.get(url, timeout=60)
        response.raise_for_status()

        # Determine output path
        if output_path:
            path = Path(output_path)
        else:
            # Generate a safe filename from title
            safe_title = re.sub(r'[^\w\s-]', '', title)[:30].strip()
            safe_title = re.sub(r'[-\s]+', '_', safe_title)
            path = Path(tempfile.gettempdir()) / f"cover_{safe_title}.jpg"

        # Ensure directory exists
        path.parent.mkdir(parents=True, exist_ok=True)

        # Write the image
        with open(path, 'wb') as f:
            f.write(response.content)

        return str(path)


def generate_cover_from_markdown(
    title: str,
    chapters: Optional[List[str]] = None,
    author: Optional[str] = None,
    output_path: Optional[str] = None,
    style: str = "modern",
    api_key: Optional[str] = None
) -> Tuple[bool, str]:
    """
    Convenience function to generate a book cover.

    Args:
        title: Book title
        chapters: List of chapter titles
        author: Author name
        output_path: Where to save the image
        style: Cover style ('modern', 'classic', 'minimalist', 'artistic')
        api_key: SiliconFlow API key (optional, uses env var if not provided)

    Returns:
        Tuple of (success: bool, image_path or error_message: str)
    """
    try:
        generator = CoverGenerator(api_key=api_key)
        return generator.generate_cover(
            title=title,
            chapters=chapters,
            author=author,
            output_path=output_path,
            style=style
        )
    except ValueError as e:
        return False, str(e)


if __name__ == "__main__":
    # Example usage
    import sys

    if len(sys.argv) < 2:
        print("Usage: python cover_generator.py <book_title> [chapter1] [chapter2] ...")
        sys.exit(1)

    book_title = sys.argv[1]
    chapter_titles = sys.argv[2:] if len(sys.argv) > 2 else None

    print(f"Generating cover for: {book_title}")
    if chapter_titles:
        print(f"Chapters: {chapter_titles}")

    success, result = generate_cover_from_markdown(
        title=book_title,
        chapters=chapter_titles,
        style="modern"
    )

    if success:
        print(f"Cover generated successfully: {result}")
    else:
        print(f"Failed to generate cover: {result}")
        sys.exit(1)
