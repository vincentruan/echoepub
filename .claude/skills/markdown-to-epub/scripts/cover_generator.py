"""
EPUB cover image generation module.

This module generates book cover images using SiliconFlow's image generation API
based on the book title and table of contents.

Supports two modes:
1. Illustration mode: Generate themed illustration for cover background
2. Full cover mode: Generate complete cover with illustration background
"""

import os
import re
import requests
import tempfile
from pathlib import Path
from typing import Optional, List, Tuple
from PIL import Image, ImageDraw, ImageFont, ImageFilter


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

        Generates a full-bleed themed illustration that fills the entire cover.
        The illustration is designed for text overlay (title, author will be added programmatically).

        Args:
            title: Book title
            chapters: List of chapter titles
            author: Author name
            style: Cover style

        Returns:
            Prompt string for image generation
        """
        # Analyze title and chapters to extract themes and subject
        themes = self._extract_themes(title, chapters)
        subject = self._extract_subject(title, chapters)

        # Build illustration prompt based on book subject
        illustration_prompt = self._build_illustration_prompt(subject, themes, style)

        return illustration_prompt

    def _extract_subject(
        self,
        title: str,
        chapters: Optional[List[str]] = None
    ) -> str:
        """
        Extract the main subject/category of the book for illustration generation.

        Args:
            title: Book title
            chapters: List of chapter titles

        Returns:
            Subject description for illustration
        """
        all_text = title
        if chapters:
            all_text += " " + " ".join(chapters[:10])

        # Subject mapping with specific illustration elements
        subject_keywords = {
            # 技术类
            "architecture": {
                "keywords": ["架构", "架构师", "系统", "微服务", "分布式", "设计模式", "软件"],
                "illustration": "software architecture blueprints, server racks, network diagrams, code flowing like rivers, circuit board patterns, floating geometric structures representing modules and components, technical schematics with glowing nodes"
            },
            "programming": {
                "keywords": ["编程", "代码", "程序", "开发", "算法", "数据结构", "Python", "Java", "Go"],
                "illustration": "cascading code streams, abstract binary patterns, glowing syntax highlighting colors, programming symbols forming landscapes, developer tools transforming into art"
            },
            "ai": {
                "keywords": ["AI", "人工智能", "机器学习", "深度学习", "神经网络", "GPT", "LLM"],
                "illustration": "neural network visualization with glowing nodes, robot silhouettes, digital brain patterns, data streams converging into intelligence, futuristic AI landscape"
            },
            # 商业管理类
            "business": {
                "keywords": ["商业", "企业", "管理", "创业", "公司", "市场", "营销", "战略", "领导"],
                "illustration": "abstract business growth charts as mountain peaks, interconnected gears and people silhouettes, city skyline with data overlays, professional geometric patterns suggesting progress and teamwork"
            },
            "finance": {
                "keywords": ["金融", "经济", "货币", "投资", "财富", "股票", "基金", "理财", "资产"],
                "illustration": "golden coins and charts forming abstract art, currency symbols in elegant patterns, financial growth visualization as ascending stairs, wealth represented through artistic golden streams"
            },
            # 科技类
            "internet": {
                "keywords": ["互联网", "网络", "电商", "平台", "产品", "运营", "流量"],
                "illustration": "global network connections, data flowing across continents, digital marketplace visualization, user icons connecting in patterns, web of light representing connectivity"
            },
            # 哲学思想类
            "philosophy": {
                "keywords": ["哲学", "思想", "思维", "认知", "人生", "智慧", "道理", "逻辑", "思考"],
                "illustration": "abstract thought bubbles merging, brain-shaped constellations, zen garden patterns, philosophical symbols floating in ethereal space, light representing enlightenment"
            },
            # 历史类
            "history": {
                "keywords": ["历史", "朝代", "改革", "古代", "王朝", "皇帝", "年代", "战争", "革命"],
                "illustration": "ancient scrolls and artifacts, historical timeline as a flowing river, classical architecture silhouettes, sepia-toned historical scenes blending into modern times"
            },
            # 科学类
            "science": {
                "keywords": ["科学", "物理", "化学", "生物", "数学", "宇宙", "量子", "实验"],
                "illustration": "atomic structures and molecular patterns, mathematical equations as art, scientific instruments in abstract form, galaxy and microscopic worlds juxtaposed"
            },
            # 文学艺术类
            "literature": {
                "keywords": ["小说", "文学", "诗歌", "散文", "故事", "艺术", "音乐", "电影"],
                "illustration": "flowing ink patterns, book pages transforming into birds, artistic brushstrokes, creative inspiration represented as light, poetic imagery"
            },
            # 自我提升类
            "self-improvement": {
                "keywords": ["成长", "成功", "习惯", "时间", "效率", "学习", "方法", "技巧", "提升"],
                "illustration": "ascending stairs to light, growing tree metaphors, clock and compass motifs, person silhouette reaching upward, path from darkness to light"
            },
        }

        # Find matching subject
        for subject_name, subject_info in subject_keywords.items():
            for keyword in subject_info["keywords"]:
                if keyword in all_text:
                    return subject_info["illustration"]

        # Default: abstract knowledge/learning theme
        return "abstract flowing knowledge patterns, books transforming into light, learning journey visualization, elegant geometric shapes suggesting growth and wisdom, soft gradients with depth"

    def _build_illustration_prompt(
        self,
        subject: str,
        themes: List[str],
        style: str
    ) -> str:
        """
        Build a detailed illustration prompt for book cover.

        Creates a full-bleed illustration designed for text overlay.

        Args:
            subject: Subject illustration description
            themes: List of themes
            style: Cover style

        Returns:
            Complete illustration prompt
        """
        # Style-specific visual direction (for illustration style, not text)
        style_directions = {
            "modern": (
                "Modern minimalist style with clean lines and contemporary aesthetics. "
                "Use a cohesive color palette with 2-3 main colors. "
                "Subtle gradient backgrounds with depth. "
                "Geometric elements with soft shadows. "
            ),
            "classic": (
                "Classic elegant style with rich textures and traditional aesthetics. "
                "Use warm, sophisticated color palette. "
                "Ornate borders and decorative elements. "
                "Artistic brushwork with painterly quality. "
            ),
            "minimalist": (
                "Minimalist style with maximum negative space for text overlay. "
                "Single focal point illustration. "
                "Limited color palette with strong contrast. "
                "Clean, simple composition. "
            ),
            "artistic": (
                "Artistic expressive style with bold colors and creative interpretation. "
                "Abstract and impressionistic elements. "
                "Dynamic composition with visual impact. "
                "Unique artistic vision. "
            ),
        }

        style_direction = style_directions.get(style, style_directions["modern"])

        # Color scheme suggestions based on themes
        color_hints = self._get_color_hints(themes)

        # Build the complete illustration prompt
        # Key: NO text/letters, FULL BLEED, designed for text overlay
        prompt = (
            # Subject illustration
            f"{subject}. "
            # Style direction
            f"{style_direction}"
            # Color hints
            f"{color_hints} "
            # Technical requirements
            "Full bleed illustration covering entire canvas. "
            "No text, no letters, no words, no typography in the image. "
            "Leave upper portion relatively simple for title text overlay. "
            "Professional book cover illustration quality. "
            "High detail, visually striking, suitable for commercial publication. "
            "3:4 aspect ratio composition. "
        )

        return prompt

    def _get_color_hints(self, themes: List[str]) -> str:
        """
        Get color palette suggestions based on themes.

        Args:
            themes: List of themes

        Returns:
            Color hint string
        """
        theme_colors = {
            "technology": "Use cool blues, teals, and silver accents",
            "business": "Use navy blue, gold, and white",
            "finance": "Use gold, deep green, and cream",
            "philosophy": "Use deep purple, cream, and soft gold",
            "history": "Use warm sepia, burgundy, and aged paper tones",
            "science": "Use vibrant blues, greens, and electric accents",
            "literature": "Use rich burgundy, cream, and artistic splashes",
            "self-improvement": "Use warm oranges, blues, and white",
            "growth": "Use greens, blues, and golden yellow",
            "crisis": "Use dramatic reds, dark blues, and amber highlights",
        }

        for theme in themes:
            if theme in theme_colors:
                return theme_colors[theme]

        return "Use a harmonious professional color palette"

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

    def generate_hybrid_cover(
        self,
        title: str,
        author: Optional[str] = None,
        subtitle: Optional[str] = None,
        chapters: Optional[List[str]] = None,
        output_path: Optional[str] = None,
        style: str = "modern",
        image_size: str = None
    ) -> Tuple[bool, str]:
        """
        Generate a complete book cover with AI illustration + text overlay.

        This method:
        1. Generates a themed illustration using AI (no text)
        2. Overlays title, author, and subtitle using proper fonts

        Args:
            title: Book title
            author: Author name
            subtitle: Subtitle or tagline
            chapters: List of chapter titles for theme extraction
            output_path: Where to save the final cover
            style: Cover style
            image_size: Image size in "widthxheight" format

        Returns:
            Tuple of (success: bool, image_path: str or error_message: str)
        """
        size = image_size or self.DEFAULT_SIZE

        # Step 1: Generate illustration background
        prompt = self._build_prompt(title, chapters, author, style)

        try:
            image_url = self._call_api(prompt, size)
        except Exception as e:
            return False, f"AI illustration generation failed: {str(e)}"

        # Step 2: Download illustration
        try:
            temp_path = self._download_image(image_url, None, title)
        except Exception as e:
            return False, f"Illustration download failed: {str(e)}"

        # Step 3: Add text overlay
        try:
            final_path = self._add_text_overlay(
                illustration_path=temp_path,
                title=title,
                author=author,
                subtitle=subtitle,
                output_path=output_path,
                style=style
            )

            # Clean up temp file if different from output
            if temp_path != final_path:
                Path(temp_path).unlink(missing_ok=True)

            return True, final_path
        except Exception as e:
            return False, f"Text overlay failed: {str(e)}"

    def _add_text_overlay(
        self,
        illustration_path: str,
        title: str,
        author: Optional[str],
        subtitle: Optional[str],
        output_path: Optional[str],
        style: str
    ) -> str:
        """
        Add text overlay to illustration background.

        Layout:
        - Top 30%: Title area with semi-transparent overlay
        - Middle: Illustration (visible)
        - Bottom 20%: Author name

        Args:
            illustration_path: Path to AI-generated illustration
            title: Book title
            author: Author name
            subtitle: Subtitle
            output_path: Output path
            style: Style for font selection

        Returns:
            Path to final cover image
        """
        # Load illustration
        img = Image.open(illustration_path)
        width, height = img.size
        draw = ImageDraw.Draw(img)

        # Load fonts
        fonts = self._load_cover_fonts()

        # Add semi-transparent overlay at top for better text readability
        overlay_height = int(height * 0.35)
        overlay = Image.new('RGBA', (width, overlay_height), (0, 0, 0, 0))
        overlay_draw = ImageDraw.Draw(overlay)

        # Gradient overlay (top to transparent)
        for y in range(overlay_height):
            alpha = int(120 * (1 - y / overlay_height))  # Fade from 120 to 0
            overlay_draw.line([(0, y), (width, y)], fill=(0, 0, 0, alpha))

        # Paste overlay onto image
        img = img.convert('RGBA')
        img.paste(overlay, (0, 0), overlay)
        draw = ImageDraw.Draw(img)

        # Draw title (centered, top third)
        title_font = fonts['title']
        title_lines = self._wrap_text_for_cover(title, title_font, width - 80)
        title_y = height * 0.12

        for line in title_lines:
            bbox = draw.textbbox((0, 0), line, font=title_font)
            text_width = bbox[2] - bbox[0]
            x = (width - text_width) / 2

            # Draw text shadow for better visibility
            draw.text((x + 2, title_y + 2), line, font=title_font, fill=(0, 0, 0, 180))
            draw.text((x, title_y), line, font=title_font, fill=(255, 255, 255, 255))
            title_y += title_font.size + 15

        # Draw subtitle if provided
        if subtitle:
            subtitle_font = fonts['subtitle']
            bbox = draw.textbbox((0, 0), subtitle, font=subtitle_font)
            text_width = bbox[2] - bbox[0]
            x = (width - text_width) / 2
            y = height * 0.28

            draw.text((x + 1, y + 1), subtitle, font=subtitle_font, fill=(0, 0, 0, 150))
            draw.text((x, y), subtitle, font=subtitle_font, fill=(220, 220, 220, 255))

        # Draw decorative line
        line_y = height * 0.32
        line_width = min(200, width * 0.3)
        line_x = (width - line_width) / 2
        draw.rectangle(
            [line_x, line_y, line_x + line_width, line_y + 3],
            fill=(255, 255, 255, 200)
        )

        # Draw author at bottom
        if author:
            author_font = fonts['author']
            author_text = f"{author} 著"
            bbox = draw.textbbox((0, 0), author_text, font=author_font)
            text_width = bbox[2] - bbox[0]
            x = (width - text_width) / 2
            y = height - 120

            # Add subtle background for author
            padding = 20
            bg_bbox = [
                x - padding, y - 10,
                x + text_width + padding, y + author_font.size + 10
            ]
            draw.rectangle(bg_bbox, fill=(0, 0, 0, 100))

            draw.text((x + 1, y + 1), author_text, font=author_font, fill=(0, 0, 0, 150))
            draw.text((x, y), author_text, font=author_font, fill=(255, 255, 255, 255))

        # Convert back to RGB and save
        img = img.convert('RGB')

        if output_path:
            final_path = output_path
        else:
            safe_title = re.sub(r'[^\w\s-]', '', title)[:30].strip()
            safe_title = re.sub(r'[-\s]+', '_', safe_title)
            final_path = str(Path(illustration_path).parent / f"cover_{safe_title}_final.jpg")

        img.save(final_path, 'JPEG', quality=95)
        return final_path

    def _load_cover_fonts(self) -> dict:
        """
        Load fonts for cover text rendering.

        Returns:
            Dictionary with 'title', 'subtitle', 'author' fonts
        """
        fonts = {}

        # Try to load Chinese fonts
        font_candidates = [
            # macOS
            "/System/Library/Fonts/PingFang.ttc",
            "/System/Library/Fonts/Hiragino Sans GB.ttc",
            "/System/Library/Fonts/STHeiti Light.ttc",
            # Windows
            "C:/Windows/Fonts/msyh.ttc",
            "C:/Windows/Fonts/simhei.ttf",
            "C:/Windows/Fonts/simsun.ttc",
            # Linux
            "/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf",
            "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
            "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        ]

        font_path = None
        for candidate in font_candidates:
            if candidate and os.path.exists(candidate):
                font_path = candidate
                break

        try:
            if font_path:
                fonts['title'] = ImageFont.truetype(font_path, 68)
                fonts['subtitle'] = ImageFont.truetype(font_path, 32)
                fonts['author'] = ImageFont.truetype(font_path, 36)
            else:
                fonts['title'] = ImageFont.load_default()
                fonts['subtitle'] = ImageFont.load_default()
                fonts['author'] = ImageFont.load_default()
        except Exception:
            fonts['title'] = ImageFont.load_default()
            fonts['subtitle'] = ImageFont.load_default()
            fonts['author'] = ImageFont.load_default()

        return fonts

    def _wrap_text_for_cover(
        self,
        text: str,
        font: ImageFont.FreeTypeFont,
        max_width: int
    ) -> List[str]:
        """
        Wrap text to fit within max_width for cover display.

        Args:
            text: Text to wrap
            font: Font to use
            max_width: Maximum width per line

        Returns:
            List of text lines
        """
        # For Chinese text, check character by character
        if all('\u4e00' <= c <= '\u9fff' or c in '，。、：；！？""''（）—…' for c in text):
            lines = []
            current_line = ""

            for char in text:
                test_line = current_line + char
                bbox = font.getbbox(test_line)
                width = bbox[2] - bbox[0]

                if width <= max_width:
                    current_line = test_line
                else:
                    if current_line:
                        lines.append(current_line)
                    current_line = char

            if current_line:
                lines.append(current_line)

            return lines if lines else [text]

        # For mixed or English text, use word-based wrapping
        words = text.split()
        lines = []
        current_line = []

        for word in words:
            test_line = ' '.join(current_line + [word])
            bbox = font.getbbox(test_line)
            width = bbox[2] - bbox[0]

            if width <= max_width:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                current_line = [word]

        if current_line:
            lines.append(' '.join(current_line))

        return lines if lines else [text]


def generate_cover_from_markdown(
    title: str,
    chapters: Optional[List[str]] = None,
    author: Optional[str] = None,
    output_path: Optional[str] = None,
    style: str = "modern",
    api_key: Optional[str] = None
) -> Tuple[bool, str]:
    """
    Convenience function to generate a book cover (illustration only, no text).

    For complete covers with text overlay, use generate_hybrid_cover() instead.

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


def generate_hybrid_cover(
    title: str,
    author: Optional[str] = None,
    subtitle: Optional[str] = None,
    chapters: Optional[List[str]] = None,
    output_path: Optional[str] = None,
    style: str = "modern",
    api_key: Optional[str] = None
) -> Tuple[bool, str]:
    """
    Generate a complete book cover with AI illustration + text overlay.

    This is the recommended method for generating professional book covers:
    - AI generates a themed illustration that fills the entire cover
    - Chinese/English text (title, author, subtitle) is rendered with proper fonts
    - Layout: Title at top, illustration in middle, author at bottom

    Args:
        title: Book title (supports Chinese, English, and other languages)
        author: Author name
        subtitle: Optional subtitle or tagline
        chapters: List of chapter titles for theme extraction
        output_path: Where to save the final cover image
        style: Cover style ('modern', 'classic', 'minimalist', 'artistic')
        api_key: SiliconFlow API key (optional, uses env var if not provided)

    Returns:
        Tuple of (success: bool, image_path or error_message: str)
    """
    try:
        generator = CoverGenerator(api_key=api_key)
        return generator.generate_hybrid_cover(
            title=title,
            author=author,
            subtitle=subtitle,
            chapters=chapters,
            output_path=output_path,
            style=style
        )
    except ValueError as e:
        return False, str(e)


if __name__ == "__main__":
    # Example usage
    import sys

    if len(sys.argv) < 2:
        print("Usage: python cover_generator.py <book_title> [--author <name>] [--hybrid]")
        print("")
        print("Options:")
        print("  --author <name>  Specify author name")
        print("  --hybrid         Generate hybrid cover with text overlay (recommended)")
        print("")
        print("Examples:")
        print("  python cover_generator.py '架构师之路' --author '沈剑' --hybrid")
        sys.exit(1)

    # Parse arguments
    book_title = sys.argv[1]
    author_name = None
    use_hybrid = False

    i = 2
    while i < len(sys.argv):
        if sys.argv[i] == '--author' and i + 1 < len(sys.argv):
            author_name = sys.argv[i + 1]
            i += 2
        elif sys.argv[i] == '--hybrid':
            use_hybrid = True
            i += 1
        else:
            i += 1

    print(f"Generating cover for: {book_title}")
    if author_name:
        print(f"Author: {author_name}")
    if use_hybrid:
        print("Mode: Hybrid (AI illustration + text overlay)")

    if use_hybrid:
        success, result = generate_hybrid_cover(
            title=book_title,
            author=author_name,
            style="modern"
        )
    else:
        success, result = generate_cover_from_markdown(
            title=book_title,
            author=author_name,
            style="modern"
        )

    if success:
        print(f"Cover generated successfully: {result}")
    else:
        print(f"Failed to generate cover: {result}")
        sys.exit(1)
