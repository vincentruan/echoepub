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
输入文件 → [步骤1: 转 Markdown] → [步骤2a: 内容增强] → [步骤2b: 格式清理] → [步骤2c: 翻译(可选)] → [步骤3: 生成 EPUB] → 输出电子书
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

### 步骤 2: Markdown 收听优化（三个独立技能）

#### 步骤 2a: 内容增强

使用 `markdown-content-enhancer` 技能为图片、代码块、表格添加描述：

- 图片描述生成（调用视觉模型 API + Agent 上下文总结）
  - 支持识别并跳过装饰性图片（二维码、图标、封面等）
  - 文件大小 < 500B 或尺寸 < 50x50px 的图片自动跳过
  - 可通过 `image_descriptor.py` 批量处理，支持多路并行
- 代码块功能说明（Agent 直接生成）
  - 支持识别 ``` 包裹的标准代码块
  - 支持识别未包裹的代码段落（EPUB 转换常见问题）
- 表格内容描述（Agent 直接生成）
- 输出到 `_enhanced/` 子目录
- **自动修正图片路径**：`./images/` → `../images/`（因输出在子目录中）

#### 步骤 2b: 格式清理

使用 `markdown-format-cleaner` 技能清理格式问题：

- 压缩多余空行、统一列表缩进
- 修复未闭合代码块、补充标题/表格前后空行
- **未包裹代码段落**自动用 ``` 标记包裹（识别函数定义、SQL、伪代码等）
- **代码缩进修复**：恢复 EPUB/PDF 转换后丢失的缩进
- 自动修正图片路径
- 输出到 `_cleaned/` 子目录

#### 步骤 2c: 翻译（条件执行）

使用 `markdown-translator` 技能翻译非中文内容：

- 仅在文档主体为非中文时执行
- 语言检测排除代码块、行内代码、URL、技术术语后统计中文占比
- 技术类中文文档（夹杂大量英文术语）智能识别为中文，避免误翻译
- 保留技术术语、代码、变量名
- 输出到 `_translated/` 子目录

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

# 步骤 2a: 内容增强（图片/代码/表格描述）
# 方式 1: 使用 Python 脚本批量处理图片描述（推荐，快速）
cd input_markdown
python ~/.claude/skills/markdown-content-enhancer/scripts/image_descriptor.py "chapter.md" "./images"

# 方式 2: 使用 Agent 完整处理（图片+代码+表格描述，较慢）
# 通过 Claude Code 调用 markdown-content-enhancer skill

# 步骤 2b: 格式清理（可选）
# 使用 markdown-format-cleaner 技能处理

# 步骤 2c: 翻译（可选，仅非中文文档）
# 使用 markdown-translator 技能处理

# 步骤 3: 生成 EPUB
python -c "
import sys
sys.path.insert(0, '~/.claude/skills/markdown-to-epub/scripts')
from epub_generator import create_epub_from_markdown

# 合并所有章节
chapters = sorted(Path('_enhanced').glob('*.md'))
content = '\n\n'.join([open(c).read() for c in chapters])

# 生成 EPUB
create_epub_from_markdown(
    markdown_content=content,
    output_path='output.epub',
    title='书名',
    author='作者',
    base_path='_enhanced',  # 图片路径基准目录
    generate_cover=True,
    use_programmatic_cover=True
)
"
```

## 批量处理技巧

### 并行处理图片描述

对于大量章节，可以分批并行运行 `image_descriptor.py`：

```bash
# 将章节分成 4 批
split -l 20 chapters.txt batch_

# 4 路并行处理
for batch in batch_*; do
  while read chapter; do
    python image_descriptor.py "$chapter" "./images"
  done < "$batch" &
done
wait
```

### Python 脚本批量转换

对于 `_with_descriptions.md` 中间文件批量转换为 `_enhanced/`：

```python
import re, glob
from pathlib import Path

for wd_file in glob.glob("*_with_descriptions.md"):
    with open(wd_file) as f:
        content = f.read()

    # 转换 IMAGE_DESCRIPTION 注释为引用块
    content = re.sub(
        r'<!-- IMAGE_DESCRIPTION: (.*?) -->',
        r'\n> 【图片描述】\1\n',
        content,
        flags=re.DOTALL
    )

    # 修正图片路径
    content = content.replace('./images/', '../images/')

    # 写入 _enhanced/
    name = wd_file.replace('_with_descriptions.md', '.md')
    Path('_enhanced').mkdir(exist_ok=True)
    with open(f'_enhanced/{name}', 'w') as f:
        f.write(content)
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
├── markdown-content-enhancer/    # 内容增强（图片/代码/表格描述）
├── markdown-format-cleaner/      # 格式清理
├── markdown-translator/          # 翻译（条件执行）
├── markdown-to-epub/             # 生成 EPUB
├── input-converter-template/     # 新格式转换器模板
└── _backup/                      # 已归档的旧技能
```

## Environment Variables

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `ECHO_EPUB_OPEN_API_KEY` | 图片描述视觉模型 API Key（必须） | - |
| `ECHO_EPUB_OPEN_AI_BASE_URL` | OpenAI 兼容 API 地址 | `https://api.siliconflow.cn/v1` |
| `ECHO_EPUB_VLM_MODEL` | 视觉模型名称 | `Pro/Qwen/Qwen2.5-VL-7B-Instruct` |
| `SILICONFLOW_API_KEY` | 封面生成 API Key（可选） | - |

> 支持任何 OpenAI 兼容的 API 接口（SiliconFlow、阿里云 DashScope 等），通过 `ECHO_EPUB_OPEN_AI_BASE_URL` 切换。

## 已知问题与注意事项

- **图片路径**：输出到子目录（`_enhanced/`、`_cleaned/`、`_translated/`）时，图片引用路径需从 `./images/` 改为 `../images/`，各 skill 已内置此修正
- **EPUB 图片尺寸**：EPUB 转换后的图片通常较小，`image_descriptor.py` 的最小文件大小阈值已调整为 500B（原 2KB 会误跳过有意义的小图）
- **未包裹代码块**：EPUB 转换后代码缩进和 ``` 标记经常丢失，`format-cleaner` 负责识别并包裹，`content-enhancer` 也能识别未包裹代码并添加说明
- **EPUB 生成 API**：`epub_generator.py` 提供 `create_epub_from_markdown()` 函数（非 `create_epub_from_folder`），需先合并章节为单个 Markdown 字符串，`base_path` 应指向章节文件所在目录以正确解析相对图片路径

## Development Commands

安装依赖：

```bash
pip install ebooklib Pillow PyMuPDF requests
```

可选（语法高亮）：

```bash
pip install pygments
```
