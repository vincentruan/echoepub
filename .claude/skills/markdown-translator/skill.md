---
name: markdown-translator
description: Translate non-Chinese Markdown content to Simplified Chinese. Preserves technical terms, code, variable names, and markdown formatting. Only runs if document is predominantly non-Chinese. Use after content-enhancer and format-cleaner.
---

# Markdown Translator

将非中文 Markdown 内容翻译为简体中文。**条件执行：仅在文档主体为非中文时运行。**

## 核心原则

**翻译散文，保留技术内容。** 仅翻译自然语言文本，所有技术术语、代码、变量名、URL 等保持原样。

## 输入要求

标准 Markdown 目录结构，通常来自 `markdown-format-cleaner` 的输出：

```
$原文件名_markdown/
├── _cleaned/               # 输入目录
│   ├── 01_章节.md
│   ├── 02_章节.md
│   └── ...
├── images/
└── ...
```

也可直接处理 `_enhanced/` 或源目录。

## 输出

```
$原文件名_markdown/
├── _translated/            # 输出目录（新增）
│   ├── 01_章节.md       # 已翻译
│   ├── 02_章节.md       # 已翻译
│   └── *_report.md      # 处理报告
├── _cleaned/               # 不修改
├── images/                 # 不修改
└── ...
```

> 源文件始终不会被修改，所有处理结果输出到 `_translated/` 子文件夹。

---

## 语言检测

在处理前，Agent 需要先检测文档的语言构成：

1. **读取所有章节文件**
2. **统计中文字符占比**：仅统计**散文段落**中的字符，排除以下内容后再计算：
   - 代码块（``` 包裹的内容）
   - 行内代码（`` ` `` 包裹的内容）
   - URL 和文件路径
   - 引用块中的描述（`> 【图片描述】`、`> 【代码说明】`、`> 【表格说明】`）
   - 技术术语和变量名（驼峰命名、全大写缩写如 API/RPC/HTTP）

   计算公式：中文字符（`\u4e00`-`\u9fff`）占过滤后散文文本总字符数的比例
3. **根据占比决定处理方式**：

| 中文占比 | 处理方式 |
|----------|----------|
| > 70% | **跳过翻译**，直接复制文件到 `_translated/` |
| 30% - 70% | **部分翻译**，仅翻译非中文段落 |
| < 30% | **全文翻译**，翻译所有散文内容 |

> **注意**：技术类中文文档因大量英文术语（service、API、RPC 等）可能导致中文占比偏低。Agent 应结合整体判断——如果散文段落的主体语言是中文（只是夹杂英文术语），应视为中文文档，直接复制而非逐段翻译。

---

## 翻译规则

### 需要翻译的内容
- 英文/日文/其他非中文的散文段落
- 标题文字（保留 `#` 标记）
- 列表项文字（保留 `-`、`*`、数字标记）
- 引用块中的非中文文字（保留 `>` 标记）

### 不翻译的内容
- 代码块（` ``` ` 包裹的内容）
- 行内代码（`` ` `` 包裹的内容）
- 变量名、函数名、类名
- URL、文件路径
- 技术术语和缩写（如 GPU、API、LLM、HTTP、JSON、Python 等）
- 产品名/公司名（如 Google、Microsoft、OpenAI 等）
- 已有的中文内容描述（`> 【图片描述】`、`> 【代码说明】`、`> 【表格说明】`）
- Markdown 语法标记
- 数学公式（`$...$`、`$$...$$`）
- 引用标记（`[1]`、`[2,3]` 等）

### 翻译质量要求
- 保持学术/专业语气
- 翻译为简体中文
- 技术术语首次出现时可保留原文并附中文解释，如：`API（应用程序编程接口）`
- 后续出现直接使用原文术语
- 不添加任何解释、注释或评论
- 仅输出翻译后的文本

---

## 严格约束

- **不修改 Markdown 格式结构**（标题层级、列表嵌套、代码块等）
- **不修改已有的中文内容**
- **不添加任何非翻译内容**（不加注释、不加解释）
- **不合并或拆分段落**
- **保持原文的段落结构和换行**

---

## Agent 处理流程

当 Agent 使用此技能处理文件夹时：

1. **确定输入目录**：优先从 `_cleaned/` 读取，其次 `_enhanced/`，最后源目录
2. **语言检测**：
   - 读取所有章节文件
   - 统计中文字符占比
   - 如果 > 70%，直接复制文件到 `_translated/` 并跳过翻译
3. **创建输出目录**：`_translated/`
4. **逐章节翻译**：
   - 读取章节文件
   - 识别需要翻译的段落（非中文、非代码、非技术标记）
   - 逐段翻译，保留所有不需翻译的内容
   - **修正图片路径**：确保图片引用路径相对于输出子目录正确（如 `./images/` → `../images/`）
   - 写入 `_translated/` 目录
5. **生成处理报告**：记录翻译统计

---

## 处理报告格式

```markdown
## Translator 处理

- 处理时间：2026-xx-xx
- 处理章节：N 章
- 文档语言占比：中文 XX%，英文 XX%，其他 XX%
- 翻译段落：N 段
- 跳过段落：N 段（已为中文或技术内容）
- 翻译模式：全文翻译 / 部分翻译 / 跳过
```

---

## 示例

### 示例 1：全文翻译（英文文档）

**翻译前：**
```markdown
# Introduction to Microservices

Microservices architecture breaks down applications into small, independent services.
Each service runs in its own process and communicates via lightweight APIs such as REST or gRPC.

```python
@app.route('/api/orders')
def get_orders():
    return jsonify(orders)
```
```

**翻译后：**
```markdown
# 微服务简介

微服务架构将应用程序拆分为小型、独立的服务。
每个服务运行在自己的进程中，通过轻量级 API（如 REST 或 gRPC）进行通信。

```python
@app.route('/api/orders')
def get_orders():
    return jsonify(orders)
```
```

### 示例 2：跳过翻译（中文技术文档）

**输入：**
```markdown
# 系统架构设计

本系统采用 Spring Boot 框架，使用 MySQL 作为主数据库，Redis 作为缓存层。
API 网关基于 Kong 实现，支持 OAuth 2.0 认证。
```

**结果：** 中文占比 > 70%，直接复制到 `_translated/`，不做翻译。

---

## 依赖

无外部依赖。纯 Agent 驱动，Agent 自身具备高质量翻译能力，无需调用外部 API。
