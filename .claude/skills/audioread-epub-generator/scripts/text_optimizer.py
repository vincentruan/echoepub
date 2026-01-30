# -*- coding: utf-8 -*-
"""
文本优化脚本

功能：
- 常见错别字检测与提示
- 标点符号规范化
- 格式检查

注意：此脚本仅提供辅助检测功能
实际的文本优化（错别字纠正、关键词加粗）应由 AI subagent 完成
以确保理解上下文语义

使用方法：
    python text_optimizer.py <markdown文件或目录>

示例：
    python text_optimizer.py "趋势与周期3-货币债务与投资时钟"
    python text_optimizer.py "趋势与周期3-货币债务与投资时钟/01_第一章.md"
"""

import os
import re
import sys
import glob
from collections import defaultdict

# 常见错别字映射（仅供参考，需人工确认）
COMMON_TYPOS = {
    # 形近字错误
    '己经': '已经',
    '以经': '已经',
    '在再': '（需确认）',
    '那里': '（疑问句中可能是"哪里"）',
    '他她它': '（需确认代词使用）',

    # 同音字错误
    '做作': '（需确认）',
    '副幅': '（需确认）',
    '带代': '（需确认）',

    # 易混淆词
    '的地得': '（需检查使用是否正确）',
    '必须必需': '（需确认）',

    # OCR 常见错误
    '囗': '口',
    '廾': '开',
    '亻': '人',
    '氵': '水',
    '扌': '手',
}

# 应该加粗的关键词模式
BOLD_PATTERNS = [
    # 强调词
    r'(?<![*])(?:重要|关键|核心|必须|注意|警告|提示)(?![*])',
    # 数据（百分比、金额等）
    r'(?<![*\d])\d+(\.\d+)?%(?![*])',
    r'(?<![*\d])\d+(\.\d+)?亿(?![*])',
    r'(?<![*\d])\d+(\.\d+)?万(?![*])',
]

# 标点符号规范
PUNCTUATION_RULES = {
    # 中文环境下应使用中文标点
    r'(?<=[\u4e00-\u9fff]),(?=[\u4e00-\u9fff])': '，',
    r'(?<=[\u4e00-\u9fff])\.(?=[\u4e00-\u9fff])': '。',
    r'(?<=[\u4e00-\u9fff]);(?=[\u4e00-\u9fff])': '；',
    r'(?<=[\u4e00-\u9fff]):(?=[\u4e00-\u9fff])': '：',
    r'(?<=[\u4e00-\u9fff])\?(?=[\u4e00-\u9fff])': '？',
    r'(?<=[\u4e00-\u9fff])!(?=[\u4e00-\u9fff])': '！',
    r'(?<=[\u4e00-\u9fff])\(': '（',
    r'\)(?=[\u4e00-\u9fff])': '）',
}


def analyze_file(filepath):
    """分析单个文件"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
        lines = content.split('\n')

    results = {
        'typo_candidates': [],
        'punctuation_issues': [],
        'bold_candidates': [],
        'format_issues': [],
        'stats': {
            'lines': len(lines),
            'chars': len(content),
            'paragraphs': len([l for l in lines if l.strip()]),
        }
    }

    # 检查可能的错别字
    for typo, suggestion in COMMON_TYPOS.items():
        if typo in content:
            occurrences = content.count(typo)
            results['typo_candidates'].append({
                'text': typo,
                'suggestion': suggestion,
                'count': occurrences
            })

    # 检查标点符号
    for pattern, replacement in PUNCTUATION_RULES.items():
        matches = re.findall(pattern, content)
        if matches:
            results['punctuation_issues'].append({
                'pattern': pattern,
                'replacement': replacement,
                'count': len(matches)
            })

    # 检查可能需要加粗的内容
    for pattern in BOLD_PATTERNS:
        matches = re.findall(pattern, content)
        if matches:
            results['bold_candidates'].append({
                'pattern': pattern,
                'matches': list(set(matches))[:10],  # 最多显示10个
                'count': len(matches)
            })

    # 检查格式问题
    # 1. 标题层级跳跃
    header_levels = []
    for line in lines:
        match = re.match(r'^(#{1,6})\s', line)
        if match:
            header_levels.append(len(match.group(1)))

    for i in range(1, len(header_levels)):
        if header_levels[i] - header_levels[i-1] > 1:
            results['format_issues'].append(f"标题层级跳跃: H{header_levels[i-1]} -> H{header_levels[i]}")

    # 2. 列表格式不统一
    list_markers = set()
    for line in lines:
        if re.match(r'^\s*[-*+]\s', line):
            list_markers.add(line.strip()[0])
    if len(list_markers) > 1:
        results['format_issues'].append(f"列表标记不统一: 使用了 {list_markers}")

    return results


def print_analysis(filepath, results):
    """打印分析结果"""
    print(f"\n{'='*60}")
    print(f"文件: {os.path.basename(filepath)}")
    print(f"{'='*60}")

    stats = results['stats']
    print(f"\n统计: {stats['lines']} 行 | {stats['chars']} 字符 | {stats['paragraphs']} 段落")

    if results['typo_candidates']:
        print(f"\n可能的错别字 ({len(results['typo_candidates'])} 项):")
        for item in results['typo_candidates']:
            print(f"  - '{item['text']}' ({item['count']}次) -> {item['suggestion']}")

    if results['punctuation_issues']:
        print(f"\n标点符号问题 ({len(results['punctuation_issues'])} 项):")
        for item in results['punctuation_issues']:
            print(f"  - {item['replacement']} ({item['count']}处)")

    if results['bold_candidates']:
        print(f"\n建议加粗的内容:")
        for item in results['bold_candidates']:
            samples = ', '.join(str(m) for m in item['matches'][:5])
            print(f"  - {samples}... ({item['count']}处)")

    if results['format_issues']:
        print(f"\n格式问题:")
        for issue in results['format_issues']:
            print(f"  - {issue}")

    if not any([results['typo_candidates'], results['punctuation_issues'],
                results['format_issues']]):
        print("\n未发现明显问题")


def process_directory(directory):
    """处理目录中的所有 markdown 文件"""
    md_files = glob.glob(os.path.join(directory, '*.md'))
    chapter_files = [f for f in md_files if re.match(r'^\d+_', os.path.basename(f))]
    chapter_files.sort(key=lambda f: int(re.match(r'^(\d+)_', os.path.basename(f)).group(1)))

    if not chapter_files:
        print("未找到章节文件")
        return

    print(f"分析 {len(chapter_files)} 个章节文件...")

    all_typos = defaultdict(int)
    all_punct = defaultdict(int)
    all_format = []

    for filepath in chapter_files:
        results = analyze_file(filepath)
        print_analysis(filepath, results)

        # 汇总统计
        for item in results['typo_candidates']:
            all_typos[item['text']] += item['count']
        for item in results['punctuation_issues']:
            all_punct[item['replacement']] += item['count']
        all_format.extend(results['format_issues'])

    # 打印汇总
    print(f"\n{'='*60}")
    print("汇总统计")
    print(f"{'='*60}")

    if all_typos:
        print("\n所有可能的错别字:")
        for text, count in sorted(all_typos.items(), key=lambda x: -x[1]):
            print(f"  - '{text}': {count}次")

    if all_punct:
        print("\n所有标点问题:")
        for punct, count in sorted(all_punct.items(), key=lambda x: -x[1]):
            print(f"  - {punct}: {count}处")


def generate_subagent_prompt(filepath):
    """生成用于 subagent 的优化提示"""
    results = analyze_file(filepath)
    chapter_name = os.path.basename(filepath)

    prompt = f"""
任务：优化电子书章节文本

文件路径：{filepath}
章节名称：{chapter_name}

预扫描发现以下潜在问题：
"""

    if results['typo_candidates']:
        prompt += "\n可能的错别字：\n"
        for item in results['typo_candidates']:
            prompt += f"- '{item['text']}' 出现 {item['count']} 次\n"

    if results['punctuation_issues']:
        prompt += "\n标点符号问题：\n"
        for item in results['punctuation_issues']:
            prompt += f"- 需替换为 {item['replacement']} ({item['count']}处)\n"

    if results['format_issues']:
        prompt += "\n格式问题：\n"
        for issue in results['format_issues']:
            prompt += f"- {issue}\n"

    prompt += """
请完成以下任务：

1. **错别字纠正**
   - 根据上下文确认并纠正错别字
   - 注意区分形近字、同音字的正确用法
   - 记录所有纠正项

2. **文本格式优化**
   - 对关键概念、重要结论使用 **加粗** 标记
   - 确保标点符号使用正确（中英文标点一致）
   - 优化段落分隔，确保阅读流畅

3. **忠于原文原则**
   - 不改变原文含义
   - 不添加原文没有的内容
   - 保持作者的写作风格

完成后返回修改统计和主要修改列表。
"""
    return prompt


def main():
    if len(sys.argv) < 2:
        print("使用方法:")
        print("  python text_optimizer.py <markdown文件或目录>")
        print("  python text_optimizer.py <目录> --prompt  # 生成 subagent 提示")
        sys.exit(1)

    target = sys.argv[1]
    generate_prompt = '--prompt' in sys.argv

    if os.path.isfile(target):
        if generate_prompt:
            print(generate_subagent_prompt(target))
        else:
            results = analyze_file(target)
            print_analysis(target, results)
    elif os.path.isdir(target):
        if generate_prompt:
            md_files = glob.glob(os.path.join(target, '*.md'))
            chapter_files = [f for f in md_files if re.match(r'^\d+_', os.path.basename(f))]
            for f in sorted(chapter_files):
                print(f"\n{'#'*60}")
                print(generate_subagent_prompt(f))
        else:
            process_directory(target)
    else:
        print(f"错误：路径不存在 - {target}")
        sys.exit(1)


if __name__ == "__main__":
    main()
