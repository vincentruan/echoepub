---
name: markdown-converter
description: Convert Markdown files or folders to standard multi-file format. Splits content by H1 headers into separate chapter files with a table of contents. Use when preparing Markdown content for audioread processing.
---

# Markdown Converter

将 Markdown 文件或文件夹转换为标准多文件格式，便于后续处理。

## 输出格式

转换后生成以下标准目录结构：

```
$原文件名_markdown/
├── 00_目录.md                 # 目录文件，包含章节链接
├── 01_第一章标题.md           # 章节文件（一章一个）
├── 02_第二章标题.md
├── ...
├── images/                    # 图片资源（如有）
│   ├── 01/
│   │   └── image_001.jpg
│   └── ...
└── $原文件名_report.md        # 处理报告
```

## 输入支持

| 输入类型 | 处理方式 |
|----------|----------|
| 单个 Markdown 文件 | 按 H1 标题拆分为多个章节文件 |
| 文件夹（多个 Markdown） | 合并整理为标准目录结构 |
| 含 SUMMARY.md 的文件夹 | 按 SUMMARY.md 定义的顺序组织 |
| 含 README.md 的文件夹 | 将 README.md 作为首章处理 |

## 使用方法

### 转换单个文件

```bash
python ./scripts/markdown_splitter.py "<input.md>" [output-dir]
```

### 转换文件夹

```bash
python ./scripts/markdown_splitter.py "<input-folder>" [output-dir]
```

**参数说明**：
- `input`: Markdown 文件路径或文件夹路径
- `output-dir`: 可选，输出目录，默认为输入文件同级目录

## 章节拆分规则

### 单文件模式

1. **按 H1 标题拆分**：每个 `# 标题` 开始一个新章节
2. **无 H1 时按 H2 拆分**：如果文件没有 H1，则按 `## 标题` 拆分
3. **前言处理**：第一个标题之前的内容作为前言（00_前言.md）

### 文件夹模式

1. **索引文件优先**：
   - `SUMMARY.md` - 作为目录定义，按其顺序组织章节
   - `README.md` / `index.md` - 作为首章或前言
   - `toc.md` / `目录.md` - 作为目录定义

2. **自然排序**：
   - 数字前缀文件：`01_xxx.md`, `02_xxx.md` 按序号排序
   - 无前缀文件：按文件名字母顺序排序

3. **子目录处理**：
   - 递归处理子目录
   - 子目录名作为章节组名称

4. **过滤规则**：
   - 忽略 `node_modules/`, `.git/`, `build/`, `dist/` 等目录
   - 忽略隐藏文件（以 `.` 开头）

## 图片处理

1. **路径规范化**：将图片路径统一为相对路径
2. **图片复制**：复制图片到 `images/章节序号/` 目录
3. **格式转换**：webp/gif/bmp → jpg（使用 Pillow）

## 处理报告

生成 `$原文件名_report.md`，包含：

```markdown
# Markdown 转换报告

## 基本信息
- 输入类型：单文件/文件夹
- 输入路径：xxx
- 转换时间：2024-xx-xx
- 章节数量：N

## 章节列表
| 序号 | 章节标题 | 源文件 | 字数 |
|------|----------|--------|------|
| 01 | 第一章 | input.md | 1234 |
...

## 图片处理
- 处理图片：N 张
- 格式转换：N 张

## 备注
- 处理日志
```

## 示例

### 单文件转换

```bash
# 输入
book.md (含多个 H1 标题)

# 输出
book_markdown/
├── 00_目录.md
├── 01_引言.md
├── 02_第一章.md
├── 03_第二章.md
└── book_report.md
```

### 文件夹转换

```bash
# 输入
my-docs/
├── SUMMARY.md
├── intro.md
├── chapter1.md
└── chapter2.md

# 输出
my-docs_markdown/
├── 00_目录.md
├── 01_intro.md
├── 02_chapter1.md
├── 03_chapter2.md
└── my-docs_report.md
```

## 依赖

```bash
pip install Pillow  # 可选，用于图片格式转换
```

## 脚本位置

- 主脚本：`scripts/markdown_splitter.py`
