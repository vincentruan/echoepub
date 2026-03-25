#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
图片描述生成器

结合章节上下文和图片内容，调用第三方视觉模型生成一段连贯的中文描述，
使读者即使不看图片，也能通过文字理解上下文的完整信息。

支持模式:
- 描述模式（默认）: 为图片生成中文描述
- OCR模式 (--ocr-code): 识别代码截图，提取代码文本
"""

import re
import os
import argparse
import json
import hashlib
from pathlib import Path
from typing import Optional, Tuple, Dict, List


class ImageDescriptionCache:
    """Cache for image descriptions to avoid re-processing."""

    def __init__(self, cache_dir: str = None):
        if cache_dir:
            self.cache_dir = Path(cache_dir)
        else:
            self.cache_dir = Path.home() / '.cache' / 'echoepub' / 'image_descriptions'
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache_file = self.cache_dir / 'descriptions_cache.json'
        self.cache = self._load_cache()

    def _load_cache(self) -> Dict:
        """Load cache from file."""
        if self.cache_file.exists():
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {}
        return {}

    def _save_cache(self) -> None:
        """Save cache to file."""
        with open(self.cache_file, 'w', encoding='utf-8') as f:
            json.dump(self.cache, f, ensure_ascii=False, indent=2)

    def _get_cache_key(self, image_path: str) -> str:
        """Generate cache key from image path and modification time."""
        path = Path(image_path)
        mtime = path.stat().st_mtime if path.exists() else 0
        content = f"{image_path}:{mtime}"
        return hashlib.md5(content.encode()).hexdigest()

    def get(self, image_path: str) -> Optional[str]:
        """Get cached description if available."""
        key = self._get_cache_key(image_path)
        entry = self.cache.get(key)
        if entry:
            return entry.get('description')
        return None

    def set(self, image_path: str, description: str) -> None:
        """Cache a description."""
        key = self._get_cache_key(image_path)
        self.cache[key] = {
            'path': image_path,
            'description': description,
            'timestamp': os.path.getmtime(image_path) if Path(image_path).exists() else 0
        }
        self._save_cache()

    def clear(self) -> None:
        """Clear the cache."""
        self.cache = {}
        if self.cache_file.exists():
            self.cache_file.unlink()


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

    def __init__(self, use_cache: bool = True):
        self.cache = ImageDescriptionCache() if use_cache else None

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

        # Check cache first
        if self.cache:
            cached = self.cache.get(image_path)
            if cached:
                return cached, None

        try:
            from openai_client import get_openai_client
            client = get_openai_client()

            description = client.analyze_image(
                image_path,
                context=context,
            )

            if description:
                description = description.strip()
                # Cache the result
                if self.cache:
                    self.cache.set(image_path, description)
                return description, None
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
    auto_ocr_code: bool = True,
) -> Tuple[str, Dict]:
    """
    处理 Markdown 中的图片，调用视觉模型获取描述。

    注意：此函数仅返回 API 的原始描述，不添加引用块格式。
    引用块格式和上下文总结由 Agent 在 skill.md 指导下完成。

    Args:
        markdown_content: 原始 Markdown 内容
        images_dir: 图片目录路径
        descriptor: ImageDescriptor 实例（为 None 时跳过 AI 处理）
        auto_ocr_code: 是否自动检测并 OCR 代码截图（默认 True）

    Returns:
        (processed_markdown, stats_dict)
    """
    use_ai = descriptor is not None

    # Import OCR module if auto-ocr is enabled
    ocr_instance = None
    if auto_ocr_code:
        try:
            from code_image_ocr import CodeImageOCR
            ocr_instance = CodeImageOCR()
        except ImportError:
            pass  # OCR module not available, skip

    lines = markdown_content.split('\n')
    processed_lines = []

    stats = {
        'total_images': 0,
        'described': 0,
        'ocr_success': 0,
        'ocr_failed': 0,
        'skipped': 0,
        'failed': 0,
        'failed_images': [],
    }

    i = 0
    while i < len(lines):
        line = lines[i]
        img_match = re.match(r'^!\[([^\]]*)\]\(([^)]+)\)', line)

        if not img_match:
            processed_lines.append(line)
            i += 1
            continue

        stats['total_images'] += 1
        alt_text, img_path = img_match.groups()

        # 提取上下文：前后各 10 行
        ctx_start = max(0, i - 10)
        ctx_end = min(len(lines), i + 11)
        context = '\n'.join(
            lines[ctx_start:i] + lines[i + 1:ctx_end]
        )

        # 解析图片实际路径
        if img_path.startswith(('http://', 'https://')):
            stats['skipped'] += 1
            processed_lines.append(line)
            i += 1
            continue

        img_path_clean = img_path.lstrip('./')
        if img_path_clean.startswith('images/'):
            full_image_path = Path(images_dir).parent / img_path_clean
        else:
            full_image_path = Path(images_dir) / img_path_clean

        # 检查是否跳过
        if use_ai and descriptor.should_skip(context, alt_text, str(full_image_path)):
            stats['skipped'] += 1
            processed_lines.append(line)
            i += 1
            continue

        # Step 1: 尝试 OCR 代码截图检测
        is_code_screenshot = False
        if ocr_instance and use_ai:
            is_code, _ = ocr_instance.is_likely_code_screenshot(str(full_image_path), context)
            if is_code:
                is_code_screenshot = True
                code_block, failure_reason = ocr_instance.ocr_code_image(
                    str(full_image_path), context
                )
                if code_block:
                    # 替换图片引用为代码块
                    processed_lines.append(f"<!-- Code extracted from: {img_path} -->")
                    processed_lines.append("")
                    processed_lines.append(code_block)
                    processed_lines.append("")
                    stats['ocr_success'] += 1
                    i += 1
                    continue
                else:
                    stats['ocr_failed'] += 1
                    # OCR 失败，继续尝试生成描述

        # Step 2: 生成图片描述
        if use_ai:
            description, failure_reason = descriptor.describe(
                str(full_image_path), context
            )

            if description:
                processed_lines.append(line)
                # 以特殊标记输出，供 Agent 后续处理
                processed_lines.append("")
                processed_lines.append(f"<!-- IMAGE_DESCRIPTION: {description} -->")
                processed_lines.append("")
                stats['described'] += 1
            else:
                processed_lines.append(line)
                stats['failed'] += 1
                stats['failed_images'].append(
                    (str(full_image_path), failure_reason)
                )
        else:
            processed_lines.append(line)
            stats['skipped'] += 1

        i += 1

    return '\n'.join(processed_lines), stats


def ocr_images_in_markdown(
    markdown_content: str,
    images_dir: str,
    ocr_instance=None,
) -> Tuple[str, Dict]:
    """
    处理 Markdown 中的图片，使用 OCR 提取代码文本。

    识别代码截图并提取其中的代码，替换图片引用为 ``` 代码块。

    Args:
        markdown_content: 原始 Markdown 内容
        images_dir: 图片目录路径
        ocr_instance: CodeImageOCR 实例

    Returns:
        (processed_markdown, stats_dict)
    """
    from code_image_ocr import CodeImageOCR, get_ocr_instance

    if ocr_instance is None:
        ocr_instance = get_ocr_instance()

    lines = markdown_content.split('\n')
    processed_lines = []

    stats = {
        'total_images': 0,
        'ocr_success': 0,
        'ocr_failed': 0,
        'skipped': 0,
        'failed_images': [],
        'ocr_results': [],  # Store (image_path, code) tuples
    }

    i = 0
    while i < len(lines):
        line = lines[i]
        img_match = re.match(r'^!\[([^\]]*)\]\(([^)]+)\)', line)

        if not img_match:
            processed_lines.append(line)
            i += 1
            continue

        stats['total_images'] += 1
        alt_text, img_path = img_match.groups()

        # 提取上下文：前后各 10 行
        ctx_start = max(0, i - 10)
        ctx_end = min(len(lines), i + 11)
        context = '\n'.join(
            lines[ctx_start:i] + lines[i + 1:ctx_end]
        )

        # 解析图片实际路径
        if img_path.startswith(('http://', 'https://')):
            stats['skipped'] += 1
            processed_lines.append(line)
            i += 1
            continue

        img_path_clean = img_path.lstrip('./')
        if img_path_clean.startswith('images/'):
            full_image_path = Path(images_dir).parent / img_path_clean
        else:
            full_image_path = Path(images_dir) / img_path_clean

        # 尝试 OCR 提取代码
        code_block, failure_reason = ocr_instance.ocr_code_image(
            str(full_image_path), context
        )

        if code_block:
            # 替换图片引用为代码块
            processed_lines.append(f"<!-- Original image: {img_path} -->")
            processed_lines.append("")
            processed_lines.append(code_block)
            processed_lines.append("")
            stats['ocr_success'] += 1
            stats['ocr_results'].append((str(full_image_path), code_block[:100] + '...'))
        else:
            # OCR 失败，保留图片引用
            processed_lines.append(line)
            stats['ocr_failed'] += 1
            stats['failed_images'].append((str(full_image_path), failure_reason))

        i += 1

    return '\n'.join(processed_lines), stats


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='处理 Markdown 中的图片'
    )
    parser.add_argument('markdown_file', help='Markdown 文件路径')
    parser.add_argument('images_dir', help='图片目录路径')
    parser.add_argument('--ocr-code', action='store_true',
                        help='OCR 模式：识别代码截图并提取代码文本')
    parser.add_argument('--no-auto-ocr', action='store_true',
                        help='禁用自动代码截图 OCR 检测')

    args = parser.parse_args()

    md_file = args.markdown_file
    images_dir = args.images_dir

    with open(md_file, 'r', encoding='utf-8') as f:
        content = f.read()

    if args.ocr_code:
        # 纯 OCR 模式：提取代码截图中的代码
        processed, stats = ocr_images_in_markdown(content, images_dir)

        print(f"处理 {stats['total_images']} 张图片 (OCR 模式)")
        print(f"  OCR 成功: {stats['ocr_success']}")
        print(f"  OCR 失败: {stats['ocr_failed']}")
        print(f"  已跳过: {stats['skipped']}")

        if stats['failed_images']:
            print("\n失败详情:")
            for img_path, reason in stats['failed_images']:
                print(f"  - {img_path}: {reason}")

        output_file = Path(md_file).parent / f"{Path(md_file).stem}_with_ocr.md"
    else:
        # 描述模式：生成图片描述（默认自动 OCR 代码截图）
        desc = ImageDescriptor()
        auto_ocr = not args.no_auto_ocr
        processed, stats = describe_images_in_markdown(content, images_dir, desc, auto_ocr_code=auto_ocr)

        print(f"处理 {stats['total_images']} 张图片")
        print(f"  已描述: {stats['described']}")
        if stats.get('ocr_success', 0) > 0:
            print(f"  OCR 代码: {stats['ocr_success']}")
        if stats.get('ocr_failed', 0) > 0:
            print(f"  OCR 失败: {stats['ocr_failed']}")
        print(f"  已跳过: {stats['skipped']}")
        print(f"  失败: {stats['failed']}")

        if stats['failed_images']:
            print("\n失败详情:")
            for img_path, reason in stats['failed_images']:
                print(f"  - {img_path}: {reason}")

        output_file = Path(md_file).parent / f"{Path(md_file).stem}_with_descriptions.md"

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(processed)

    print(f"\n输出已保存: {output_file}")
