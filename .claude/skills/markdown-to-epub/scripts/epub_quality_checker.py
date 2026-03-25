#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EPUB Quality Checker

Validates EPUB quality for audiobook optimization:
- Structure integrity (chapters, images)
- TOC hierarchy
- Chinese content coverage (descriptions, translations)
- Image handling
"""

import argparse
import subprocess
import zipfile
from pathlib import Path
from typing import Dict, List, Tuple
import re


class EPUBQualityChecker:
    """Check EPUB quality metrics."""

    def __init__(self, epub_path: str):
        self.epub_path = Path(epub_path)
        self.results = {
            'structure': {},
            'content': {},
            'issues': [],
            'recommendations': []
        }

    def check_all(self) -> Dict:
        """Run all quality checks."""
        self.check_structure()
        self.check_content()
        self.generate_recommendations()
        return self.results

    def check_structure(self) -> None:
        """Check EPUB structure integrity."""
        if not self.epub_path.exists():
            self.results['issues'].append(f"EPUB file not found: {self.epub_path}")
            return

        # Basic file info
        self.results['structure']['file_size_mb'] = round(
            self.epub_path.stat().st_size / 1024 / 1024, 2
        )

        # Count images
        with zipfile.ZipFile(self.epub_path, 'r') as z:
            files = z.namelist()
            images = [f for f in files if any(f.lower().endswith(ext)
                     for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp'])]
            self.results['structure']['image_count'] = len(images)

            # Check for cover
            cover_found = any('cover' in f.lower() for f in images)
            self.results['structure']['has_cover'] = cover_found

        # Get chapter count via epub-reader
        try:
            result = subprocess.run(
                ['node', '.claude/skills/epub-to-markdown-converter/scripts/epub-reader/dist/index.js',
                 'metadata', str(self.epub_path)],
                capture_output=True, text=True, cwd=Path.cwd()
            )
            chapter_match = re.search(r'Total Chapters:\s*(\d+)', result.stdout)
            if chapter_match:
                self.results['structure']['chapter_count'] = int(chapter_match.group(1))
        except Exception as e:
            self.results['issues'].append(f"Failed to get chapter count: {e}")

    def check_content(self) -> None:
        """Check content quality."""
        # Extract and check markdown content
        try:
            with zipfile.ZipFile(self.epub_path, 'r') as z:
                xhtml_files = [f for f in z.namelist() if f.endswith('.xhtml')]

                total_content = ""
                for xhtml in xhtml_files[:10]:  # Sample first 10 chapters
                    try:
                        content = z.read(xhtml).decode('utf-8')
                        total_content += content
                    except:
                        pass

                # Count Chinese descriptions
                image_desc_count = len(re.findall(r'【图片描述】', total_content))
                code_desc_count = len(re.findall(r'【代码说明】', total_content))
                table_desc_count = len(re.findall(r'【表格说明】', total_content))

                self.results['content']['image_descriptions'] = image_desc_count
                self.results['content']['code_descriptions'] = code_desc_count
                self.results['content']['table_descriptions'] = table_desc_count

                # Check Chinese ratio
                chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', total_content))
                total_chars = len(re.sub(r'\s', '', total_content))
                if total_chars > 0:
                    self.results['content']['chinese_ratio'] = round(
                        chinese_chars / total_chars * 100, 1
                    )

        except Exception as e:
            self.results['issues'].append(f"Content check failed: {e}")

    def generate_recommendations(self) -> None:
        """Generate improvement recommendations."""
        content = self.results.get('content', {})
        structure = self.results.get('structure', {})

        # Image descriptions
        if content.get('image_descriptions', 0) < structure.get('image_count', 0) * 0.9:
            self.results['recommendations'].append(
                "P1: Add more image descriptions (current: {}, images: {})".format(
                    content.get('image_descriptions', 0),
                    structure.get('image_count', 0)
                )
            )

        # Chinese ratio
        chinese_ratio = content.get('chinese_ratio', 0)
        if chinese_ratio < 30:
            self.results['recommendations'].append(
                f"P0: Translate more content to Chinese (current: {chinese_ratio}%)"
            )
        elif chinese_ratio < 70:
            self.results['recommendations'].append(
                f"P1: Consider translating remaining content (current: {chinese_ratio}%)"
            )

        # Cover
        if not structure.get('has_cover', False):
            self.results['recommendations'].append(
                "P1: Add cover image"
            )

    def print_report(self) -> None:
        """Print quality report."""
        print("\n" + "=" * 60)
        print("EPUB Quality Report")
        print("=" * 60)

        print("\n📁 Structure:")
        for key, value in self.results.get('structure', {}).items():
            print(f"  • {key}: {value}")

        print("\n📝 Content:")
        for key, value in self.results.get('content', {}).items():
            print(f"  • {key}: {value}")

        if self.results.get('issues'):
            print("\n⚠️  Issues:")
            for issue in self.results['issues']:
                print(f"  • {issue}")

        if self.results.get('recommendations'):
            print("\n💡 Recommendations:")
            for rec in self.results['recommendations']:
                print(f"  • {rec}")

        print("\n" + "=" * 60)

        # Calculate score
        score = 100
        if self.results.get('issues'):
            score -= len(self.results['issues']) * 10
        if self.results.get('recommendations'):
            score -= len(self.results['recommendations']) * 5

        score = max(0, score)
        print(f"Overall Score: {score}/100")
        print("=" * 60 + "\n")


def main():
    parser = argparse.ArgumentParser(description='Check EPUB quality')
    parser.add_argument('epub_path', help='Path to EPUB file')
    parser.add_argument('--json', action='store_true', help='Output as JSON')

    args = parser.parse_args()

    checker = EPUBQualityChecker(args.epub_path)
    checker.check_all()

    if args.json:
        import json
        print(json.dumps(checker.results, indent=2))
    else:
        checker.print_report()


if __name__ == '__main__':
    main()