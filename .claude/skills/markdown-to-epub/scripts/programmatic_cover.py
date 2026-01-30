"""
Programmatic cover generation using Pillow.

This module generates book covers using direct image manipulation
instead of AI, ensuring perfect text rendering for Chinese characters.
"""

import os
from pathlib import Path
from typing import Optional, Tuple
from PIL import Image, ImageDraw, ImageFont, ImageFilter


class ProgrammaticCoverGenerator:
    """Generate book covers programmatically using Pillow."""

    # 预设颜色方案
    COLOR_SCHEMES = {
        "modern": {
            "bg_top": (45, 55, 72),      # 深蓝灰
            "bg_bottom": (26, 32, 44),    # 更深的蓝灰
            "accent": (66, 153, 225),     # 亮蓝
            "title": (255, 255, 255),     # 白色
            "subtitle": (203, 213, 224),  # 浅灰
            "author": (160, 174, 192),    # 中灰
        },
        "classic": {
            "bg_top": (139, 69, 19),      # 棕色
            "bg_bottom": (101, 67, 33),   # 深棕
            "accent": (218, 165, 32),     # 金色
            "title": (255, 248, 220),     # 米白
            "subtitle": (245, 222, 179),  # 小麦色
            "author": (222, 184, 135),    # 浅棕
        },
        "minimalist": {
            "bg_top": (255, 255, 255),    # 白色
            "bg_bottom": (247, 250, 252), # 浅灰白
            "accent": (49, 130, 206),     # 蓝色
            "title": (26, 32, 44),        # 深灰
            "subtitle": (74, 85, 104),    # 中灰
            "author": (113, 128, 150),    # 浅灰
        },
        "elegant": {
            "bg_top": (31, 41, 55),       # 深灰蓝
            "bg_bottom": (17, 24, 39),    # 接近黑色
            "accent": (167, 139, 250),    # 紫色
            "title": (243, 244, 246),     # 浅灰白
            "subtitle": (209, 213, 219),  # 灰白
            "author": (156, 163, 175),    # 中灰
        },
        "warm": {
            "bg_top": (120, 40, 31),      # 深红棕
            "bg_bottom": (76, 29, 24),    # 更深的红棕
            "accent": (251, 191, 36),     # 金黄
            "title": (254, 252, 232),     # 暖白
            "subtitle": (254, 243, 199),  # 浅黄
            "author": (253, 224, 71),     # 金黄
        },
    }

    def __init__(self, width: int = 768, height: int = 1024):
        """
        Initialize cover generator.

        Args:
            width: Cover width in pixels
            height: Cover height in pixels
        """
        self.width = width
        self.height = height

    def generate(
        self,
        title: str,
        author: Optional[str] = None,
        subtitle: Optional[str] = None,
        output_path: str = "cover.jpg",
        style: str = "modern",
        font_path: Optional[str] = None
    ) -> Tuple[bool, str]:
        """
        Generate a book cover.

        Args:
            title: Book title
            author: Author name
            subtitle: Subtitle or tagline
            output_path: Output file path
            style: Color scheme ('modern', 'classic', 'minimalist', 'elegant', 'warm')
            font_path: Path to custom font file (optional)

        Returns:
            Tuple of (success: bool, path or error message: str)
        """
        try:
            # 创建图像
            img = Image.new('RGB', (self.width, self.height), color='white')
            draw = ImageDraw.Draw(img)

            # 获取颜色方案
            colors = self.COLOR_SCHEMES.get(style, self.COLOR_SCHEMES['modern'])

            # 绘制渐变背景
            self._draw_gradient_background(img, colors['bg_top'], colors['bg_bottom'])

            # 绘制装饰元素
            self._draw_decorative_elements(img, colors['accent'])

            # 加载字体
            fonts = self._load_fonts(font_path)

            # 重新创建draw对象（因为背景被修改了）
            draw = ImageDraw.Draw(img)

            # 绘制书名
            self._draw_title(draw, title, fonts['title'], colors['title'])

            # 绘制副标题
            if subtitle:
                self._draw_subtitle(draw, subtitle, fonts['subtitle'], colors['subtitle'])

            # 绘制作者
            if author:
                self._draw_author(draw, author, fonts['author'], colors['author'])

            # 绘制装饰线
            self._draw_accent_lines(draw, colors['accent'])

            # 保存图像
            img.save(output_path, 'JPEG', quality=95)
            return True, output_path

        except Exception as e:
            return False, f"Cover generation failed: {str(e)}"

    def _draw_gradient_background(
        self,
        img: Image.Image,
        color_top: Tuple[int, int, int],
        color_bottom: Tuple[int, int, int]
    ):
        """Draw a vertical gradient background."""
        for y in range(self.height):
            # 计算当前行的颜色
            ratio = y / self.height
            r = int(color_top[0] * (1 - ratio) + color_bottom[0] * ratio)
            g = int(color_top[1] * (1 - ratio) + color_bottom[1] * ratio)
            b = int(color_top[2] * (1 - ratio) + color_bottom[2] * ratio)

            # 绘制这一行
            draw = ImageDraw.Draw(img)
            draw.line([(0, y), (self.width, y)], fill=(r, g, b))

    def _draw_decorative_elements(self, img: Image.Image, accent_color: Tuple[int, int, int]):
        """Draw decorative elements on the cover."""
        draw = ImageDraw.Draw(img)

        # 绘制几何图案
        # 左上角三角形
        triangle_size = 120
        draw.polygon(
            [(0, 0), (triangle_size, 0), (0, triangle_size)],
            fill=accent_color + (50,) if len(accent_color) == 3 else accent_color
        )

        # 右下角圆形
        circle_size = 150
        circle_x = self.width - circle_size
        circle_y = self.height - circle_size
        draw.ellipse(
            [circle_x, circle_y, self.width, self.height],
            fill=accent_color + (30,) if len(accent_color) == 3 else accent_color
        )

    def _load_fonts(self, custom_font_path: Optional[str] = None) -> dict:
        """
        Load fonts for title, subtitle, and author.

        Returns:
            Dictionary with 'title', 'subtitle', and 'author' fonts
        """
        fonts = {}

        # 尝试加载系统中文字体
        font_candidates = [
            custom_font_path,
            # macOS 中文字体
            "/System/Library/Fonts/PingFang.ttc",
            "/System/Library/Fonts/Hiragino Sans GB.ttc",
            "/System/Library/Fonts/STHeiti Light.ttc",
            # Windows 中文字体
            "C:/Windows/Fonts/msyh.ttc",      # 微软雅黑
            "C:/Windows/Fonts/simhei.ttf",    # 黑体
            "C:/Windows/Fonts/simsun.ttc",    # 宋体
            # Linux 中文字体
            "/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf",
            "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
        ]

        # 找到第一个可用的字体
        font_path = None
        for candidate in font_candidates:
            if candidate and os.path.exists(candidate):
                font_path = candidate
                break

        try:
            if font_path:
                fonts['title'] = ImageFont.truetype(font_path, 72)
                fonts['subtitle'] = ImageFont.truetype(font_path, 36)
                fonts['author'] = ImageFont.truetype(font_path, 42)
            else:
                # 使用默认字体
                fonts['title'] = ImageFont.load_default()
                fonts['subtitle'] = ImageFont.load_default()
                fonts['author'] = ImageFont.load_default()
        except Exception:
            # 如果加载失败，使用默认字体
            fonts['title'] = ImageFont.load_default()
            fonts['subtitle'] = ImageFont.load_default()
            fonts['author'] = ImageFont.load_default()

        return fonts

    def _draw_title(
        self,
        draw: ImageDraw.Draw,
        title: str,
        font: ImageFont.FreeTypeFont,
        color: Tuple[int, int, int]
    ):
        """Draw the book title."""
        # 处理长标题，自动换行
        max_width = self.width - 100  # 留边距
        lines = self._wrap_text(title, font, max_width)

        # 计算总高度
        line_height = font.size + 20
        total_height = len(lines) * line_height

        # 从中上部开始绘制
        y = self.height * 0.35 - total_height / 2

        for line in lines:
            # 获取文本边界框
            bbox = draw.textbbox((0, 0), line, font=font)
            text_width = bbox[2] - bbox[0]

            # 居中绘制
            x = (self.width - text_width) / 2
            draw.text((x, y), line, font=font, fill=color)
            y += line_height

    def _draw_subtitle(
        self,
        draw: ImageDraw.Draw,
        subtitle: str,
        font: ImageFont.FreeTypeFont,
        color: Tuple[int, int, int]
    ):
        """Draw the subtitle."""
        # 获取文本边界框
        bbox = draw.textbbox((0, 0), subtitle, font=font)
        text_width = bbox[2] - bbox[0]

        # 在标题下方绘制
        x = (self.width - text_width) / 2
        y = self.height * 0.55
        draw.text((x, y), subtitle, font=font, fill=color)

    def _draw_author(
        self,
        draw: ImageDraw.Draw,
        author: str,
        font: ImageFont.FreeTypeFont,
        color: Tuple[int, int, int]
    ):
        """Draw the author name."""
        # 在底部绘制
        text = f"作者：{author}"
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]

        x = (self.width - text_width) / 2
        y = self.height - 150
        draw.text((x, y), text, font=font, fill=color)

    def _draw_accent_lines(self, draw: ImageDraw.Draw, color: Tuple[int, int, int]):
        """Draw decorative accent lines."""
        # 标题上方的装饰线
        line_width = 200
        line_x = (self.width - line_width) / 2
        line_y = self.height * 0.25

        draw.rectangle(
            [line_x, line_y, line_x + line_width, line_y + 4],
            fill=color
        )

        # 标题下方的装饰线
        line_y2 = self.height * 0.65
        draw.rectangle(
            [line_x, line_y2, line_x + line_width, line_y2 + 4],
            fill=color
        )

    def _wrap_text(
        self,
        text: str,
        font: ImageFont.FreeTypeFont,
        max_width: int
    ) -> list:
        """
        Wrap text to fit within max_width.

        Returns:
            List of text lines
        """
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

        # 如果没有空格（如纯中文），按字符数分割
        if len(lines) == 1 and len(text) > 15:
            # 尝试在标点符号处分割
            for punct in ['：', '，', '、', '-', '—']:
                if punct in text:
                    parts = text.split(punct, 1)
                    return [parts[0] + punct, parts[1]] if len(parts) == 2 else [text]

            # 如果没有标点，按中间分割
            mid = len(text) // 2
            return [text[:mid], text[mid:]]

        return lines if lines else [text]


def generate_programmatic_cover(
    title: str,
    author: Optional[str] = None,
    subtitle: Optional[str] = None,
    output_path: str = "cover.jpg",
    style: str = "modern",
    width: int = 768,
    height: int = 1024
) -> Tuple[bool, str]:
    """
    Convenience function to generate a cover programmatically.

    Args:
        title: Book title
        author: Author name
        subtitle: Subtitle
        output_path: Output file path
        style: Color scheme
        width: Cover width
        height: Cover height

    Returns:
        Tuple of (success, path or error message)
    """
    generator = ProgrammaticCoverGenerator(width, height)
    return generator.generate(title, author, subtitle, output_path, style)
