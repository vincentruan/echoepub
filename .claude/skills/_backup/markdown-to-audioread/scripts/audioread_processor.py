#!/usr/bin/env python3
"""
Audioread Processor - 将 Markdown 转换为适合语音朗读的格式

功能：
- 并行章节处理 (subagent)
- 图片描述生成（调用第三方视觉模型）
- 代码块功能说明（由 agent 在 skill 层处理）
- 数学公式描述
- 引用块音频标记
- 表格/列表语音化转换
- 非中文内容翻译
- 章节导语/总结
"""

import os
import sys
import re
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import subprocess

# 导入处理模块
try:
    from image_descriptor import ImageDescriptor, describe_images_in_markdown
except ImportError:
    ImageDescriptor = None
    describe_images_in_markdown = None

try:
    from translate_content import translate_paragraph, is_non_chinese
except ImportError:
    translate_paragraph = None
    is_non_chinese = None


class AudioreadProcessor:
    """将 Markdown 文件处理为适合语音朗读的格式。"""

    def __init__(self, config: dict = None):
        self.config = config or {}
        self.stats = {
            'chapters_processed': 0,
            'images_described': 0,
            'paragraphs_translated': 0,
            'tables_converted': 0,
            'lists_converted': 0,
            'code_blocks_processed': 0,
            'quotes_processed': 0,
            'math_formulas_processed': 0,
            'chapters_with_intro': 0,
        }
        self.glossary = {}
        self.use_subagents = self.config.get('use_subagents', True)

    # ---- 文件夹处理 ----

    def process_folder(self, folder_path: Path) -> dict:
        """处理标准 Markdown 文件夹。

        在源文件夹同级目录下创建 _audioread 子文件夹保存处理结果，源文件不会被修改。
        """
        folder_path = Path(folder_path)

        # 创建输出目录
        output_dir = folder_path / '_audioread'
        output_dir.mkdir(exist_ok=True)

        chapter_files = sorted([
            f for f in folder_path.glob('*.md')
            if f.name != '00_目录.md'
            and not f.name.endswith('_report.md')
            and not f.name == 'glossary.md'
        ])

        print(f"发现 {len(chapter_files)} 个章节文件")
        print(f"输出目录: {output_dir}")

        if self.use_subagents and len(chapter_files) > 1:
            print("使用 subagent 并行处理...")
            self._process_with_subagents(folder_path, chapter_files, output_dir)
        else:
            print("使用顺序处理...")
            for chapter_file in chapter_files:
                print(f"处理: {chapter_file.name}")
                output_file = output_dir / chapter_file.name
                self.process_chapter(chapter_file, output_file)

        # 生成术语表
        if self.glossary:
            self._write_glossary(output_dir / 'glossary.md')

        # 更新报告
        self._update_report(folder_path, output_dir)

        return self.stats

    def _process_with_subagents(self, folder_path: Path, chapter_files: List[Path], output_dir: Path):
        """使用 subagent 并行处理章节。"""
        script = self._create_subagent_script()
        batch_size = 5

        for i in range(0, len(chapter_files), batch_size):
            batch = chapter_files[i:i + batch_size]
            batch_num = i // batch_size + 1
            total_batches = (len(chapter_files) + batch_size - 1) // batch_size

            print(f"\n处理批次 {batch_num}/{total_batches} ({len(batch)} 章)...")
            for chapter_file in batch:
                self._invoke_subagent(script, chapter_file, folder_path)

    def _create_subagent_script(self) -> str:
        """创建 subagent 独立处理脚本。"""
        return '''#!/usr/bin/env python3
"""Subagent: 处理单个章节。"""
import sys, json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from audioread_processor import AudioreadProcessor

def main():
    if len(sys.argv) < 3:
        print("Usage: subagent.py <chapter_file> <base_folder>", file=sys.stderr)
        sys.exit(1)

    processor = AudioreadProcessor({'use_subagents': False})
    try:
        processor.process_chapter(Path(sys.argv[1]))
        print(json.dumps({'status': 'success', 'stats': processor.stats}))
    except Exception as e:
        print(json.dumps({'status': 'error', 'error': str(e)}), file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
'''

    def _invoke_subagent(self, script_content: str, chapter_file: Path, base_folder: Path):
        """调用 subagent 处理一个章节。"""
        script_path = base_folder / ".subagent_process.py"
        with open(script_path, 'w') as f:
            f.write(script_content)

        try:
            result = subprocess.run(
                [sys.executable, str(script_path), str(chapter_file), str(base_folder)],
                capture_output=True, text=True, timeout=300
            )

            if result.returncode == 0:
                try:
                    output = json.loads(result.stdout.strip())
                    if output.get('status') == 'success':
                        for key, value in output.get('stats', {}).items():
                            self.stats[key] = self.stats.get(key, 0) + value
                        self.stats['chapters_processed'] += 1
                        print(f"  ✓ {chapter_file.name}")
                except json.JSONDecodeError:
                    print(f"  ⚠ {chapter_file.name} (解析统计失败)")
            else:
                print(f"  ✗ {chapter_file.name} (错误: {result.stderr[:100]})")

        except subprocess.TimeoutExpired:
            print(f"  ✗ {chapter_file.name} (超时)")
        except Exception as e:
            print(f"  ✗ {chapter_file.name} (异常: {e})")
        finally:
            if script_path.exists():
                script_path.unlink()

    # ---- 章节处理 ----

    def process_chapter(self, file_path: Path, output_path: Path = None):
        """处理单个章节文件。

        Args:
            file_path: 源文件路径（只读）
            output_path: 输出文件路径（默认为源文件同目录下 _audioread 子文件夹）
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 提取章节标题
        title_match = re.match(r'^#\s+(.+)$', content, re.MULTILINE)
        title = title_match.group(1) if title_match else file_path.stem

        # 按顺序处理各类内容
        # 注意：代码块说明由 agent 在 skill 层直接生成，此处仅做标记提取
        content = self._process_code_blocks(content)
        content = self._process_math_formulas(content)
        content = self._process_blockquotes(content)
        content = self._process_images(content, file_path.parent)

        if self.config.get('translate', True):
            content = self._translate_content(content)

        content = self._convert_tables(content)
        content = self._convert_lists(content)

        if self.config.get('add_intro', True):
            content = self._add_chapter_intro(content, title)

        content = self._optimize_sentences(content)

        # 写入输出文件（不修改源文件）
        if output_path is None:
            output_dir = file_path.parent / '_audioread'
            output_dir.mkdir(exist_ok=True)
            output_path = output_dir / file_path.name

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)

        self.stats['chapters_processed'] += 1

    # ---- 代码块处理 ----
    # 注意：代码的功能总结和关键实现说明由 agent 在 skill.md 指导下直接生成
    # 此脚本仅提取代码块信息，实际的文字说明在 agent 处理时完成

    def _process_code_blocks(self, content: str) -> str:
        """为代码块添加音频友好标记。

        agent 在处理章节时会结合上下文直接为代码块生成功能说明，
        此方法仅做基础的代码块识别和统计。
        """
        lines = content.split('\n')
        result = []
        in_code_block = False
        code_lang = ''

        for line in lines:
            if line.strip().startswith('```'):
                if not in_code_block:
                    in_code_block = True
                    code_lang = line.strip()[3:].strip() or '代码'
                    result.append(line)
                else:
                    in_code_block = False
                    result.append(line)
                    self.stats['code_blocks_processed'] += 1
            else:
                result.append(line)

        return '\n'.join(result)

    # ---- 数学公式处理 ----

    def _process_math_formulas(self, content: str) -> str:
        """为数学公式添加描述标记。"""
        def replace_block_math(match):
            formula = match.group(1)
            self.stats['math_formulas_processed'] += 1
            ftype = self._infer_formula_type(formula)
            return f'> 【数学公式】\n> 该公式为{ftype}。\n> 建议查看原文获取准确表达式。\n\n$$\n{formula}\n$$'

        content = re.sub(r'\$\$([^\$]+)\$\$', replace_block_math, content, flags=re.DOTALL)

        def replace_inline_math(match):
            formula = match.group(1)
            self.stats['math_formulas_processed'] += 1
            return f'（公式：{self._infer_formula_type(formula)}）$$ {formula} $$'

        content = re.sub(r'\$([^\$]+)\$', replace_inline_math, content)
        return content

    def _infer_formula_type(self, formula: str) -> str:
        """推断公式类型。"""
        if any(op in formula for op in ['+', '-', '=', '∑', '∫']):
            return '计算公式'
        elif any(op in formula for op in ['√', 'x^', '²', '³']):
            return '方程式'
        elif any(s in formula for s in ['α', 'β', 'θ', 'λ', 'μ', 'σ']):
            return '希腊字母表达式'
        elif any(s in formula for s in ['\\frac', '\\over', '/']):
            return '分式'
        elif any(s in formula for s in ['∞', 'lim', '→']):
            return '极限表达式'
        elif any(s in formula for s in ['∂', '∇', 'dx', 'dy']):
            return '微分表达式'
        return '数学表达式'

    # ---- 引用块处理 ----

    def _process_blockquotes(self, content: str) -> str:
        """为引用块添加音频标记。"""
        lines = content.split('\n')
        result = []
        quote_lines = []

        for line in lines:
            if line.strip().startswith('>'):
                quote_lines.append(line)
            else:
                if quote_lines:
                    result.extend(self._format_quote_block(quote_lines))
                    quote_lines = []
                result.append(line)

        if quote_lines:
            result.extend(self._format_quote_block(quote_lines))

        return '\n'.join(result)

    def _format_quote_block(self, quote_lines: List[str]) -> List[str]:
        """格式化引用块。"""
        combined = ' '.join([line.lstrip('>').strip() for line in quote_lines])
        # 已格式化的块（图片描述、代码说明等）保持不变
        if any(kw in combined for kw in ['图片描述', '代码说明', '数学公式', '表格', '要点', '引用']):
            return quote_lines

        formatted = ['> 【引用开始】']
        formatted.extend(quote_lines)
        formatted.append('> 【引用结束】')
        self.stats['quotes_processed'] += 1
        return formatted

    # ---- 图片处理 ----

    def _process_images(self, content: str, base_path: Path) -> str:
        """调用第三方视觉模型为图片生成描述。"""
        if ImageDescriptor is None or describe_images_in_markdown is None:
            return content

        try:
            descriptor = ImageDescriptor()
            images_dir = base_path / 'images'
            processed, stats = describe_images_in_markdown(
                content, str(images_dir), descriptor
            )
            self.stats['images_described'] += stats.get('described', 0)
            return processed
        except Exception as e:
            print(f"图片处理异常: {e}")
            return content

    # ---- 翻译处理 ----

    def _translate_content(self, content: str) -> str:
        """翻译非中文段落。"""
        if translate_paragraph is None or is_non_chinese is None:
            return content

        paragraphs = content.split('\n\n')
        translated = []

        for para in paragraphs:
            if is_non_chinese(para) and len(para.strip()) > 50:
                try:
                    translated.append(translate_paragraph(para))
                    self.stats['paragraphs_translated'] += 1
                except Exception:
                    translated.append(para)
            else:
                translated.append(para)

        return '\n\n'.join(translated)

    # ---- 表格转换 ----

    def _convert_tables(self, content: str) -> str:
        """将表格转换为语音友好格式。"""
        pattern = r'(\|[^\n]+\|\n\|[-:| ]+\|\n(?:\|[^\n]+\|\n)+)'

        def replace_table(match):
            table = match.group(0)
            lines = table.strip().split('\n')
            if len(lines) < 3:
                return table

            headers = [h.strip() for h in lines[0].split('|')[1:-1]]
            desc_parts = ["\n> 【表格内容说明】\n"]

            for line in lines[2:]:
                cells = [c.strip() for c in line.split('|')[1:-1]]
                for i, cell in enumerate(cells):
                    if i < len(headers) and cell:
                        desc_parts.append(f"> 关于{headers[i]}：{cell}。")

            desc_parts.append("\n> 原始表格数据见上。\n")
            self.stats['tables_converted'] += 1
            return table + '\n' + '\n'.join(desc_parts)

        return re.sub(pattern, replace_table, content)

    # ---- 列表转换 ----

    def _convert_lists(self, content: str) -> str:
        """将列表转换为语音友好格式。"""
        pattern = r'((?:^[-*+]\s+.+\n){3,})'
        ordinals = ['第一', '第二', '第三', '第四', '第五', '第六', '第七', '第八', '第九', '第十']

        def replace_list(match):
            list_text = match.group(0)
            items = re.findall(r'^[-*+]\s+(.+)$', list_text, re.MULTILINE)
            if len(items) < 3:
                return list_text

            audio_items = [
                f"{ordinals[i]}，{item}。"
                for i, item in enumerate(items) if i < len(ordinals)
            ]

            self.stats['lists_converted'] += 1
            return list_text + f"\n> 以下是{len(items)}个要点：\n" + '\n'.join(audio_items) + '\n'

        return re.sub(pattern, replace_list, content, flags=re.MULTILINE)

    # ---- 章节导语 ----

    def _add_chapter_intro(self, content: str, title: str) -> str:
        """添加章节导语。"""
        intro = f'\n\n> 本章导读：本章"{title}"将为您讲解核心概念与要点。让我们开始学习。\n'
        self.stats['chapters_with_intro'] += 1
        return re.sub(r'^(#\s+.+)$', r'\1' + intro, content, count=1, flags=re.MULTILINE)

    # ---- 句子优化 ----

    def _optimize_sentences(self, content: str) -> str:
        """优化长句，使其更适合听觉理解。"""
        lines = content.split('\n')
        result = []

        for line in lines:
            if len(line) > 200 and not line.startswith('#') and not line.startswith('>'):
                parts = re.split(r'([。！？;；])', line)
                current = ''
                for i in range(0, len(parts), 2):
                    segment = parts[i] + (parts[i + 1] if i + 1 < len(parts) else '')
                    if current and len(current) + len(segment) > 100:
                        result.append(current.strip())
                        current = segment
                    else:
                        current += segment
                if current:
                    result.append(current.strip())
            else:
                result.append(line)

        return '\n'.join(result)

    # ---- 辅助功能 ----

    def _write_glossary(self, output_path: Path):
        """生成术语表文件。"""
        if not self.glossary:
            return
        lines = ["# 术语表", "", "| 术语 | 原文 | 解释 |", "|------|------|------|"]
        for term, (original, explanation) in self.glossary.items():
            lines.append(f"| {term} | {original} | {explanation} |")
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))

    def _update_report(self, folder_path: Path, output_dir: Path = None):
        """更新处理报告。"""
        report_files = list(folder_path.glob('*_report.md'))
        if not report_files:
            return

        # 报告写入输出目录
        target_dir = output_dir or folder_path
        report_path = report_files[0]
        with open(report_path, 'r', encoding='utf-8') as f:
            report_content = f.read()

        section = f"""

## Audioread 处理

- 处理时间：{datetime.now().isoformat()}
- 处理章节：{self.stats['chapters_processed']} 章
- 图片描述：{self.stats['images_described']} 张
- 翻译段落：{self.stats['paragraphs_translated']} 段
- 表格转换：{self.stats['tables_converted']} 个
- 列表转换：{self.stats['lists_converted']} 个
- 代码块处理：{self.stats['code_blocks_processed']} 个
- 引用处理：{self.stats['quotes_processed']} 个
- 数学公式：{self.stats['math_formulas_processed']} 个
- 章节导语：{self.stats['chapters_with_intro']} 章
"""
        output_report = target_dir / report_path.name
        with open(output_report, 'w', encoding='utf-8') as f:
            f.write(report_content + section)


def main():
    if len(sys.argv) < 2:
        print("Usage: python audioread_processor.py <input> [options]")
        print("  input: Markdown 文件或文件夹路径")
        print("  --no-subagents: 禁用 subagent 并行处理")
        print("  --no-translate: 跳过翻译")
        print("  --no-intro: 跳过章节导语")
        sys.exit(1)

    input_path = Path(sys.argv[1]).resolve()

    config = {
        'use_subagents': '--no-subagents' not in sys.argv,
        'translate': '--no-translate' not in sys.argv,
        'add_intro': '--no-intro' not in sys.argv,
    }

    if not input_path.exists():
        print(f"错误: 路径不存在: {input_path}")
        sys.exit(1)

    processor = AudioreadProcessor(config)

    if input_path.is_file():
        print(f"处理单个文件: {input_path}")
        processor.process_chapter(input_path)
    else:
        print(f"处理文件夹: {input_path}")
        processor.process_folder(input_path)

    print("\n=== 处理完成 ===")
    for key, value in processor.stats.items():
        print(f"  {key}: {value}")


if __name__ == "__main__":
    main()
