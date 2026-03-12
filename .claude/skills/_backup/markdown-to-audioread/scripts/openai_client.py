#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OpenAI-Compatible API Client for Translation and VLM

通过 OpenAI 兼容接口调用 LLM 进行翻译和图片描述生成。
支持 SiliconFlow、OpenAI、Azure OpenAI 等任何兼容接口。
"""

import os
import base64
from typing import List, Dict, Optional, Union
from pathlib import Path


class OpenAIClient:
    """通用 OpenAI 兼容 API 客户端。"""

    DEFAULT_TRANSLATE_MODEL = "MiniMaxAI/MiniMax-M2"
    DEFAULT_VLM_MODEL = "Qwen/Qwen2-VL-7B-Instruct"
    DEFAULT_API_BASE = "https://api.siliconflow.cn/v1"

    def __init__(
        self,
        api_key: Optional[str] = None,
        translate_model: Optional[str] = None,
        vlm_model: Optional[str] = None
    ):
        """
        初始化客户端。

        Args:
            api_key: API Key（默认读取 ECHO_EPUB_OPEN_API_KEY 环境变量）
            translate_model: 翻译模型（默认读取 ECHO_EPUB_TRANSLATE_MODEL）
            vlm_model: 视觉模型（默认读取 ECHO_EPUB_VLM_MODEL）
        """
        self.api_key = api_key or os.getenv("ECHO_EPUB_OPEN_API_KEY")
        if not self.api_key:
            raise ValueError(
                "API key not found. Please set ECHO_EPUB_OPEN_API_KEY environment variable "
                "or pass api_key parameter."
            )

        self.translate_model = translate_model or os.getenv(
            "ECHO_EPUB_TRANSLATE_MODEL", self.DEFAULT_TRANSLATE_MODEL
        )
        self.vlm_model = vlm_model or os.getenv(
            "ECHO_EPUB_VLM_MODEL", self.DEFAULT_VLM_MODEL
        )
        self.api_base = (
            os.getenv("ECHO_EPUB_OPEN_AI_BASE_URL")
            or os.getenv("ECHO_EPUB_API_BASE", self.DEFAULT_API_BASE)
        )

    def translate_text(
        self,
        text: str,
        source_lang: str = "English",
        target_lang: str = "Chinese",
        preserve_terms: Optional[List[str]] = None
    ) -> str:
        """翻译文本。"""
        try:
            import requests
        except ImportError:
            raise ImportError("requests library not installed. Install with: pip install requests")

        term_section = ""
        if preserve_terms:
            term_list = preserve_terms[:20]
            term_section = "\n# Technical Terms to Preserve (MUST keep in English):\n"
            term_section += "\n".join([f"  - {term}" for term in term_list])

        prompt = f"""Translate the following {source_lang} text to {target_lang} (Simplified Chinese).

# Translation Rules:
- Maintain academic/professional tone
- Translate only the prose content
- Do NOT add explanations, notes, or commentary
- Return ONLY the translated text
{term_section}

# Text to Translate:
{text}

# Output:
Return only the translated text without any additional formatting or explanation."""

        try:
            response = requests.post(
                f"{self.api_base}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": self.translate_model,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.3,
                    "max_tokens": 4096
                },
                timeout=60
            )
            response.raise_for_status()
            result = response.json()

            if "choices" in result and len(result["choices"]) > 0:
                return result["choices"][0]["message"]["content"].strip()
            else:
                raise ValueError(f"Unexpected API response: {result}")

        except requests.exceptions.RequestException as e:
            print(f"翻译 API 调用失败: {e}")
            return text

    def translate_batch(
        self,
        texts: List[str],
        source_lang: str = "English",
        target_lang: str = "Chinese",
        preserve_terms: Optional[List[str]] = None,
        batch_size: int = 5
    ) -> List[str]:
        """批量翻译。"""
        translations = []
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            combined = "\n\n---SEPARATOR---\n\n".join(batch)
            translated = self.translate_text(combined, source_lang, target_lang, preserve_terms)
            parts = translated.split("---SEPARATOR---")
            translations.extend([t.strip() for t in parts])
        return translations

    def analyze_image(
        self,
        image_path: str,
        context: str = "",
        image_type: str = "general",
        max_retries: int = 2,
        retry_delay: int = 1
    ) -> Optional[str]:
        """
        调用视觉模型分析图片，生成连贯的中文描述。

        Args:
            image_path: 图片文件路径
            context: 章节上下文
            max_retries: 最大重试次数
            retry_delay: 重试间隔（秒）

        Returns:
            图片描述文本，失败返回 None
        """
        try:
            import requests
            import time
        except ImportError:
            raise ImportError("requests library not installed. Install with: pip install requests")

        if not Path(image_path).exists():
            print(f"图片不存在: {image_path}")
            return None

        valid_formats = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'}
        img_ext = Path(image_path).suffix.lower()
        if img_ext not in valid_formats:
            print(f"不支持的图片格式: {img_ext}")
            return None

        try:
            with open(image_path, 'rb') as f:
                image_data = f.read()
            image_base64 = base64.b64encode(image_data).decode('utf-8')
        except Exception as e:
            print(f"读取图片失败: {e}")
            return None

        # 构建提示词
        prompt = "请结合以下章节上下文，为这张图片生成一段连贯的中文描述。\n\n"
        prompt += "要求：\n"
        prompt += "1. 描述应让读者不看图片也能理解图片传达的信息\n"
        prompt += "2. 结合上下文语境，使描述与前后文自然衔接\n"
        prompt += "3. 用一段连贯的文字表达，不要分点列举\n"
        prompt += "4. 语言干练、专业\n"
        prompt += "5. 忠实于图片内容，不要编造信息\n\n"
        prompt += "请直接输出描述文字，不要添加任何前缀或标记。"

        if context:
            prompt += f"\n\n章节上下文：\n{context[:500]}"

        # 带重试的 API 调用
        last_error = None
        for attempt in range(max_retries + 1):
            try:
                response = requests.post(
                    f"{self.api_base}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": self.vlm_model,
                        "messages": [{
                            "role": "user",
                            "content": [
                                {"type": "text", "text": prompt},
                                {
                                    "type": "image_url",
                                    "image_url": {"url": f"data:image/{img_ext.lstrip('.')};base64,{image_base64}"}
                                }
                            ]
                        }],
                        "temperature": 0.3,
                        "max_tokens": 2048
                    },
                    timeout=90
                )
                response.raise_for_status()
                result = response.json()

                if "choices" in result and len(result["choices"]) > 0:
                    description = result["choices"][0]["message"]["content"].strip()
                    # 校验：确保返回的不是 prompt 本身或错误信息
                    if description and len(description) > 10 and "要求" not in description[:20]:
                        return description
                    else:
                        last_error = "模型返回内容异常"
                        if attempt < max_retries:
                            time.sleep(retry_delay)
                        continue
                else:
                    last_error = f"响应格式异常: {result}"
                    if attempt < max_retries:
                        time.sleep(retry_delay)
                    continue

            except requests.exceptions.Timeout:
                last_error = "请求超时"
                if attempt < max_retries:
                    print(f"  ⏱ 超时，重试 ({attempt + 1}/{max_retries})...")
                    time.sleep(retry_delay)

            except requests.exceptions.RequestException as e:
                last_error = str(e)
                if attempt < max_retries:
                    print(f"  ⚠ API 错误: {e}，重试 ({attempt + 1}/{max_retries})...")
                    time.sleep(retry_delay)

        print(f"  ✗ 图片分析失败: {last_error}")
        return None


# 单例
_client_instance = None


def get_openai_client() -> OpenAIClient:
    """获取或创建单例客户端。"""
    global _client_instance
    if _client_instance is None:
        _client_instance = OpenAIClient()
    return _client_instance


# 向后兼容别名
get_siliconflow_client = get_openai_client
SiliconFlowClient = OpenAIClient


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "test-translate":
        client = get_openai_client()
        result = client.translate_text(
            "This is a test of the translation API with technical terms like GPU, API, and LLM.",
            preserve_terms=["GPU", "API", "LLM"]
        )
        print(f"翻译结果: {result}")

    elif len(sys.argv) > 1 and sys.argv[1] == "test-image":
        if len(sys.argv) < 3:
            print("Usage: python openai_client.py test-image <image_path>")
            sys.exit(1)
        client = get_openai_client()
        result = client.analyze_image(sys.argv[2])
        print(f"图片分析结果:\n{result}")

    else:
        print("Usage:")
        print("  python openai_client.py test-translate")
        print("  python openai_client.py test-image <image_path>")
