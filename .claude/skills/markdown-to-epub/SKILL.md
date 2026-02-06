---
name: markdown-to-epub
description: Convert standard Markdown folder to EPUB ebook. Creates professional ebooks with cover, table of contents, chapters, and embedded images. Final step in the audioread pipeline.
---

# Markdown to EPUB Converter

将标准 Markdown 目录结构转换为专业的 EPUB 电子书，包含封面、目录、章节和嵌入图片。

## 输入格式

接受标准 Markdown 目录结构（由上游技能生成）：

```
$原文件名_markdown/
├── 00_目录.md                 # 目录文件
├── 01_章节.md                 # 章节文件
├── 02_章节.md
├── images/                    # 图片资源
│   └── ...
└── $原文件名_report.md        # 处理报告
```

## 输出

生成完整的 EPUB3 电子书：

```
$原文件名_markdown/
├── [书名].epub               # 生成的电子书
├── cover.jpg                 # 封面图片（AI生成或自动生成）
└── ...（其他文件保持不变）
```

## 使用方法

### 从标准 Markdown 目录生成 EPUB

```python
from epub_generator import create_epub_from_folder

create_epub_from_folder(
    folder_path="/path/to/book_markdown",
    title="书名",
    author="作者",
    generate_cover=True,
    cover_style="modern"
)
```

### 从单个 Markdown 文件生成 EPUB

```python
from epub_generator import create_epub_from_markdown

create_epub_from_markdown(
    markdown_content=content,
    output_path="book.epub",
    title="书名",
    author="作者",
    base_path="/path/to/images",
    generate_cover=True
)
```

## 功能特性

### 1. 封面生成

支持两种封面生成方式：

#### AI 封面（推荐）

使用 SiliconFlow API 生成专业封面：

```python
create_epub_from_folder(
    folder_path=path,
    generate_cover=True,
    cover_style="modern"  # modern, classic, minimalist, artistic
)
```

**环境变量**：`SILICONFLOW_API_KEY`

#### 程序化封面

无需 API，自动生成简洁封面：

```python
create_epub_from_folder(
    folder_path=path,
    generate_cover=True,
    use_programmatic_cover=True
)
```

### 2. 目录生成

自动从章节文件生成导航目录：

- 支持多级标题层次
- 可点击跳转
- 符合 EPUB3 标准

### 3. 图片处理

#### 图片格式转换

自动将不兼容格式转换为 EPUB 兼容格式：

| 原格式 | 转换后 | 说明 |
|--------|--------|------|
| WebP | JPEG | 透明背景转白色 |
| GIF | JPEG | 取第一帧 |
| BMP | JPEG | 直接转换 |
| PNG | PNG | 保持不变 |
| JPEG | JPEG | 保持不变 |

#### 图片嵌入

- 自动扫描 Markdown 中的图片引用
- 解析相对路径并嵌入 EPUB
- 自动调整图片尺寸适配阅读器

### 4. 文本优化（可选）

启用文本优化功能：

```python
create_epub_from_folder(
    folder_path=path,
    optimize_text=True  # 错别字纠正、格式优化
)
```

### 5. 样式定制

内置专业阅读样式：

- 大行距，适合阅读
- 清晰的标题层级
- 代码块语法高亮样式
- 表格斑马纹显示
- 引用块左边框样式

## 完整工作流示例

```python
import os
import sys

# 添加脚本路径
skill_path = os.path.expanduser('./scripts')
sys.path.insert(0, skill_path)

from epub_generator import create_epub_from_folder

# 从标准 Markdown 目录生成 EPUB
result = create_epub_from_folder(
    folder_path="/path/to/趋势与周期_markdown",
    title="趋势与周期",
    author="作者名",
    language="zh-CN",
    generate_cover=True,
    cover_style="modern",
    optimize_text=True
)

print(f"EPUB 生成成功: {result}")
```

## API 参考

### create_epub_from_folder

```python
def create_epub_from_folder(
    folder_path: str,
    title: str = None,           # 从目录文件提取
    author: str = "Unknown",
    language: str = "zh-CN",
    generate_cover: bool = True,
    cover_style: str = "modern",
    use_programmatic_cover: bool = False,
    cover_path: str = None,      # 使用已有封面
    optimize_text: bool = False,
) -> str:
    """从标准 Markdown 目录生成 EPUB"""
```

### create_epub_from_markdown

```python
def create_epub_from_markdown(
    markdown_content: str,
    output_path: str,
    title: str,
    author: str = "Unknown",
    language: str = "zh-CN",
    base_path: str = None,       # 图片基础目录
    generate_cover: bool = False,
    cover_style: str = "modern",
    cover_path: str = None,
) -> str:
    """从 Markdown 内容生成 EPUB"""
```

## 依赖

```bash
pip install ebooklib Pillow
```

可选（AI 封面生成）：
```bash
pip install requests
```

## 脚本列表

| 脚本 | 功能 |
|------|------|
| `epub_generator.py` | EPUB 文件生成核心 |
| `markdown_processor.py` | Markdown 解析和 HTML 转换 |
| `cover_generator.py` | AI 封面生成 |
| `programmatic_cover.py` | 程序化封面生成 |
| `convert_images.py` | 图片格式转换 |

## 错误处理

| 错误 | 解决方案 |
|------|----------|
| 图片嵌入失败 | 检查图片路径是否正确，确保 base_path 设置正确 |
| 封面生成失败 | 检查 API Key，或使用程序化封面 |
| EPUB 打开失败 | 检查 Markdown 格式，确保标题层级正确 |

## 输出结构

生成的 EPUB 包含：

```
[书名].epub/
├── mimetype
├── META-INF/
│   └── container.xml
├── OEBPS/
│   ├── content.opf          # 元数据清单
│   ├── toc.ncx              # 导航文件
│   ├── nav.xhtml            # EPUB3 导航
│   ├── styles/
│   │   └── style.css        # 样式表
│   ├── images/
│   │   ├── cover.jpg        # 封面
│   │   └── ...              # 内容图片
│   └── text/
│       ├── cover.xhtml      # 封面页
│       ├── toc.xhtml        # 目录页
│       ├── ch01.xhtml       # 章节内容
│       └── ...
```
