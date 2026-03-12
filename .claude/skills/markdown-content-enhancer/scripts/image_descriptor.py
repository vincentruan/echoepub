#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
图片描述生成器

结合章节上下文和图片内容，调用第三方视觉模型生成一段连贯的中文描述，
使读者即使不看图片，也能通过文字理解上下文的完整信息。
"""

import re
import os
from pathlib import Path
from typing import Optional, Tuple, Dict


class ImageDescriptor:
    """调用第三方视觉模型，为图片生成连贯的中文描述。"""

    # 不需要描述的图片类型（黑名单关键词）
    SKIP_PATTERNS = [
        r'二维码|qr|qrcode|微信|weixin|wechat|关注公众号',
        r'封面|cover|书皮|title.?page|扉页',
        r'作者|author|portrait|头像|照片|肖像',
        r'decoration|装饰|背景图|background|分隔线|separator',
        r'emoji|表情包|梗图|贴纸',
        r'icon|图标|badge|徽章|logo',
    ]

    # 不支持的图片格式
    UNSUPPORTED_FORMATS = {'.svg', '.ico'}

    # 跳过的最小文件大小（字节），小于此值可能是图标
    MIN_FILE_SIZE = 500  # 0.5KB - EPUB 图片通常较小

    # 跳过的最小图片尺寸（像素）
    MIN_DIMENSION = 50

    def __init__(self):
        pass

    def should_skip(self, context: str, alt_text: str = "", image_path: str = "") -> bool:
        """
        判断图片是否应跳过（不生成描述）。

        检查顺序：
        1. 关键词黑名单（文件名、alt文本、上下文）
        2. 文件大小（< 2KB 可能是图标）
        3. 图片尺寸（< 50x50px 可能是图标）
        """
        # 关键词检查
        text = f"{context} {alt_text}".lower()
        for pattern in self.SKIP_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                return True

        # 文件名关键词检查
        if image_path:
            filename = Path(image_path).stem.lower()
            for pattern in self.SKIP_PATTERNS:
                if re.search(pattern, filename, re.IGNORECASE):
                    return True

        # 文件大小检查
        if image_path and Path(image_path).exists():
            file_size = os.path.getsize(image_path)
            if file_size < self.MIN_FILE_SIZE:
                return True

            # 图片尺寸检查
            try:
                from PIL import Image
                with Image.open(image_path) as img:
                    width, height = img.size
                    if width < self.MIN_DIMENSION and height < self.MIN_DIMENSION:
                        return True
            except Exception:
                pass  # PIL 不可用或图片无法打开时跳过尺寸检查

        return False

    def describe(
        self,
        image_path: str,
        context: str = "",
    ) -> Tuple[Optional[str], Optional[str]]:
        """
        结合上下文为图片生成中文描述。

        Args:
            image_path: 图片文件路径
            context: 图片前后的章节上下文

        Returns:
            (description, failure_reason)
            - description: 生成的描述文本（纯文本，不含引用块格式），失败时为 None
            - failure_reason: 失败原因，成功时为 None
        """
        path = Path(image_path)

        if not path.exists():
            return None, "图片文件不存在"

        if path.suffix.lower() in self.UNSUPPORTED_FORMATS:
            return None, f"不支持的图片格式 {path.suffix.upper()}"

        try:
            from openai_client import get_openai_client
            client = get_openai_client()

            description = client.analyze_image(
                image_path,
                context=context,
            )

            if description:
                return description.strip(), None
            else:
                return None, "视觉模型分析未返回有效结果"

        except ImportError:
            return None, "API 客户端未安装"
        except Exception as e:
            return None, f"API 调用异常: {str(e)[:80]}"


def describe_images_in_markdown(
    markdown_content: str,
    images_dir: str,
    descriptor: Optional[ImageDescriptor] = None,
) -> Tuple[str, Dict]:
    """
    处理 Markdown 中的图片，调用视觉模型获取描述。

    注意：此函数仅返回 API 的原始描述，不添加引用块格式。
    引用块格式和上下文总结由 Agent 在 skill.md 指导下完成。

    Args:
        markdown_content: 原始 Markdown 内容
        images_dir: 图片目录路径
        descriptor: ImageDescriptor 实例（为 None 时跳过 AI 处理）

    Returns:
        (processed_markdown, stats_dict)
    """
    use_ai = descriptor is not None

    lines = markdown_content.split('\n')
    processed_lines = []

    stats = {
        'total_images': 0,
        'described': 0,
        'skipped': 0,
        'failed': 0,
        'failed_images': [],
    }

    for i, line in enumerate(lines):
        img_match = re.match(r'^!\[([^\]]*)\]\(([^)]+)\)', line)

        if not img_match:
            processed_lines.append(line)
            continue

        stats['total_images'] += 1
        alt_text, img_path = img_match.groups()

        processed_lines.append(line)

        if not use_ai:
            stats['skipped'] += 1
            continue

        # 提取上下文：前后各 10 行
        ctx_start = max(0, i - 10)
        ctx_end = min(len(lines), i + 11)
        context = '\n'.join(
            lines[ctx_start:i] + lines[i + 1:ctx_end]
        )

        # 解析图片实际路径
        if img_path.startswith(('http://', 'https://')):
            stats['skipped'] += 1
            continue

        img_path_clean = img_path.lstrip('./')
        if img_path_clean.startswith('images/'):
            full_image_path = Path(images_dir).parent / img_path_clean
        else:
            full_image_path = Path(images_dir) / img_path_clean

        # 检查是否跳过
        if descriptor.should_skip(context, alt_text, str(full_image_path)):
            stats['skipped'] += 1
            continue

        # 生成描述
        description, failure_reason = descriptor.describe(
            str(full_image_path), context
        )

        if description:
            # 以特殊标记输出，供 Agent 后续处理
            processed_lines.append("")
            processed_lines.append(f"<!-- IMAGE_DESCRIPTION: {description} -->")
            processed_lines.append("")
            stats['described'] += 1
        else:
            stats['failed'] += 1
            stats['failed_images'].append(
                (str(full_image_path), failure_reason)
            )

    return '\n'.join(processed_lines), stats


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 3:
        print("Usage: python image_descriptor.py <markdown_file> <images_dir>")
        sys.exit(1)

    md_file = sys.argv[1]
    images_dir = sys.argv[2]

    with open(md_file, 'r', encoding='utf-8') as f:
        content = f.read()

    desc = ImageDescriptor()
    processed, stats = describe_images_in_markdown(content, images_dir, desc)

    print(f"处理 {stats['total_images']} 张图片")
    print(f"  已描述: {stats['described']}")
    print(f"  已跳过: {stats['skipped']}")
    print(f"  失败: {stats['failed']}")

    output_file = Path(md_file).parent / f"{Path(md_file).stem}_with_descriptions.md"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(processed)

    print(f"\n输出已保存: {output_file}")
