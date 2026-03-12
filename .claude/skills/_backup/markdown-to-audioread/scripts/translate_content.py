#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Translation Module using SiliconFlow API

Translates text using external LLM API to avoid bloating the skill context.
"""

import re
import sys
from pathlib import Path
from typing import List, Dict, Tuple, Optional

from technical_term_detector import TechnicalTermDetector, analyze_paragraphs_for_translation


def is_chinese_char(c: str) -> bool:
    """Check if character is Chinese."""
    return '\u4e00' <= c <= '\u9fff'


def needs_translation(text: str) -> bool:
    """
    Check if text needs translation.

    A paragraph needs translation if:
    - It's not empty
    - It's not a header (#)
    - It's not a blockquote (>)
    - It's not a list item (- or number)
    - It's not already translated content (>30% Chinese characters)
    - It has minimum length (20 chars) to avoid false positives
    - It's not mostly code
    - It's not mostly symbols/punctuation
    """
    if not text:
        return False

    stripped = text.strip()

    # Skip markdown elements
    if stripped.startswith(('#', '>', '-', '*', '+')):
        # Check if numbered list
        if re.match(r'^\d+[.、)]\s', stripped):
            return False
        return False

    # Skip image markdown
    if stripped.startswith('!['):
        return False

    # Skip short text
    if len(stripped) < 20:
        return False

    # Skip if it's mostly code
    if '```' in stripped or stripped.count('`') > 2:
        return False

    # Check Chinese character ratio
    chinese_count = sum(1 for c in stripped if is_chinese_char(c))
    ratio = chinese_count / len(stripped)

    # If less than 30% Chinese, consider it needs translation
    # But also skip if it's mostly symbols/punctuation
    non_letter = sum(1 for c in stripped if not c.isalnum() and not is_chinese_char(c))
    if non_letter / len(stripped) > 0.3:
        return False

    return ratio < 0.3


def detect_translatable_paragraphs(lines: List[str]) -> List[Dict]:
    """
    Identify paragraphs that need translation with technical term awareness.

    Args:
        lines: List of markdown lines

    Returns:
        List of dictionaries with line_num and text for translatable paragraphs
    """
    # Use enhanced detector with technical term awareness
    paragraphs = analyze_paragraphs_for_translation(lines)

    # Filter only those needing translation
    return [p for p in paragraphs if p['needs_translation']]


def translate_with_api(
    paragraphs: List[Dict],
    batch_size: int = 5
) -> Tuple[List[str], bool]:
    """
    Translate paragraphs using SiliconFlow API.

    Args:
        paragraphs: List of paragraph dictionaries to translate
        batch_size: Number of paragraphs to translate in one API call

    Returns:
        Tuple of (translated_texts, success_flag)
    """
    try:
        from openai_client import get_openai_client
    except ImportError:
        print("Warning: openai_client not available. Using placeholder translations.")
        translations = [f"[API不可用] {p['text']}" for p in paragraphs]
        return translations, False

    # Extract technical terms from all paragraphs for preservation
    detector = TechnicalTermDetector()
    all_terms = set()

    for p in paragraphs:
        terms = detector.extract_terms(p['text'])
        all_terms.update(terms.keys())

    # Build term preservation list (top 20 most common)
    term_list = sorted(list(all_terms), key=len, reverse=True)[:20]

    try:
        client = get_openai_client()

        # Translate in batches
        texts = [p['text'] for p in paragraphs]
        translations = client.translate_batch(
            texts,
            source_lang="English",
            target_lang="Chinese",
            preserve_terms=term_list if term_list else None,
            batch_size=batch_size
        )

        return translations, True

    except Exception as e:
        print(f"Error during translation: {e}")
        print("Falling back to original text.")
        translations = [p['text'] for p in paragraphs]
        return translations, False


def translate_with_subagent(
    paragraphs: List[Dict]
) -> List[str]:
    """
    Translate paragraphs using SiliconFlow API (legacy interface).

    Args:
        paragraphs: List of paragraph dictionaries to translate

    Returns:
        List of translated texts (same order as input)
    """
    translations, _ = translate_with_api(paragraphs)
    return translations


def apply_translations_to_markdown(
    lines: List[str],
    translations: List[str],
    translated_indices: List[int]
) -> List[str]:
    """
    Replace original text with translations.

    Args:
        lines: Original markdown lines
        translations: List of translated texts
        translated_indices: Line indices that were translated

    Returns:
        New markdown lines with translations applied
    """
    output_lines = lines.copy()
    trans_index = 0

    for line_num in translated_indices:
        if trans_index < len(translations):
            output_lines[line_num - 1] = translations[trans_index] + '\n'
            trans_index += 1

    return output_lines


def translate_markdown_file(
    input_path: str,
    output_path: str,
    batch_size: int = 10
) -> Tuple[bool, str]:
    """
    Main translation function.

    This function is designed to be called from main.py where
    Claude's Task tool is available for subagent-based translation.

    Args:
        input_path: Path to input markdown
        output_path: Path for translated markdown
        batch_size: Paragraphs per subagent call (for efficiency)

    Returns:
        Tuple of (success, message)
    """
    md_file = Path(input_path)
    if not md_file.exists():
        return False, f"Markdown file not found: {input_path}"

    with open(md_file, 'r', encoding='utf-8') as f:
        content = f.read()

    lines = content.split('\n')

    # Detect paragraphs needing translation
    paragraphs = detect_translatable_paragraphs(lines)

    if not paragraphs:
        # No translation needed
        # Copy original to output
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(content)
        return True, "0 paragraphs (no translation needed)"

    print(f"  - Detected {len(paragraphs)} paragraphs needing translation")

    # Translate paragraphs
    # Note: In main.py, this will use Claude subagents
    # For standalone execution, we'll use a placeholder approach
    translated_texts = []
    for i in range(0, len(paragraphs), batch_size):
        batch = paragraphs[i:i + batch_size]
        print(f"  - Translating batch {i//batch_size + 1}/{(len(paragraphs)-1)//batch_size + 1}...")
        batch_translations = translate_with_subagent(batch)
        translated_texts.extend(batch_translations)

    # Apply translations
    translated_indices = [p['line_num'] for p in paragraphs]
    translated_lines = apply_translations_to_markdown(lines, translated_texts, translated_indices)

    # Write output
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(translated_lines))

    return True, f"{len(paragraphs)} paragraphs translated"


# This function is for use with Claude's Task tool
def translate_with_claude_subagent(paragraphs: List[str]) -> List[str]:
    """
    Translate paragraphs using Claude's built-in translation via Task tool.

    This function should be called from main.py using the Task tool.
    The prompt is built and sent to a subagent for actual translation.

    Args:
        paragraphs: List of paragraph texts to translate

    Returns:
        List of translated texts (same order as input)
    """
    # Build the paragraphs text for the prompt
    paragraphs_text = '\n\n'.join([
        f"{i+1}. {para}" for i, para in enumerate(paragraphs)
    ])

    prompt = f"""Translate the following English paragraph(s) to Simplified Chinese.

# Translation Rules
- Maintain academic/professional tone
- Preserve ALL technical terms, acronyms, and product names in English:
  - Model names: GPT, Claude, Llama, CodeAct, BERT, Mistral, etc.
  - Companies: Google, Microsoft, Anthropic, OpenAI, Meta, etc.
  - Technologies: API, GPU, LLM, JSON, Python, HTTP, TCP, IP, etc.
  - Frameworks: TensorFlow, PyTorch, React, Vue, Django, Flask, etc.
  - Protocols: HTTP, HTTPS, TCP, IP, DNS, SSL, TLS, etc.
  - Formats: JSON, XML, HTML, CSS, YAML, PDF, EPUB, etc.
  - Languages: Python, JavaScript, TypeScript, Java, C++, Go, Rust, etc.
  - Code, variable names, function names, class names
  - URLs, paths, file names, command lines
  - Citation markers: [1], [2,3], etc.
  - Mathematical notation: $...$, $$...$$
  - Any 2-6 letter acronyms
- Preserve mathematical notation, code blocks, tables
- Translate only the English prose content
- Do NOT add explanations, notes, or commentary
- Return ONLY the translated text, no original text
- Do NOT add any markdown formatting around the translations

# Paragraphs to Translate:
{paragraphs_text}

# Output Format
Return each translation as a separate line, matching the numbered input order. Use the format:
1. [first translation]
2. [second translation]
3. [third translation]
...

Do not include the original English text, only the translations."""

    # This function is called from main.py, which will handle
    # the actual Task tool invocation
    # The prompt is returned here for main.py to use
    return prompt, paragraphs


def main():
    """Main function for standalone testing."""
    if len(sys.argv) < 2:
        print("Usage: python translate_content.py <input_md> [output_md] [--batch-size N]")
        print("\nExamples:")
        print("  python translate_content.py document.md")
        print("  python translate_content.py document.md document_translated.md")
        print("  python translate_content.py document.md document_translated.md --batch-size 5")
        sys.exit(1)

    input_path = sys.argv[1]
    batch_size = 10

    # Parse optional arguments
    i = 2
    output_path = None
    while i < len(sys.argv):
        arg = sys.argv[i]
        if arg == '--batch-size' and i + 1 < len(sys.argv):
            batch_size = int(sys.argv[i + 1])
            i += 2
        elif not arg.startswith('--'):
            output_path = arg
            i += 1
        else:
            i += 1

    # Default output path
    if not output_path:
        md_file = Path(input_path)
        output_path = str(md_file.parent / f"{md_file.stem}_translated.md")

    # Perform translation
    print(f"Translating: {input_path}")
    success, message = translate_markdown_file(input_path, output_path, batch_size)

    if success:
        print(f"\n✓ Translation complete: {output_path}")
        print(f"  - {message}")
    else:
        print(f"\n✗ Translation failed: {message}")
        sys.exit(1)


if __name__ == "__main__":
    main()
