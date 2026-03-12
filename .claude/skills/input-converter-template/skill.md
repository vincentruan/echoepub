---
name: input-converter-template
description: Template for creating new input format converters. Use this as a guide when adding support for new input formats (e.g., DOCX, HTML, etc.) to the audioread pipeline.
---

# 输入转换器模板

本技能为开发新的输入格式转换器提供模板和规范指南。

## 目的

当需要支持新的输入格式（如 DOCX、HTML、RTF 等）时，按照此模板创建新的转换器技能，确保输出格式统一，便于后续处理流程。

## 标准输出格式

**所有输入转换器必须输出以下标准目录结构**：

```
$原文件名_markdown/
├── 00_目录.md                 # 目录文件
├── 01_第一章标题.md           # 章节文件（一章一个）
├── 02_第二章标题.md
├── ...
├── images/                    # 图片资源
│   ├── 01/
│   │   └── image_001.jpg
│   └── ...
└── $原文件名_report.md        # 处理报告
```

## 创建新转换器步骤

### 1. 创建技能目录

```bash
mkdir -p .claude/skills/[format]-to-markdown-converter/scripts
```

### 2. 创建 skill.md

使用以下模板：

```markdown
---
name: [format]-to-markdown-converter
description: Convert [FORMAT] files to standard Markdown format. Extracts content by chapters, separates images, and generates structured output. Use when converting [FORMAT] to Markdown for audioread processing.
---

# [FORMAT] to Markdown Converter

将 [FORMAT] 文件转换为标准 Markdown 格式，按章节拆分为多个文件。

## 输出格式

[标准输出格式说明]

## 使用方法

[命令和参数说明]

## 依赖

[依赖库列表]

## 脚本位置

[脚本路径]
```

### 3. 实现转换脚本

必须实现以下功能：

```python
def convert(input_path: str, output_dir: str = None) -> dict:
    """
    转换输入文件为标准 Markdown 格式。
    
    Args:
        input_path: 输入文件路径
        output_dir: 输出目录（默认为输入文件同级目录）
    
    Returns:
        dict: 处理报告
            {
                'input_type': str,
                'input_path': str,
                'output_path': str,
                'chapters': list,
                'total_images': int,
                'timestamp': str,
            }
    """
    pass
```

### 4. 必须实现的功能

| 功能 | 说明 |
|------|------|
| 章节拆分 | 按原文档结构拆分为多个文件 |
| 目录生成 | 生成 00_目录.md |
| 图片提取 | 提取图片到 images/ 目录 |
| 图片格式转换 | 非兼容格式转为 jpg/png |
| 图片路径规范 | 使用 `./images/XX/image_XXX.ext` 格式（XX为章节编号） |
| 处理报告 | 生成 _report.md |

### 4.1 图片路径规范

**重要**：所有图片引用必须使用相对路径，格式为 `./images/XX/image_XXX.ext`

- `./` - 当前目录相对路径前缀
- `images/` - 图片目录
- `XX/` - 章节编号（两位数，如 01, 02）
- `image_XXX.ext` - 图片文件名

**示例**：
```markdown
![架构图](./images/03/image_001.jpg)
![流程图](./images/03/image_002.png)
```

**错误示例**（不要使用）：
```markdown
![图片](../images/03/image_001.jpg)  ❌ 多了 ../
![图片](images/03/image_001.jpg)     ❌ 缺少 ./
```

### 5. 处理报告模板

```markdown
# [格式] 转换报告

## 基本信息
- 源文件：xxx
- 转换时间：2024-xx-xx
- 章节数量：N

## 章节列表
| 序号 | 章节标题 | 字数 | 图片数 |
|------|----------|------|--------|
| 01 | 第一章 | 1234 | 2 |
...

## 图片处理
- 提取图片：N 张
- 格式转换：N 张

## 备注
- 处理日志
```

## 示例：DOCX 转换器

下面是一个 DOCX 转换器的示例结构：

### 目录结构

```
.claude/skills/docx-to-markdown-converter/
├── skill.md
└── scripts/
    └── docx_converter.py
```

### skill.md

```markdown
---
name: docx-to-markdown-converter
description: Convert DOCX files to standard Markdown format.
---

# DOCX to Markdown Converter

将 DOCX 文件转换为标准 Markdown 格式。

## 依赖

pip install python-docx Pillow
```

### docx_converter.py

```python
#!/usr/bin/env python3
from docx import Document
from pathlib import Path

def convert(input_path: str, output_dir: str = None) -> dict:
    doc = Document(input_path)
    # ... 实现转换逻辑
    pass

if __name__ == "__main__":
    import sys
    convert(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
```

## 注册新转换器

创建完成后，在 CLAUDE.md 中添加新格式的说明：

```markdown
| DOCX | docx-to-markdown-converter | 转换 Word 文档 |
```

## 测试清单

- [ ] 输出目录结构正确
- [ ] 目录文件包含所有章节链接
- [ ] 章节文件编号连续
- [ ] 图片路径正确引用
- [ ] 图片格式兼容
- [ ] 处理报告完整
