#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SiliconFlow API Client for Translation and VLM

Provides integration with SiliconFlow's chat completion and vision APIs.
"""

import os
import base64
from typing import List, Dict, Optional, Union
from pathlib import Path


class SiliconFlowClient:
    """Client for SiliconFlow API."""

    # Default models
    DEFAULT_TRANSLATE_MODEL = "MiniMaxAI/MiniMax-M2"
    DEFAULT_VLM_MODEL = "Qwen/Qwen2-VL-7B-Instruct"  # 更换为支持视觉理解的模型
    DEFAULT_API_BASE = "https://api.siliconflow.cn/v1"

    def __init__(
        self,
        api_key: Optional[str] = None,
        translate_model: Optional[str] = None,
        vlm_model: Optional[str] = None
    ):
        """
        Initialize SiliconFlow client.

        Args:
            api_key: API key (defaults to ECHO_EPUB_OPEN_API_KEY env var)
            translate_model: Translation model (defaults to ECHO_EPUB_TRANSLATE_MODEL or MiniMax-M2)
            vlm_model: VLM model for image analysis (defaults to ECHO_EPUB_VLM_MODEL or PaddleOCR-VL-1.5)
        """
        self.api_key = api_key or os.getenv("ECHO_EPUB_OPEN_API_KEY")
        if not self.api_key:
            raise ValueError(
                "API key not found. Please set ECHO_EPUB_OPEN_API_KEY environment variable "
                "or pass api_key parameter."
            )

        self.translate_model = translate_model or os.getenv(
            "ECHO_EPUB_TRANSLATE_MODEL",
            self.DEFAULT_TRANSLATE_MODEL
        )
        self.vlm_model = vlm_model or os.getenv(
            "ECHO_EPUB_VLM_MODEL",
            self.DEFAULT_VLM_MODEL
        )
        # Use ECHO_EPUB_OPEN_AI_BASE_URL, fall back to ECHO_EPUB_API_BASE for backward compatibility
        self.api_base = os.getenv("ECHO_EPUB_OPEN_AI_BASE_URL") or os.getenv("ECHO_EPUB_API_BASE", self.DEFAULT_API_BASE)

    def translate_text(
        self,
        text: str,
        source_lang: str = "English",
        target_lang: str = "Chinese",
        preserve_terms: Optional[List[str]] = None
    ) -> str:
        """
        Translate text using SiliconFlow chat completion API.

        Args:
            text: Text to translate
            source_lang: Source language (for prompt)
            target_lang: Target language
            preserve_terms: List of technical terms to preserve in original form

        Returns:
            Translated text
        """
        try:
            import requests
        except ImportError:
            raise ImportError("requests library not installed. Install with: pip install requests")

        # Build preservation section
        term_section = ""
        if preserve_terms:
            term_list = preserve_terms[:20]  # Limit to 20 terms
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
                    "messages": [
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    "temperature": 0.3,
                    "max_tokens": 4096
                },
                timeout=60
            )

            response.raise_for_status()
            result = response.json()

            # Extract translated text
            if "choices" in result and len(result["choices"]) > 0:
                translated = result["choices"][0]["message"]["content"].strip()
                return translated
            else:
                raise ValueError(f"Unexpected API response format: {result}")

        except requests.exceptions.RequestException as e:
            print(f"Error calling translation API: {e}")
            # Return original text on error
            return text

    def translate_batch(
        self,
        texts: List[str],
        source_lang: str = "English",
        target_lang: str = "Chinese",
        preserve_terms: Optional[List[str]] = None,
        batch_size: int = 5
    ) -> List[str]:
        """
        Translate multiple texts in batches.

        Args:
            texts: List of texts to translate
            source_lang: Source language
            target_lang: Target language
            preserve_terms: Technical terms to preserve
            batch_size: Number of texts to translate in one API call

        Returns:
            List of translated texts
        """
        translations = []

        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            combined_text = "\n\n---SEPARATOR---\n\n".join(batch)

            translated = self.translate_text(
                combined_text,
                source_lang,
                target_lang,
                preserve_terms
            )

            # Split by separator
            batch_translations = translated.split("---SEPARATOR---")
            translations.extend([t.strip() for t in batch_translations])

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
        Analyze image using SiliconFlow VLM API with retry mechanism.

        Args:
            image_path: Path to image file
            context: Surrounding text context for better understanding
            image_type: Type of image (chart, flowchart, architecture, etc.)
            max_retries: Maximum number of retry attempts (default: 2)
            retry_delay: Delay between retries in seconds (default: 1)

        Returns:
            Structured image description or None if failed after all retries
        """
        try:
            import requests
            import time
        except ImportError:
            raise ImportError("requests library not installed. Install with: pip install requests")

        if not Path(image_path).exists():
            print(f"Image not found: {image_path}")
            return None

        # Validate image format
        valid_formats = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'}
        img_ext = Path(image_path).suffix.lower()
        if img_ext not in valid_formats:
            print(f"Unsupported image format: {img_ext}")
            return None

        # Read and encode image
        try:
            with open(image_path, 'rb') as f:
                image_data = f.read()
            image_base64 = base64.b64encode(image_data).decode('utf-8')
        except Exception as e:
            print(f"Error reading image: {e}")
            return None

        # Build prompt based on image type
        type_prompts = {
            'chart': """Analyze this data chart and provide a structured description for audio narration.

Follow this EXACT format in Chinese:
> **图表说明**：这是一张[chart type]。
> 核心结论是：[main conclusion in 1-2 sentences]
> 关键元素包括：[axes labels, data series, trends]
> 要点总结：
> - 第一，[key insight 1]
> - 第二，[key insight 2]
> - 第三，[key insight 3]
> - 第四，[key insight 4]
> - 第五，[key insight 5]""",

            'flowchart': """Analyze this flowchart and provide a structured description for audio narration.

Follow this EXACT format in Chinese:
> **流程图说明**：这是一张流程图。
> 核心流程是：[overall flow in 1-2 sentences]
> 关键元素包括：[steps, decisions, branches]
> 要点总结：
> - 第一，[starting point]
> - 第二，[each major step]
> - 第三，[decision points]
> - 第四，[branches]
> - 第五，[end point or outcome]""",

            'architecture': """Analyze this system architecture diagram and provide a structured description for audio narration.

Follow this EXACT format in Chinese:
> **架构图说明**：这是一张系统架构图。
> 核心结构是：[overall architecture in 1-2 sentences]
> 关键元素包括：[components, layers, connections]
> 要点总结：
> - 第一，[major component 1]
> - 第二，[major component 2]
> - 第三，[data flow]
> - 第四，[relationships]
> - 第五，[key patterns]""",

            'general': """Analyze this image and provide a structured description for audio narration.

Follow this EXACT format in Chinese:
> **图片说明**：这是一张[image type]。
> 核心内容是：[main content in 1-2 sentences]
> 关键元素包括：[key visual elements]
> 要点总结：
> - 第一，[element 1]
> - 第二，[element 2]
> - 第三，[element 3]
> - 第四，[element 4]
> - 第五，[element 5]"""
        }

        base_prompt = type_prompts.get(image_type, type_prompts['general'])

        # Add context if provided
        if context:
            full_prompt = f"""{base_prompt}

Additional context from the document:
{context}

Remember to follow the EXACT format specified above."""
        else:
            full_prompt = base_prompt

        # Retry mechanism for API calls
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
                        "messages": [
                            {
                                "role": "user",
                                "content": [
                                    {
                                        "type": "text",
                                        "text": full_prompt
                                    },
                                    {
                                        "type": "image_url",
                                        "image_url": {
                                            "url": f"data:image/jpeg;base64,{image_base64}"
                                        }
                                    }
                                ]
                            }
                        ],
                        "temperature": 0.3,
                        "max_tokens": 2048
                    },
                    timeout=90  # 增加到90秒以支持更复杂的VLM模型
                )

                response.raise_for_status()
                result = response.json()

                # Extract description
                if "choices" in result and len(result["choices"]) > 0:
                    description = result["choices"][0]["message"]["content"].strip()
                    return description
                else:
                    print(f"Unexpected API response format: {result}")
                    last_error = f"Unexpected response format: {result}"
                    if attempt < max_retries:
                        time.sleep(retry_delay)
                    continue

            except requests.exceptions.Timeout:
                last_error = f"Timeout after 30 seconds"
                if attempt < max_retries:
                    print(f"  ⏱ Request timeout, retrying ({attempt + 1}/{max_retries})...")
                    time.sleep(retry_delay)
                else:
                    print(f"  ✗ Timeout after {max_retries} retries")

            except requests.exceptions.RequestException as e:
                last_error = str(e)
                if attempt < max_retries:
                    print(f"  ⚠ API error: {e}, retrying ({attempt + 1}/{max_retries})...")
                    time.sleep(retry_delay)
                else:
                    print(f"  ✗ Failed after {max_retries} retries: {e}")

        # All retries failed
        print(f"  ⚠ Image analysis failed: {last_error}")
        return None


# Singleton instance for reuse
_client_instance = None


def get_siliconflow_client() -> SiliconFlowClient:
    """Get or create singleton SiliconFlow client instance."""
    global _client_instance
    if _client_instance is None:
        _client_instance = SiliconFlowClient()
    return _client_instance


if __name__ == "__main__":
    import sys

    # Test translation
    if len(sys.argv) > 1 and sys.argv[1] == "test-translate":
        client = get_siliconflow_client()
        result = client.translate_text(
            "This is a test of the translation API with technical terms like GPU, API, and LLM.",
            preserve_terms=["GPU", "API", "LLM"]
        )
        print(f"Translation result: {result}")

    # Test image analysis
    elif len(sys.argv) > 1 and sys.argv[1] == "test-image":
        if len(sys.argv) < 3:
            print("Usage: python siliconflow_client.py test-image <image_path>")
            sys.exit(1)

        client = get_siliconflow_client()
        result = client.analyze_image(sys.argv[2], image_type="general")
        print(f"Image analysis result:\n{result}")

    else:
        print("Usage:")
        print("  python siliconflow_client.py test-translate")
        print("  python siliconflow_client.py test-image <image_path>")
