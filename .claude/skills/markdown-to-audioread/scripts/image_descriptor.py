#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI-Powered Image Descriptor for Audiobook-Optimized EPUBs

Generates structured, speech-friendly descriptions for images, charts, and diagrams
using vision model analysis.
"""

import re
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import base64


class ImageDescriptor:
    """Generate AI-powered image descriptions for audio narration."""

    def __init__(self, rules_path: Optional[str] = None):
        """
        Initialize image descriptor.

        Args:
            rules_path: Path to image description rules markdown file
        """
        self.rules_path = rules_path
        self.description_rules = self._load_rules()

    def _load_rules(self) -> str:
        """Load image description rules from reference file."""
        if self.rules_path and Path(self.rules_path).exists():
            with open(self.rules_path, 'r', encoding='utf-8') as f:
                return f.read()
        return ""

    def encode_image_for_analysis(self, image_path: str) -> Optional[str]:
        """
        Encode image to base64 for vision model analysis.

        Args:
            image_path: Path to image file

        Returns:
            Base64 encoded string or None if failed
        """
        try:
            with open(image_path, 'rb') as f:
                return base64.b64encode(f.read()).decode('utf-8')
        except Exception as e:
            print(f"Error encoding image: {e}")
            return None

    def should_describe_image(self, context: str, alt_text: str = "") -> bool:
        """
        Determine if image should be described based on blacklist rules.

        Blacklist: Skip emoji/stickers, pure portraits, decorations, QR codes, covers, etc.

        Args:
            context: Surrounding text context
            alt_text: Alt text from image markdown

        Returns:
            True if image should be described
        """
        # Combine context and alt text for checking
        text_to_check = f"{context} {alt_text}".lower()

        # Skip patterns - images that should NOT be described
        skip_patterns = [
            # QR codes and contact images
            r'二维码|qr|qrcode|微信|weixin|wechat|关注公众号',

            # Covers and title pages
            r'封面|cover|书皮|title.?page|扉页',

            # Portraits and author photos
            r'作者|author|portrait|头像|照片|肖像',

            # Decorations and backgrounds
            r'decoration|装饰|背景图|background|分隔线|separator',

            # Emojis and stickers
            r'emoji|表情包|梗图|贴纸',

            # Icons and small UI elements
            r'icon|图标|badge|徽章|logo',
        ]

        for pattern in skip_patterns:
            if re.search(pattern, text_to_check, re.IGNORECASE):
                return False

        # Default to True - describe the image
        return True

    def build_description_prompt(
        self,
        image_type: str = "general",
        context: str = ""
    ) -> str:
        """
        Build prompt for vision model based on image type and rules.

        Args:
            image_type: Type of image (chart, flowchart, architecture, etc.)
            context: Surrounding text context

        Returns:
            Prompt string for vision model
        """
        base_prompt = """Analyze this image and generate a structured description for audio narration.

Follow this EXACT format (using blockquote with > prefix):

> **图片说明**：[Type identification in one sentence]
> **核心内容**：[Core conclusion in 1-2 sentences]
> **关键元素**：[Key elements narration]
>
> **要点总结**：
> - 第一，[point 1]
> - 第二，[point 2]
> - 第三，[point 3]
> - 第四，[point 4]
> - 第五，[point 5]

Guidelines:
- Use 3-7 summary points
- Start each point with 第一、第二、第三...
- Keep each point under 50 characters
- Focus on insights, not obvious observations
- Use **bold** for section headers (图片说明, 核心内容, 关键元素, 要点总结)
- Add blank line after 关键元素 for better separation
- For charts: narrate axes, trends, peaks, comparisons
- For flowcharts: start point, steps, branches, end point
- For architecture: components, relationships, data flow
- For screenshots: interface, key fields, status indicators
"""

        if image_type == "chart":
            base_prompt += """

Specific to charts:
- Identify X-axis and Y-axis meanings
- Describe overall trend (increasing, decreasing, stable)
- Note peak/valley points
- Compare data series
- Mention anomalies or patterns"""
        elif image_type == "flowchart":
            base_prompt += """

Specific to flowcharts:
- Identify starting point
- Describe each step or decision point
- Explain branching logic and conditions
- Identify ending point or outcomes"""
        elif image_type == "architecture":
            base_prompt += """

Specific to architecture diagrams:
- List major components
- Describe relationships and connections
- Explain data flow direction
- Note layers or tiers"""

        return base_prompt

    def describe_image_with_vision_model(
        self,
        image_path: str,
        image_context: str = "",
        use_vlm_api: bool = True
    ) -> Tuple[Optional[str], Optional[str]]:
        """
        Generate image description using vision model with error tracking.

        Args:
            image_path: Path to image file
            image_context: Surrounding text context for classification
            use_vlm_api: Whether to use VLM API (default: True)

        Returns:
            Tuple of (description_text, failure_reason)
            - description_text: Generated description, or None if failed
            - failure_reason: None if success, reason string if failed
        """
        if not Path(image_path).exists():
            return None, "Image file not found"

        # Check blacklist
        if not self.should_describe_image(image_context):
            return None, "Image skipped (blacklist pattern)"

        # Determine image type from context
        image_type = self._classify_image_type(image_context)

        # Check image format
        img_ext = Path(image_path).suffix.lower()
        unsupported_formats = {'.svg', '.ico'}
        if img_ext in unsupported_formats:
            return None, f"不支持的图片格式 {img_ext.upper()}"

        # Try to use VLM API
        if use_vlm_api:
            try:
                from siliconflow_client import get_siliconflow_client
                client = get_siliconflow_client()

                description = client.analyze_image(
                    image_path,
                    context=image_context,
                    image_type=image_type
                )

                if description:
                    return description, None
                else:
                    return None, "AI 视觉模型分析失败"

            except ImportError:
                return None, "API 客户端未安装"
            except Exception as e:
                return None, f"API 调用异常: {str(e)[:50]}"

        # VLM API disabled
        return None, "VLM API 未启用"

    def _classify_image_type(self, context: str) -> str:
        """
        Classify image type from surrounding text.

        Args:
            context: Text around image reference

        Returns:
            Image type string
        """
        context_lower = context.lower()

        if any(word in context_lower for word in ['chart', 'graph', 'figure', 'plot', '图', '图表', '曲线', '柱状']):
            return "chart"
        elif any(word in context_lower for word in ['flow', 'process', 'workflow', '流程', '流程图']):
            return "flowchart"
        elif any(word in context_lower for word in ['architecture', 'system', '架构', '系统', '架构图']):
            return "architecture"
        elif any(word in context_lower for word in ['comparison', 'compare', '对比', '比较']):
            return "comparison"
        elif any(word in context_lower for word in ['screenshot', 'interface', 'ui', '界面', '截图']):
            return "screenshot"
        elif any(word in context_lower for word in ['table', '数据表', '表格']):
            return "table"
        else:
            return "general"

    def _generate_placeholder_description(self, image_type: str, context: str, reason: str = "") -> str:
        """
        Generate structured placeholder description with review notice.

        Args:
            image_type: Type of image
            context: Surrounding context
            reason: Reason for placeholder (e.g., "API timeout", "unsupported format")

        Returns:
            Structured placeholder description in blockquote format
        """
        type_names = {
            'chart': '数据图表',
            'flowchart': '流程图',
            'architecture': '系统架构图',
            'comparison': '对比图',
            'screenshot': '界面截图',
            'table': '数据表格',
            'general': '图片'
        }

        type_name = type_names.get(image_type, '图片')
        reason_note = f"（原因：{reason}）" if reason else ""

        # Use blockquote format for better visual separation and readability
        description = f"""> **图片说明**：这是一张{type_name}。
> **核心内容**：图片描述暂未生成，建议人工审核{reason_note}。
> **关键元素**：无法识别，请查看原图片。
>
> **要点总结**：
> - 第一，该图片未能通过AI视觉模型成功分析。
> - 第二，可能因为图片模糊、格式不支持或网络问题。
> - 第三，请查看原图片以获取具体内容。
> - 第四，如需详细描述，建议人工审核。
> - 第五，后续版本可能自动修复此问题。
"""

        return description


def describe_images_in_markdown(
    markdown_content: str,
    images_dir: str,
    descriptor: Optional[ImageDescriptor] = None,
    smart_fallback: bool = True
) -> Tuple[str, Dict]:
    """
    Process markdown and add AI-generated image descriptions with failure tracking.

    Args:
        markdown_content: Original markdown text
        images_dir: Directory containing image files
        descriptor: ImageDescriptor instance (if None and smart_fallback=True, skip AI)
        smart_fallback: If True, generate placeholder descriptions for important images when AI fails

    Returns:
        Tuple of (processed_markdown, stats_dict)
        - stats_dict includes: total_images, described, skipped, failed, failed_images (list)
    """
    # Only create descriptor if explicitly provided
    # If descriptor is None, we're in smart fallback only mode (no AI processing)
    use_ai = descriptor is not None

    lines = markdown_content.split('\n')
    processed_lines = []

    stats = {
        'total_images': 0,
        'described': 0,
        'skipped': 0,
        'failed': 0,
        'failed_images': [],  # List of (image_path, reason) tuples
        'fallback_generated': 0  # Track smart fallback descriptions
    }

    i = 0
    while i < len(lines):
        line = lines[i]

        # Detect image markdown
        img_match = re.match(r'^!\[([^\]]*)\]\(([^)]+)\)', line)
        if img_match:
            stats['total_images'] += 1
            alt_text, img_path = img_match.groups()

            # Resolve image path
            if img_path.startswith('./'):
                img_path_clean = img_path[2:]
            elif img_path.startswith('/'):
                img_path_clean = img_path[1:]
            else:
                img_path_clean = img_path

            # If the path starts with 'images/', it's relative to images_dir parent
            # So we use parent / img_path_clean
            if img_path_clean.startswith('images/'):
                # images_dir is already the images subdirectory
                # so we need to go up one level and then append the full path
                full_image_path = Path(images_dir).parent / img_path_clean
            else:
                # Direct path relative to images_dir
                full_image_path = Path(images_dir) / img_path_clean

            # Get context (previous 2 lines)
            context_start = max(0, i - 2)
            context = '\n'.join(lines[context_start:i])

            processed_lines.append(line)

            # Check if we should use AI or smart fallback only
            if use_ai:
                # Use AI descriptor to check if image should be described
                if not descriptor.should_describe_image(context, alt_text):
                    # Skip this image - don't add description
                    stats['skipped'] += 1
                    i += 1
                    continue

                # Generate description using AI
                description, failure_reason = descriptor.describe_image_with_vision_model(
                    str(full_image_path),
                    context
                )

                if description:
                    # Add blank line before description for better readability
                    processed_lines.append("")
                    # Description already uses blockquote format (> prefix)
                    processed_lines.append(description)
                    # Add blank line after description
                    processed_lines.append("")

                    if failure_reason is None:
                        stats['described'] += 1
                    else:
                        # Description exists but had failure_reason (shouldn't happen, but handle it)
                        stats['described'] += 1
                else:
                    # No description generated from AI
                    if failure_reason:
                        # Attempted but failed (API error, unsupported format, etc.)

                        # Smart fallback: Check if this is an important image
                        if smart_fallback and _is_important_image(context, alt_text):
                            # Generate placeholder description in blockquote format
                            placeholder = _generate_smart_placeholder(context, alt_text, img_path_clean)
                            processed_lines.append("")  # Blank line before
                            processed_lines.append(placeholder)
                            processed_lines.append("")  # Blank line after
                            stats['described'] += 1  # Count as described (with placeholder)
                            stats['fallback_generated'] = stats.get('fallback_generated', 0) + 1
                        else:
                            stats['failed'] += 1
                            stats['failed_images'].append((str(full_image_path), failure_reason))
                    else:
                        # Explicitly skipped (blacklist pattern)
                        # Note: This branch is reached when should_describe_image() returned False
                        # which is handled earlier in the code, so this is for other skip cases
                        stats['skipped'] += 1
            else:
                # Smart fallback only mode (no AI processing)
                # Check if this is an important image
                if _is_important_image(context, alt_text):
                    # Generate placeholder description in blockquote format
                    placeholder = _generate_smart_placeholder(context, alt_text, img_path_clean)
                    processed_lines.append("")  # Blank line before
                    processed_lines.append(placeholder)
                    processed_lines.append("")  # Blank line after
                    stats['described'] += 1  # Count as described (with placeholder)
                    stats['fallback_generated'] = stats.get('fallback_generated', 0) + 1
                else:
                    # Skip meaningless images (QR codes, covers, etc.)
                    stats['skipped'] += 1
        else:
            processed_lines.append(line)

        i += 1

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

    processed, stats = describe_images_in_markdown(content, images_dir)

    print(f"Processed {stats['total_images']} images")
    print(f"  Described: {stats['described']}")
    print(f"  Skipped: {stats['skipped']}")
    print(f"  Failed: {stats['failed']}")

    # Output to file
    output_file = Path(md_file).parent / f"{Path(md_file).stem}_with_descriptions.md"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(processed)

    print(f"\nOutput saved to: {output_file}")


def _is_important_image(context: str, alt_text: str) -> bool:
    """
    判断图片是否为重要图片（需要占位描述）。

    重要图片：流程图、架构图、UML、数据表格、饼图、柱状图等包含上下文语义的图表
    无意义图片：二维码、封面、装饰图、人物肖像、图标等

    Args:
        context: 图片周围的文本上下文
        alt_text: 图片的alt文本

    Returns:
        True if image is important and should have placeholder description
    """
    text_to_check = f"{context} {alt_text}".lower()
    filename_to_check = alt_text.lower()

    # 首先检查是否是无意义图片（黑名单）
    meaningless_patterns = [
        r'二维码|qr\s*code|qr码',  # 二维码
        r'封面|cover|封面图',  # 封面
        r'肖像|portrait|头像|avatar|photo|照片',  # 人物肖像
        r'装饰|decoration|decorative',  # 装饰图
        r'图标|icon|logo|徽标',  # 图标/Logo
        r'background|bg|背景',  # 背景图
        r'banner|页头|header',  # 页头图
        r'separator|divider|分割线',  # 分隔线图
        r'placeholder|占位',  # 占位图
    ]

    # 如果匹配黑名单，直接返回False
    for pattern in meaningless_patterns:
        if re.search(pattern, text_to_check, re.IGNORECASE):
            return False

    # 重要图片关键词（白名单）- 使用更精确的匹配
    important_keywords = [
        r'架构图|架构|architecture.*图|system.*图|系统.*图',  # 架构图
        r'流程图|流程|flow.*图|workflow.*图|处理流程',  # 流程图
        r'uml|类图|时序图|sequence.*图|class.*图',  # UML图
        r'数据图|饼图|柱状图|折线图|bar.*图|pie.*图|line.*图',  # 数据图表
        r'表格|table|数据表',  # 表格
        r'对比图|对比|comparison.*图|compare.*图',  # 对比图
        r'截图|screenshot|界面|界面.*图',  # 界面截图
        r'拓扑图|topology|拓扑',  # 拓扑图
        r'关系图|relation.*图|relationship.*图',  # 关系图
        r'时序图|sequence.*图|timing.*图',  # 时序图
        r'状态图|state.*图|status.*图',  # 状态图
        r'部署图|deployment|部署',  # 部署图
        r'示例图|example.*图|demo.*图',  # 示例图
        r'模型图|model.*图',  # 模型图
        r'设计图|design.*图',  # 设计图
        r'结构图|structure.*图',  # 结构图
    ]

    # 检查是否包含重要关键词
    for pattern in important_keywords:
        if re.search(pattern, text_to_check, re.IGNORECASE):
            return True

    return False


def _generate_smart_placeholder(context: str, alt_text: str, filename: str) -> str:
    """
    为重要图片生成智能占位描述（强制使用引用块格式）。

    Args:
        context: 图片周围的文本上下文
        alt_text: 图片的alt文本
        filename: 图片文件名

    Returns:
        Blockquote-formatted placeholder description
    """
    text_to_check = f"{context} {alt_text} {filename}".lower()

    # 智能分类
    if any(word in text_to_check for word in ['架构', 'architecture', 'system', '结构', 'structure']):
        type_name = "架构图"
        content = "展示系统结构或组件关系"
    elif any(word in text_to_check for word in ['流程', 'flow', 'workflow', 'process']):
        type_name = "流程图"
        content = "展示处理流程或步骤"
    elif any(word in text_to_check for word in ['图', 'chart', 'graph', '曲线', '���状', '饼']):
        type_name = "数据图表"
        content = "展示数据趋势或对比"
    elif any(word in text_to_check for word in ['表', 'table', 'data']):
        type_name = "数据表格"
        content = "展示详细数据信息"
    elif any(word in text_to_check for word in ['对比', 'comparison', 'compare']):
        type_name = "对比图"
        content = "展示不同方案的对比"
    elif any(word in text_to_check for word in ['截图', 'screenshot', '界面', 'ui', 'interface']):
        type_name = "界面截图"
        content = "展示用户界面或操作步骤"
    elif any(word in text_to_check for word in ['示例', 'example', 'demo', '模型', 'model', '设计', 'design']):
        type_name = "示意图"
        content = "补充说明正文内容"
    else:
        type_name = "示意图"
        content = "补充说明文字内容"

    # 提取核心内容（使用alt文本或context的一部分）
    core_content = alt_text[:40] if alt_text else (context[:40] if len(context) > 40 else context)
    if core_content:
        content = f"{content}：{core_content}"

    # 生成引用块格式的占位描述
    description = f"""> **图片说明**：这是一张{type_name}。
> **核心内容**：{content}
> **关键元素**：请查看原图片获取详细信息
>
> **要点总结**：
> - 第一，该图片为重要示意图，建议查看原图。
> - 第二，图片包含关键信息，有助于理解正文内容。
> - 第三，AI图片描述功能暂未启用或分析失败。
> - 第四，如需详细说明，建议人工审核或查看原图。
"""

    return description
