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

支持三种封面生成方式：

#### 混合封面（推荐）

AI 生成主题插画 + 程序化渲染中英文文字，完美支持中文：

```python
from cover_generator import generate_hybrid_cover

success, result = generate_hybrid_cover(
    title="架构师之路",
    author="沈剑",
    subtitle="从程序员到架构师",
    output_path="cover.jpg",
    style="modern"
)
```

**特点**：
- AI 生成铺满封面的主题插画（根据书名和内容智能匹配）
- 中文/英文字体完美渲染（使用系统字体）
- 标准布局：标题在上，插画居中，作者在下

**环境变量**：`SILICONFLOW_API_KEY`

#### AI 插画封面

仅生成 AI 插画背景，不含文字：

```python
from cover_generator import generate_cover_from_markdown

success, result = generate_cover_from_markdown(
    title="书名",
    author="作者",
    output_path="cover.jpg",
    style="modern"
)
```

#### 程序化封面

无需 API，自动生成简洁封面（支持中文）：

```python
from programmatic_cover import generate_programmatic_cover

success, result = generate_programmatic_cover(
    title="书名",
    author="作者",
    output_path="cover.jpg",
    style="modern"
)
```

### 封面风格

| 风格 | 特点 | 适用场景 |
|------|------|----------|
| `modern` | 现代简约，冷色调 | 技术类、商业类 |
| `classic` | 经典优雅，暖色调 | 文学类、历史类 |
| `minimalist` | 极简留白 | 哲学类、思想类 |
| `artistic` | 艺术创意 | 设计类、艺术类 |

### 主题识别

混合封面会根据书名和章节自动识别主题，生成匹配的插画：

| 主题关键词 | 插画元素 |
|------------|----------|
| 架构、系统、微服务 | 软件架构图、服务器、网络拓扑 |
| 编程、代码、算法 | 代码流、二进制模式、编程符号 |
| AI、机器学习 | 神经网络、机器人、数字大脑 |
| 商业、管理、创业 | 商业图表、城市天际线、齿轮协作 |
| 金融、经济、投资 | 金色流线、货币符号、财富增长 |
| 哲学、思维、认知 | 抽象思维泡泡、禅意图案、光与智慧 |
| 历史、朝代、古代 | 古卷、历史长河、古典建筑 |

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
| `cover_generator.py` | AI 封面生成 + 混合封面（推荐） |
| `programmatic_cover.py` | 程序化封面生成（支持中文） |
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
