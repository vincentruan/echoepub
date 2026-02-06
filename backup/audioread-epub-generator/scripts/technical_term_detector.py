#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Technical Term Detector for Translation Preservation

Enhanced version of terminology_manager.py with improved detection
and integration into translation workflow.
"""

import re
from typing import Dict, List, Set, Tuple
from collections import Counter
from pathlib import Path


class TechnicalTermDetector:
    """Detect technical terms to preserve during translation."""

    # Term patterns from deprecated/terminology_manager.py
    TERM_PATTERNS = {
        'acronyms': r'\b[A-Z]{2,6}\b',
        'company_names': r'\b(Google|Microsoft|Apple|Meta|Amazon|OpenAI|Anthropic)\b',
        'framework_names': r'\b(CodeAct|TensorFlow|PyTorch|Keras|React|Vue|Django|Flask|FastAPI|Spring)\b',
        'model_names': r'\b(GPT-[34]|GPT-4|Claude|Llama|Gemini|BERT|RoBERTa|Mistral|Qwen)\b',
        'protocol_names': r'\b(HTTP|HTTPS|TCP|IP|DNS|SSL|TLS|FTP|SSH|SMTP|WebRTC)\b',
        'format_names': r'\b(JSON|XML|HTML|CSS|YAML|TOML|CSV|PDF|EPUB|Markdown)\b',
        'language_names': r'\b(Python|JavaScript|TypeScript|Java|C\+\+|C#|Go|Rust|Swift|Ruby|PHP|Scala|Kotlin|R|MATLAB)\b',
    }

    COMMON_TECH_TERMS = {
        'GPU', 'CPU', 'TPU', 'LLM', 'LLMs', 'API', 'APIs', 'SDK', 'UI', 'UX',
        'JSON', 'XML', 'HTML', 'CSS', 'HTTP', 'HTTPS', 'TCP', 'IP', 'DNS', 'SSL', 'TLS',
        'CodeAct', 'GPT', 'Claude', 'Llama', 'Gemini', 'BERT', 'Mistral',
        'Python', 'JavaScript', 'TypeScript', 'Java', 'C++', 'C#', 'Go', 'Rust',
        'TensorFlow', 'PyTorch', 'Keras', 'React', 'Vue', 'Angular',
        'Django', 'Flask', 'FastAPI', 'Spring', 'Docker', 'Kubernetes',
        'Git', 'GitHub', 'Linux', 'Unix', 'macOS', 'Windows',
        'REST', 'GraphQL', 'SQL', 'NoSQL', 'MongoDB', 'PostgreSQL', 'MySQL', 'Redis',
    }

    def __init__(self):
        self.detected_terms: Dict[str, int] = Counter()

    def extract_terms(self, text: str) -> Dict[str, int]:
        """
        Extract technical terms from text.

        Args:
            text: Text content to analyze

        Returns:
            Dictionary of {term: frequency}
        """
        all_terms = Counter()

        # Apply patterns
        for pattern_name, pattern in self.TERM_PATTERNS.items():
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple):
                    term = match[0] if match[0] else (match[1] if len(match) > 1 else '')
                else:
                    term = match

                if term and len(term) >= 2:
                    normalized = term.title() if term.isupper() or term.islower() else term
                    all_terms[normalized] += 1

        # Add common terms
        for common_term in self.COMMON_TECH_TERMS:
            pattern = r'\b' + re.escape(common_term) + r'\b'
            if re.search(pattern, text, re.IGNORECASE):
                all_terms[common_term] += text.lower().count(common_term.lower())

        self.detected_terms = dict(all_terms)
        return dict(all_terms)

    def has_technical_terms(self, text: str) -> bool:
        """
        Check if text contains technical terms.

        Args:
            text: Text to check

        Returns:
            True if technical terms found
        """
        terms = self.extract_terms(text)
        return len(terms) > 0

    def get_technical_term_ratio(self, text: str) -> float:
        """
        Calculate ratio of technical term content to total text.

        Args:
            text: Text to analyze

        Returns:
            Ratio (0.0 to 1.0)
        """
        terms = self.extract_terms(text)
        if not terms:
            return 0.0

        # Count characters in technical terms
        total_term_chars = sum(len(term) * count for term, count in terms.items())
        total_chars = len(text)

        return total_term_chars / total_chars if total_chars > 0 else 0.0

    def is_chinese_char(self, c: str) -> bool:
        """Check if character is Chinese."""
        return '\u4e00' <= c <= '\u9fff'

    def needs_translation_with_terms(
        self,
        text: str,
        chinese_threshold: float = 0.3
    ) -> Tuple[bool, str]:
        """
        Enhanced translation check considering technical terms.

        Args:
            text: Text to check
            chinese_threshold: Chinese character ratio threshold

        Returns:
            Tuple of (needs_translation: bool, reason: str)
        """
        # Check Chinese ratio
        chinese_count = sum(1 for c in text if self.is_chinese_char(c))
        chinese_ratio = chinese_count / len(text) if text else 0

        # High Chinese content - no translation needed
        if chinese_ratio >= chinese_threshold:
            return False, f"Already {chinese_ratio:.1%} Chinese"

        # Check for technical terms
        term_ratio = self.get_technical_term_ratio(text)

        # If high technical term density (>15%), preserve as-is
        if term_ratio > 0.15:
            return False, f"High technical term density ({term_ratio:.1%})"

        # If moderate technical terms (>5%) but low Chinese, translate with caution
        if term_ratio > 0.05 and chinese_ratio < 0.15:
            return True, "Translate with term preservation"

        # Standard case - translate if low Chinese
        return chinese_ratio < chinese_threshold, f"Chinese ratio {chinese_ratio:.1%}"


def analyze_paragraphs_for_translation(lines: List[str]) -> List[Dict]:
    """
    Analyze paragraphs and determine translation needs with technical term awareness.

    Args:
        lines: List of markdown lines

    Returns:
        List of paragraph analysis dictionaries
    """
    detector = TechnicalTermDetector()
    paragraphs = []

    current_para = []
    para_start = 0
    in_code_block = False

    for i, line in enumerate(lines, 1):
        stripped = line.strip()

        # Track code blocks
        if stripped.startswith('```'):
            if current_para:
                para_text = ' '.join(current_para)
                needs_tx, reason = detector.needs_translation_with_terms(para_text)
                paragraphs.append({
                    'line_num': para_start,
                    'text': para_text,
                    'lines': current_para,
                    'needs_translation': needs_tx,
                    'reason': reason,
                    'technical_terms': list(detector.extract_terms(para_text).keys())
                })
                current_para = []
            in_code_block = not in_code_block
            continue

        if in_code_block:
            continue

        # Skip structural elements
        if stripped.startswith(('#', '>', '!', '|', '-', '*')):
            if current_para:
                para_text = ' '.join(current_para)
                needs_tx, reason = detector.needs_translation_with_terms(para_text)
                paragraphs.append({
                    'line_num': para_start,
                    'text': para_text,
                    'lines': current_para,
                    'needs_translation': needs_tx,
                    'reason': reason,
                    'technical_terms': list(detector.extract_terms(para_text).keys())
                })
                current_para = []
            continue

        # Empty line ends paragraph
        if not stripped:
            if current_para:
                para_text = ' '.join(current_para)
                needs_tx, reason = detector.needs_translation_with_terms(para_text)
                paragraphs.append({
                    'line_num': para_start,
                    'text': para_text,
                    'lines': current_para,
                    'needs_translation': needs_tx,
                    'reason': reason,
                    'technical_terms': list(detector.extract_terms(para_text).keys())
                })
                current_para = []
            continue

        # Part of current paragraph
        if not current_para:
            para_start = i
        current_para.append(stripped)

    # Last paragraph
    if current_para:
        para_text = ' '.join(current_para)
        needs_tx, reason = detector.needs_translation_with_terms(para_text)
        paragraphs.append({
            'line_num': para_start,
            'text': para_text,
            'lines': current_para,
            'needs_translation': needs_tx,
            'reason': reason,
            'technical_terms': list(detector.extract_terms(para_text).keys())
        })

    return paragraphs


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python technical_term_detector.py <markdown_file>")
        sys.exit(1)

    md_file = sys.argv[1]

    with open(md_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    paragraphs = analyze_paragraphs_for_translation(lines)

    print(f"Analyzed {len(paragraphs)} paragraphs")

    needs_tx = [p for p in paragraphs if p['needs_translation']]
    skip_tx = [p for p in paragraphs if not p['needs_translation']]

    print(f"  Need translation: {len(needs_tx)}")
    print(f"  Skip (technical/Chinese): {len(skip_tx)}")

    print("\n=== Technical Term Paragraphs (Skipping Translation) ===")
    for p in skip_tx[:5]:
        print(f"\nLine {p['line_num']}: {p['reason']}")
        print(f"  Terms: {', '.join(p['technical_terms'][:5])}")
        print(f"  Text: {p['text'][:100]}...")
