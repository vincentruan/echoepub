---
name: epub-to-markdown-converter
description: Convert EPUB ebook files to standard Markdown format. Extracts content by chapters, separates images, and generates a structured output with a table of contents file and individual chapter files. Use when converting EPUB to Markdown for further processing.
---

# EPUB to Markdown Converter

将 EPUB 电子书转换为标准 Markdown 格式，按章节拆分为多个文件，便于后续处理。

## 输出格式

转换后生成以下标准目录结构：

```
$原文件名_markdown/
├── 00_目录.md                 # 目录文件，包含章节链接
├── 01_第一章标题.md           # 章节文件（一章一个）
├── 02_第二章标题.md
├── ...
├── images/                    # 图片资源
│   ├── 01/
│   │   └── image_001.jpg
│   └── ...
└── $原文件名_report.md        # 处理报告
```

## 使用方法

### 1. 查看元数据

获取书籍信息（标题、作者、出版社等）：

```bash
node ./scripts/epub-reader/dist/index.js metadata "<path-to-epub>"
```

### 2. 查看目录

查看所有章节及其结构，每个条目显示 `[ch: N]` 表示章节编号：

```bash
node ./scripts/epub-reader/dist/index.js toc "<path-to-epub>"
```

### 3. 读取特定章节

按编号读取单个章节（1-indexed）：

```bash
node ./scripts/epub-reader/dist/index.js chapter "<path-to-epub>" <chapter-number>
```

### 4. 读取完整书籍

提取完整书籍内容：

```bash
node ./scripts/epub-reader/dist/index.js full "<path-to-epub>"
```

### 5. 搜索文本

查找文本出现位置及上下文：

```bash
node ./scripts/epub-reader/dist/index.js search "<path-to-epub>" "<search-query>"
```

### 6. 转换为标准 Markdown 格式（推荐）

将 EPUB 完整转换为标准多文件 Markdown 格式：

```bash
node ./scripts/epub-reader/dist/index.js convert "<path-to-epub>" [output-dir]
```

**参数说明**：
- `path-to-epub`: EPUB 文件路径
- `output-dir`: 可选，输出目录，默认为 EPUB 文件同级目录

## 推荐工作流

1. **查看元数据** 了解书籍基本信息
2. **查看目录** 了解章节结构和数量
3. **使用 convert 命令** 转换为标准 Markdown 格式
4. 后续可使用 `markdown-to-audioread` 进行内容优化

## 输出说明

### 目录文件格式 (00_目录.md)

```markdown
# 书籍标题

> 作者：作者名称

## 目录

1. [第一章标题](./01_第一章标题.md)
2. [第二章标题](./02_第二章标题.md)
...
```

### 章节文件格式 (01_第一章标题.md)

```markdown
# 第一章标题

章节正文内容...

![图片描述](./images/01/image_001.jpg)

更多内容...
```

### 处理报告格式 ($原文件名_report.md)

```markdown
# EPUB 转换报告

## 基本信息
- 源文件：xxx.epub
- 转换时间：2024-xx-xx
- 章节数量：N

## 章节列表
| 序号 | 章节标题 | 字数 | 图片数 |
|------|----------|------|--------|
| 01 | 第一章 | 1234 | 2 |
...

## 图片处理
- 提取图片：N 张
- 格式转换：N 张 (webp/gif → jpg)

## 备注
- 处理成功/失败信息
```

## 注意事项

- 章节编号从 1 开始
- 路径包含空格时需要加引号
- 大型书籍使用 `full` 命令可能产生大量输出
- 搜索结果每章最多显示 5 个匹配项
- 图片会自动转换为 EPUB 兼容格式（jpg/png）

## 开放式搜索

对于概念性查询如"这本书的主题是什么"，使用**查询扩展**：

1. 将查询扩展为多个具体搜索词
2. 并行运行多个搜索
3. 综合和去重结果

## 脚本位置

- CLI 工具：`scripts/epub-reader/dist/index.js`
- 转换逻辑：`scripts/epub-reader/src/`
