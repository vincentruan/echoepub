#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
详细的EPUB质量核对脚本
按照用户要求检查：
1. 翻译后的内容是否与原文（英文）语义一致
2. 技术术语恰当保留
3. 章节排版结构合理
4. 对代码和图片添加的描述恰当
"""

import re
import sys
from pathlib import Path
from dataclasses import dataclass
from typing import List, Tuple

@dataclass
class VerificationResult:
    category: str
    item: str
    status: str  # PASS, FAIL, WARNING
    details: str
    original: str = ""
    translated: str = ""

def extract_prose_text(html_content: str) -> str:
    """提取HTML中的散文文本（排除代码块）"""
    # 移除<style>标签
    text = re.sub(r'<style[^>]*>.*?</style>', '', html_content, flags=re.DOTALL)
    # 移除<blockquote>（代码块）
    text = re.sub(r'<blockquote[^>]*>.*?</blockquote>', '', text, flags=re.DOTALL)
    # 移除<div class="image-container">...</div>（图片）
    text = re.sub(r'<div class="image-container">.*?</div>', '', text, flags=re.DOTALL)
    # 移除HTML标签
    text = re.sub(r'<[^>]+>', ' ', text)
    # 清理空白
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def extract_code_blocks(html_content: str) -> List[str]:
    """提取代码块"""
    return re.findall(r'<blockquote[^>]*>(.*?)</blockquote>', html_content, re.DOTALL)

def extract_images(html_content: str) -> List[Tuple[str, str]]:
    """提取图片及其alt文本"""
    return re.findall(r'<img[^>]*src="([^"]+)"[^>]*alt="([^"]*)"[^>]*/?>', html_content)

def check_semantic_consistency(original: str, translated: str) -> List[VerificationResult]:
    """检查语义一致性"""
    results = []

    # 检查关键概念翻译
    key_concepts = [
        ("static factory method", "静态工厂方法"),
        ("constructor", "构造器"),
        ("singleton", "单例"),
        ("immutable", "不可变"),
        ("instance-controlled", "实例受控"),
        ("service provider framework", "服务提供者框架"),
        ("Flyweight pattern", "享元模式"),
        ("builder pattern", "构建器模式"),
        ("telescoping constructor", "伸缩构造器"),
        ("functional interface", "函数式接口"),
        ("lambda", "lambda"),
        ("type inference", "类型推断"),
    ]

    for eng, chn in key_concepts:
        if eng.lower() in original.lower():
            if chn in translated:
                results.append(VerificationResult(
                    category="语义一致性",
                    item=f"'{eng}' 翻译",
                    status="PASS",
                    details=f"正确翻译为 '{chn}'",
                    original=eng,
                    translated=chn
                ))
            else:
                # 检查是否在代码块中保留英文
                if eng in translated:
                    results.append(VerificationResult(
                        category="语义一致性",
                        item=f"'{eng}' 保留",
                        status="PASS",
                        details=f"在上下文中保留英文（可能是代码或专有名词）",
                        original=eng,
                        translated=eng
                    ))
                else:
                    results.append(VerificationResult(
                        category="语义一致性",
                        item=f"'{eng}' 翻译",
                        status="WARNING",
                        details=f"未找到对应翻译",
                        original=eng,
                        translated="[未找到]"
                    ))

    return results

def check_technical_terms(original: str, translated: str) -> List[VerificationResult]:
    """检查技术术语保留"""
    results = []

    # 应该保留英文的技术术语（类名、方法名等）
    java_identifiers = [
        # 类名
        r'\bBoolean\b', r'\bString\b', r'\bInteger\b', r'\bBigInteger\b',
        r'\bEnumSet\b', r'\bRegularEnumSet\b', r'\bJumboEnumSet\b',
        r'\bCollections\b', r'\bComparator\b', r'\bList\b', r'\bSet\b', r'\bMap\b',
        r'\bServiceLoader\b', r'\bDriverManager\b', r'\bConnection\b',
        r'\bStackWalker\b', r'\bArray\b', r'\bFiles\b', r'\bFileStore\b',
        r'\bBufferedReader\b', r'\bDoubleBinaryOperator\b',
        # 方法名模式
        r'\bvalueOf\b', r'\btoString\b', r'\bgetInstance\b', r'\bvalueOf\b',
        r'\bcompareTo\b', r'\bapplyAsDouble\b',
    ]

    for pattern in java_identifiers:
        matches_orig = set(re.findall(pattern, original))
        matches_trans = set(re.findall(pattern, translated))

        for term in matches_orig:
            if term in matches_trans:
                results.append(VerificationResult(
                    category="技术术语保留",
                    item=f"'{term}' 类名/方法名",
                    status="PASS",
                    details=f"正确保留英文",
                    original=term,
                    translated=term
                ))
            else:
                results.append(VerificationResult(
                    category="技术术语保留",
                    item=f"'{term}' 类名/方法名",
                    status="FAIL",
                    details=f"技术术语丢失",
                    original=term,
                    translated="[丢失]"
                ))

    return results

def check_code_blocks(original: str, translated: str) -> List[VerificationResult]:
    """检查代码块完整性"""
    results = []

    orig_codes = extract_code_blocks(original)
    trans_codes = extract_code_blocks(translated)

    results.append(VerificationResult(
        category="代码块检查",
        item="代码块数量",
        status="PASS" if len(orig_codes) == len(trans_codes) else "WARNING",
        details=f"原文 {len(orig_codes)} 个代码块，译文 {len(trans_codes)} 个代码块",
        original=str(len(orig_codes)),
        translated=str(len(trans_codes))
    ))

    # 检查代码内容是否一致
    for i, (orig, trans) in enumerate(zip(orig_codes[:5], trans_codes[:5])):
        # 清理空白后比较
        orig_clean = re.sub(r'\s+', ' ', orig).strip()
        trans_clean = re.sub(r'\s+', ' ', trans).strip()

        if orig_clean == trans_clean:
            results.append(VerificationResult(
                category="代码块检查",
                item=f"代码块 {i+1} 内容",
                status="PASS",
                details="代码内容完全保留",
                original=orig_clean[:50] + "..." if len(orig_clean) > 50 else orig_clean,
                translated="[一致]"
            ))
        else:
            results.append(VerificationResult(
                category="代码块检查",
                item=f"代码块 {i+1} 内容",
                status="WARNING",
                details="代码内容有差异",
                original=orig_clean[:50] + "..." if len(orig_clean) > 50 else orig_clean,
                translated=trans_clean[:50] + "..." if len(trans_clean) > 50 else trans_clean
            ))

    return results

def check_images(original: str, translated: str) -> List[VerificationResult]:
    """检查图片描述"""
    results = []

    orig_images = extract_images(original)
    trans_images = extract_images(translated)

    results.append(VerificationResult(
        category="图片检查",
        item="图片数量",
        status="PASS" if len(trans_images) >= len(orig_images) else "WARNING",
        details=f"原文 {len(orig_images)} 张图片（可能为链接），译文 {len(trans_images)} 张图片",
        original=str(len(orig_images)),
        translated=str(len(trans_images))
    ))

    # 检查图片alt文本
    for i, (src, alt) in enumerate(trans_images[:5]):
        if alt and alt != "图片":
            results.append(VerificationResult(
                category="图片检查",
                item=f"图片 {i+1} 描述",
                status="PASS",
                details=f"有描述性alt文本: '{alt}'",
                original="",
                translated=alt
            ))
        elif alt == "代码截图":
            results.append(VerificationResult(
                category="图片检查",
                item=f"图片 {i+1} 描述",
                status="PASS",
                details=f"代码截图类型",
                original="",
                translated=alt
            ))
        else:
            results.append(VerificationResult(
                category="图片检查",
                item=f"图片 {i+1} 描述",
                status="WARNING",
                details=f"缺少描述性alt文本",
                original="",
                translated=alt or "[无]"
            ))

    return results

def check_chapter_structure(original_dir: Path, translated_dir: Path) -> List[VerificationResult]:
    """检查章节结构"""
    results = []

    orig_files = sorted(original_dir.glob('*.md'))
    trans_files = sorted(translated_dir.glob('*.md'))

    # 过滤掉目录和报告文件
    orig_chapters = [f for f in orig_files if not f.name.startswith('00_') and '_report' not in f.name]
    trans_chapters = [f for f in trans_files if not f.name.startswith('00_') and '_report' not in f.name]

    results.append(VerificationResult(
        category="章节结构",
        item="章节数量",
        status="PASS" if len(orig_chapters) == len(trans_chapters) else "WARNING",
        details=f"原文 {len(orig_chapters)} 章，译文 {len(trans_chapters)} 章",
        original=str(len(orig_chapters)),
        translated=str(len(trans_chapters))
    ))

    # 检查章节编号对应
    for orig_file in orig_chapters:
        match = re.match(r'^(\d+)_', orig_file.name)
        if match:
            chapter_num = match.group(1)
            trans_file = list(translated_dir.glob(f'{chapter_num}_*.md'))
            if trans_file:
                results.append(VerificationResult(
                    category="章节结构",
                    item=f"章节 {chapter_num} 对应",
                    status="PASS",
                    details=f"找到对应译文文件",
                    original=orig_file.name,
                    translated=trans_file[0].name
                ))
            else:
                results.append(VerificationResult(
                    category="章节结构",
                    item=f"章节 {chapter_num} 对应",
                    status="FAIL",
                    details=f"缺少对应译文文件",
                    original=orig_file.name,
                    translated="[缺失]"
                ))

    return results

def generate_report(results: List[VerificationResult], output_path: Path):
    """生成核对报告"""
    report = []
    report.append("# EPUB 详细质量核对报告\n")
    report.append(f"生成时间: {__import__('datetime').datetime.now().isoformat()}\n")

    # 统计
    pass_count = sum(1 for r in results if r.status == "PASS")
    fail_count = sum(1 for r in results if r.status == "FAIL")
    warning_count = sum(1 for r in results if r.status == "WARNING")

    report.append("\n## 总结\n")
    report.append(f"- ✅ 通过: {pass_count}\n")
    report.append(f"- ❌ 失败: {fail_count}\n")
    report.append(f"- ⚠️ 警告: {warning_count}\n")

    # 按类别分组
    categories = {}
    for r in results:
        if r.category not in categories:
            categories[r.category] = []
        categories[r.category].append(r)

    report.append("\n## 详细结果\n")

    for category, items in categories.items():
        report.append(f"\n### {category}\n")
        for item in items:
            status_icon = "✅" if item.status == "PASS" else ("❌" if item.status == "FAIL" else "⚠️")
            report.append(f"\n{status_icon} **{item.item}**: {item.status}\n")
            report.append(f"   - {item.details}\n")
            if item.original or item.translated:
                report.append(f"   - 原文: `{item.original}` → 译文: `{item.translated}`\n")

    output_path.write_text('\n'.join(report), encoding='utf-8')
    print(f"报告已生成: {output_path}")
    print(f"\n总结: ✅ 通过 {pass_count} | ❌ 失败 {fail_count} | ⚠️ 警告 {warning_count}")

def main():
    if len(sys.argv) < 3:
        print("用法: python detailed_verification.py <原文目录> <译文EPUB提取目录> [输出报告路径]")
        return 1

    original_dir = Path(sys.argv[1])
    translated_dir = Path(sys.argv[2])
    output_path = Path(sys.argv[3]) if len(sys.argv) > 3 else Path('detailed_verification_report.md')

    results = []

    # 检查章节结构
    print("检查章节结构...")
    results.extend(check_chapter_structure(original_dir, translated_dir))

    # 检查每个章节
    print("检查章节内容...")
    orig_files = sorted(original_dir.glob('*.md'))

    for orig_file in orig_files[:3]:  # 抽样检查前3章
        if orig_file.name.startswith('00_') or '_report' in orig_file.name:
            continue

        match = re.match(r'^(\d+)_', orig_file.name)
        if not match:
            continue

        chapter_num = match.group(1)
        trans_file = list(translated_dir.glob(f'{chapter_num}_*.md'))

        if not trans_file:
            continue

        print(f"  处理章节 {chapter_num}...")

        orig_content = orig_file.read_text(encoding='utf-8')
        trans_content = trans_file[0].read_text(encoding='utf-8')

        results.extend(check_semantic_consistency(orig_content, trans_content))
        results.extend(check_technical_terms(orig_content, trans_content))
        results.extend(check_code_blocks(orig_content, trans_content))
        results.extend(check_images(orig_content, trans_content))

    # 生成报告
    generate_report(results, output_path)

    return 0

if __name__ == "__main__":
    exit(main())