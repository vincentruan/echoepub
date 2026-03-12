#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OpenAI-Compatible API Client for Vision Model (Image Analysis)

通过 OpenAI 兼容接口调用视觉模型生成图片描述。
支持 SiliconFlow、OpenAI、Azure OpenAI 等任何兼容接口。
"""

import os
import base64
from typing import Optional
from pathlib import Path


class OpenAIClient:
    """通用 OpenAI 兼容 API 客户端（仅图片分析）。"""

    DEFAULT_VLM_MODEL = "Pro/Qwen/Qwen2.5-VL-7B-Instruct"
    DEFAULT_API_BASE = "https://api.siliconflow.cn/v1"

    def __init__(
        self,
        api_key: Optional[str] = None,
        vlm_model: Optional[str] = None
    ):
        self.api_key = api_key or os.getenv("ECHO_EPUB_OPEN_API_KEY")
        if not self.api_key:
            raise ValueError(
                "API key not found. Please set ECHO_EPUB_OPEN_API_KEY environment variable "
                "or pass api_key parameter."
            )

        self.vlm_model = vlm_model or os.getenv(
            "ECHO_EPUB_VLM_MODEL", self.DEFAULT_VLM_MODEL
        )
        self.api_base = (
            os.getenv("ECHO_EPUB_OPEN_AI_BASE_URL")
            or os.getenv("ECHO_EPUB_API_BASE", self.DEFAULT_API_BASE)
        )

    def analyze_image(
        self,
        image_path: str,
        context: str = "",
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
