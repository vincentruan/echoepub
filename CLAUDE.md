# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This project (echoepub) reads epub, pdf, and markdown files and regenerates new epub files optimized for audiobook-style reading. Key features include:

- Extracting and adding text explanations for images, charts, and other visual content
- Translating non-Chinese content (English, Japanese, etc.) to Chinese
- Generating EPUB files with improved accessibility for audio-based consumption

## Architecture: Three-Step Pipeline

The codebase is organized around a modular three-step document processing pipeline:

```
输入文件 → [步骤1: 转 Markdown] → [步骤2: 收听优化] → [步骤3: 生成 EPUB] → 输出电子书
```

### 步骤 1: 输入转 Markdown

根据输入文件类型选择对应的转换器：

| 输入格式 | 使用技能 | 说明 |
|----------|----------|------|
| EPUB | `epub-to-markdown-converter` | 提取章节、文本、图片 |
| PDF | `pdf-to-markdown-converter` | PDF 转 Markdown，提取图片 |
| Markdown | `markdown-converter` | 拆分章节，规范化结构 |
| 其他格式 | 参考 `input-converter-template` 创建 | 扩展支持 |

**输出格式统一**：所有转换器输出相同的标准目录结构

```
$原文件名_markdown/
├── 00_目录.md           # 目录文件
├── 01_章节.md           # 章节文件
├── images/              # 图片资源
└── $原文件名_report.md  # 处理报告
```

### 步骤 2: Markdown 收听优化

使用 `markdown-to-audioread` 技能进行内容优化：

- 图片描述生成（AI 分析或占位符）
- 非中文内容翻译
- 表格/列表转语音友好格式
- 添加章节导语和总结
- 句子优化

### 步骤 3: 生成 EPUB

使用 `markdown-to-epub` 技能生成最终电子书：

- 封面生成（AI 封面或程序化封面）
- 目录导航
- 图片嵌入
- 专业排版样式

## Workflow Example

处理一本 EPUB 电子书的完整流程：

```bash
# 步骤 1: EPUB 转 Markdown
node ~/.claude/skills/epub-to-markdown-converter/scripts/epub-reader/dist/index.js convert "input.epub"

# 步骤 2: 收听优化
python ~/.claude/skills/markdown-to-audioread/scripts/audioread_processor.py "input_markdown/"

# 步骤 3: 生成 EPUB
python -c "
from epub_generator import create_epub_from_folder
create_epub_from_folder('input_markdown/', title='书名', author='作者')
"
```

## 处理报告

每个步骤都会在源文件同级目录生成或更新处理报告（`$原文件名_report.md`），记录：

- 处理时间
- 章节信息
- 图片处理统计
- 翻译/优化统计
- 异常信息

用于异常时定位问题。

## Skills Directory

```
.claude/skills/
├── epub-to-markdown-converter/   # EPUB 转 Markdown
├── pdf-to-markdown-converter/    # PDF 转 Markdown
├── markdown-converter/           # Markdown 格式化
├── markdown-to-audioread/        # 收听优化
├── markdown-to-epub/             # 生成 EPUB
└── input-converter-template/     # 新格式转换器模板
```

## Environment Variables

| 变量 | 说明 |
|------|------|
| `SILICONFLOW_API_KEY` | 图片描述和封面生成 API Key |

## Development Commands

安装依赖：

```bash
pip install ebooklib Pillow PyMuPDF requests
```

可选（语法高亮）：

```bash
pip install pygments
```
