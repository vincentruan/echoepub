#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EPUB Quality Comparison Tool

Compares the final Chinese EPUB with the original English markdown
to verify translation quality, technical term preservation, and content integrity.
"""

import re
import json
import sys
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional
from collections import defaultdict

# Technical terms that should be preserved in English
# These are Java-specific terms that should NOT be flagged when they appear in normal text
JAVA_KEYWORDS_IN_CODE_ONLY = {
    # These are common English words that happen to be Java keywords
    # Only flag if they appear in code context
    'try', 'do', 'return', 'for', 'if', 'else', 'while', 'break', 'continue',
    'case', 'default', 'new', 'this', 'super', 'void', 'throw', 'catch',
    'finally', 'import', 'package', 'extends', 'implements', 'instanceof',
}

JAVA_TECHNICAL_TERMS = {
    # Java keywords that are uniquely Java and should be preserved
    'public', 'private', 'protected', 'static', 'final', 'abstract', 'interface',
    'class', 'enum', 'native', 'synchronized', 'volatile', 'transient', 'assert',

    # Common Java classes/interfaces
    'String', 'Integer', 'Long', 'Double', 'Float', 'Boolean', 'Character',
    'Object', 'Class', 'System', 'Math', 'Runtime', 'Thread', 'Runnable',
    'List', 'Set', 'Map', 'Collection', 'Collections', 'Arrays',
    'ArrayList', 'LinkedList', 'HashMap', 'HashSet', 'TreeMap', 'TreeSet',
    'Iterator', 'Iterable', 'Comparator', 'Comparable',
    'Optional', 'Stream', 'Lambda', 'FunctionalInterface',
    'Exception', 'RuntimeException', 'Throwable', 'Error',
    'InputStream', 'OutputStream', 'Reader', 'Writer', 'File',
    'Connection', 'Statement', 'ResultSet', 'DriverManager',
    'EnumSet', 'EnumMap', 'RegularEnumSet', 'JumboEnumSet',
    'BigInteger', 'BigDecimal', 'Date', 'LocalDate', 'LocalDateTime',
    'StackWalker', 'ServiceLoader', 'FileStore', 'BufferedReader',

    # Java APIs
    'valueOf', 'toString', 'equals', 'hashCode', 'compareTo', 'clone',
    'getClass', 'notify', 'notifyAll', 'wait',
    'getInstance', 'newInstance',

    # Patterns and concepts (technical terms)
    'singleton', 'immutable', 'flyweight', 'decorator', 'observer',
    'DependencyInjection',

    # Technical acronyms
    'API', 'JDBC', 'JVM', 'JDK', 'JAR', 'WAR', 'URL', 'URI', 'JSON', 'XML',
    'HTTP', 'HTTPS', 'TCP', 'UDP', 'IP', 'DNS', 'SSL', 'TLS',
    'LIFO', 'FIFO', 'CRUD', 'ACID', 'ORM', 'SQL',
}

# Terms that are commonly used in prose and should NOT be flagged
COMMON_PROSE_WORDS = {
    'of', 'from', 'to', 'type', 'builder', 'factory', 'adapter', 'strategy',
    'interface', 'abstract', 'native', 'synchronized', 'volatile', 'transient'
}

@dataclass
class Issue:
    """Represents a detected issue."""
    type: str  # 'translation', 'technical_term', 'formatting', 'missing_content'
    severity: str  # 'high', 'medium', 'low'
    location: str
    description: str
    original: str
    translated: str
    suggestion: Optional[str] = None

@dataclass
class ChapterComparison:
    """Comparison results for a chapter."""
    chapter_num: int
    chapter_title: str
    original_file: str
    translated_file: str
    issues: List[Issue] = field(default_factory=list)
    stats: Dict = field(default_factory=dict)

def extract_text_for_comparison(content: str) -> str:
    """Extract text content for comparison, removing code blocks and images."""
    # Remove code blocks
    text = re.sub(r'```[\s\S]*?```', '', content)
    # Remove inline code
    text = re.sub(r'`[^`]+`', '', text)
    # Remove images
    text = re.sub(r'!\[.*?\]\(.*?\)', '', text)
    # Remove links but keep text
    text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)
    # Remove markdown headings
    text = re.sub(r'^#+\s+', '', text, flags=re.MULTILINE)
    # Remove blockquotes
    text = re.sub(r'^>\s+', '', text, flags=re.MULTILINE)
    # Remove horizontal rules
    text = re.sub(r'^---+$', '', text, flags=re.MULTILINE)
    return text.strip()

def extract_code_blocks(content: str) -> List[str]:
    """Extract all code blocks from content."""
    # Standard code blocks
    code_blocks = re.findall(r'```[\s\S]*?```', content)
    # Blockquote code (common in this book)
    bq_code = re.findall(r'^>[\s\S]*?(?=^>|\n\n|\Z)', content, re.MULTILINE)
    return code_blocks + bq_code

def extract_technical_terms(text: str) -> set:
    """Extract potential technical terms from text."""
    # CamelCase words
    camel_case = set(re.findall(r'\b[A-Z][a-z]+(?:[A-Z][a-z]+)+\b', text))
    # ALL_CAPS
    all_caps = set(re.findall(r'\b[A-Z]{2,}\b', text))
    # method names (lowerCamelCase followed by parens)
    method_names = set(re.findall(r'\b[a-z][a-zA-Z0-9]*(?=\()', text))
    # Known technical terms
    known_terms = set()
    for term in JAVA_TECHNICAL_TERMS:
        if term in text:
            known_terms.add(term)

    return camel_case | all_caps | method_names | known_terms

def check_technical_term_preservation(original: str, translated: str) -> List[Issue]:
    """Check if technical terms are preserved in translation."""
    issues = []

    original_terms = extract_technical_terms(original)

    for term in original_terms:
        if term in JAVA_TECHNICAL_TERMS:
            # Check if term appears in translation
            if term not in translated:
                issues.append(Issue(
                    type='technical_term',
                    severity='high',
                    location='content',
                    description=f'Technical term "{term}" not preserved in translation',
                    original=term,
                    translated='[MISSING]',
                    suggestion=f'Keep "{term}" in English'
                ))

    return issues

def check_code_block_integrity(original: str, translated: str) -> List[Issue]:
    """Check if code blocks are preserved correctly."""
    issues = []

    original_codes = extract_code_blocks(original)
    translated_codes = extract_code_blocks(translated)

    if len(original_codes) != len(translated_codes):
        issues.append(Issue(
            type='formatting',
            severity='high',
            location='code blocks',
            description=f'Code block count mismatch: {len(original_codes)} original vs {len(translated_codes)} translated',
            original=f'{len(original_codes)} code blocks',
            translated=f'{len(translated_codes)} code blocks',
            suggestion='Ensure all code blocks are preserved'
        ))

    return issues

def check_image_references(original: str, translated: str) -> List[Issue]:
    """Check if image references are correct."""
    issues = []

    original_images = re.findall(r'!\[(.*?)\]\((.*?)\)', original)
    translated_images = re.findall(r'!\[(.*?)\]\((.*?)\)', translated)

    # Check count
    if len(original_images) != len(translated_images):
        issues.append(Issue(
            type='formatting',
            severity='medium',
            location='images',
            description=f'Image count mismatch: {len(original_images)} original vs {len(translated_images)} translated',
            original=f'{len(original_images)} images',
            translated=f'{len(translated_images)} images',
            suggestion='Ensure all images are preserved'
        ))

    return issues

def check_chapter_structure(original_dir: Path, translated_dir: Path) -> List[Issue]:
    """Check if chapter structure is preserved."""
    issues = []

    original_files = sorted(original_dir.glob('*.md'))
    translated_files = sorted(translated_dir.glob('*.md'))

    original_names = [f.name for f in original_files if not f.name.startswith('00_') and '_report' not in f.name]
    translated_names = [f.name for f in translated_files if not f.name.startswith('00_') and '_report' not in f.name]

    if len(original_names) != len(translated_names):
        issues.append(Issue(
            type='formatting',
            severity='high',
            location='chapter structure',
            description=f'Chapter count mismatch: {len(original_names)} original vs {len(translated_names)} translated',
            original=f'{len(original_names)} chapters',
            translated=f'{len(translated_names)} chapters',
            suggestion='Ensure all chapters are translated'
        ))

    return issues

def compare_chapters(original_dir: Path, translated_dir: Path) -> List[ChapterComparison]:
    """Compare all chapters between original and translated versions."""
    comparisons = []

    original_files = sorted(original_dir.glob('*.md'))

    for orig_file in original_files:
        if orig_file.name.startswith('00_') or '_report' in orig_file.name:
            continue

        # Find corresponding translated file
        chapter_num = re.match(r'^(\d+)_', orig_file.name)
        if not chapter_num:
            continue

        trans_files = list(translated_dir.glob(f'{chapter_num.group(1)}_*.md'))
        if not trans_files:
            continue

        trans_file = trans_files[0]

        original_content = orig_file.read_text(encoding='utf-8')
        translated_content = trans_file.read_text(encoding='utf-8')

        comparison = ChapterComparison(
            chapter_num=int(chapter_num.group(1)),
            chapter_title=orig_file.stem,
            original_file=str(orig_file),
            translated_file=str(trans_file),
            stats={
                'original_chars': len(original_content),
                'translated_chars': len(translated_content),
                'original_words': len(original_content.split()),
                'translated_words': len(translated_content.split()),
            }
        )

        # Run all checks
        comparison.issues.extend(check_technical_term_preservation(original_content, translated_content))
        comparison.issues.extend(check_code_block_integrity(original_content, translated_content))
        comparison.issues.extend(check_image_references(original_content, translated_content))

        comparisons.append(comparison)

    return comparisons

def generate_report(comparisons: List[ChapterComparison], output_path: Path):
    """Generate a detailed comparison report."""
    import datetime
    report = ['# EPUB Quality Comparison Report\n']
    report.append(f'Generated: {datetime.datetime.now().isoformat()}\n')

    # Summary statistics
    total_issues = sum(len(c.issues) for c in comparisons)
    high_severity = sum(1 for c in comparisons for i in c.issues if i.severity == 'high')
    medium_severity = sum(1 for c in comparisons for i in c.issues if i.severity == 'medium')
    low_severity = sum(1 for c in comparisons for i in c.issues if i.severity == 'low')

    report.append('## Summary\n')
    report.append(f'- Chapters compared: {len(comparisons)}\n')
    report.append(f'- Total issues found: {total_issues}\n')
    report.append(f'  - High severity: {high_severity}\n')
    report.append(f'  - Medium severity: {medium_severity}\n')
    report.append(f'  - Low severity: {low_severity}\n')

    # Issues by type
    issues_by_type = defaultdict(list)
    for c in comparisons:
        for i in c.issues:
            issues_by_type[i.type].append(i)

    report.append('\n## Issues by Type\n')
    for issue_type, issues in issues_by_type.items():
        report.append(f'\n### {issue_type.title()} Issues ({len(issues)})\n')
        for i in issues[:10]:  # Limit to first 10 per type
            report.append(f'- **[{i.severity.upper()}]** {i.description}\n')
            if i.suggestion:
                report.append(f'  - Suggestion: {i.suggestion}\n')

    # Detailed chapter reports
    report.append('\n## Chapter Details\n')
    for c in comparisons:
        if c.issues:
            report.append(f'\n### Chapter {c.chapter_num}: {c.chapter_title}\n')
            report.append(f'- Original: {c.stats["original_chars"]} chars, {c.stats["original_words"]} words\n')
            report.append(f'- Translated: {c.stats["translated_chars"]} chars, {c.stats["translated_words"]} words\n')
            if c.issues:
                report.append(f'- Issues: {len(c.issues)}\n')
                for i in c.issues[:5]:
                    report.append(f'  - [{i.severity}] {i.description}\n')

    output_path.write_text('\n'.join(report), encoding='utf-8')
    print(f'Report generated: {output_path}')

def main():
    if len(sys.argv) < 3:
        print("Usage: python epub_quality_checker.py <original_dir> <translated_dir> [output_report]")
        return 1

    original_dir = Path(sys.argv[1])
    translated_dir = Path(sys.argv[2])
    output_path = Path(sys.argv[3]) if len(sys.argv) > 3 else Path('quality_report.md')

    if not original_dir.exists():
        print(f"Error: Original directory not found: {original_dir}")
        return 1

    if not translated_dir.exists():
        print(f"Error: Translated directory not found: {translated_dir}")
        return 1

    # Run comparison
    comparisons = compare_chapters(original_dir, translated_dir)

    # Check overall structure
    structure_issues = check_chapter_structure(original_dir, translated_dir)

    # Generate report
    generate_report(comparisons, output_path)

    # Print summary
    total_issues = sum(len(c.issues) for c in comparisons)
    print(f"\nComparison complete: {len(comparisons)} chapters, {total_issues} issues found")

    return 0

if __name__ == "__main__":
    exit(main())