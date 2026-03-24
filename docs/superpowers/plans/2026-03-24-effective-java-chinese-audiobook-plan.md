# Effective Java 中文收听优化转换实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将 `Effective_Java_Raw.epub` 转换为中文版 EPUB，优化语音收听体验，并通过验证收集 Skill 优化建议。

**Architecture:** 采用手动编排方式执行现有 Skills 流程，在关键节点进行验证，最终生成全量验证报告。本次执行将发现的问题记录为后续 Skill 迭代的输入。

**Tech Stack:** Python 3.x, Node.js, ebooklib, Pillow, OpenAI-compatible VLM API

---

## 文件结构

```
books/
├── Effective_Java_Raw.epub                    # 输入文件
├── Effective_Java_Raw_markdown/               # 步骤1输出：Markdown目录
│   ├── 00_目录.md
│   ├── 01_*.md ... 90_*.md                    # 章节文件
│   ├── images/                                # 提取的图片
│   └── Effective_Java_Raw_report.md           # 转换报告
├── original_cover.jpg                          # 步骤2输出：原封面
├── Effective_Java_Raw_enhanced/                # 步骤3-4输出：增强后Markdown
│   └── _enhanced/
├── Effective_Java_Raw_translated/              # 步骤6输出：翻译后Markdown
│   └── _translated/
├── Effective_Java_Chinese_Final.epub           # 步骤7输出：最终EPUB
└── Effective_Java_Verification_Report.md       # 步骤8输出：验证报告
```

---

## Task 1: 环境准备与元数据提取

**Files:**
- Input: `books/Effective_Java_Raw.epub`
- Output: 元数据信息（控制台输出）

- [ ] **Step 1: 检查环境变量**

```bash
echo "检查环境变量..."
echo "ECHO_EPUB_OPEN_API_KEY: ${ECHO_EPUB_OPEN_API_KEY:0:10}..."
echo "ECHO_EPUB_OPEN_AI_BASE_URL: $ECHO_EPUB_OPEN_AI_BASE_URL"
echo "ECHO_EPUB_VLM_MODEL: $ECHO_EPUB_VLM_MODEL"
```

Expected: 环境变量已设置，API Key 不为空

- [ ] **Step 2: 检查依赖**

```bash
python3 -c "import ebooklib; import PIL; import requests; print('依赖检查通过')"
node --version
```

Expected: 依赖检查通过，Node.js 版本 >= 14

- [ ] **Step 3: 提取 EPUB 元数据**

```bash
cd /Users/vincentruan/geek_space/github/echoepub
node .claude/skills/epub-to-markdown-converter/scripts/epub-reader/dist/index.js metadata "books/Effective_Java_Raw.epub"
```

Expected: 输出书名、作者、出版社等元数据信息

- [ ] **Step 4: 查看 EPUB 目录结构**

```bash
node .claude/skills/epub-to-markdown-converter/scripts/epub-reader/dist/index.js toc "books/Effective_Java_Raw.epub"
```

Expected: 输出所有章节列表，记录章节数量

- [ ] **Step 5: 记录元数据**

将以下信息记录到 `books/Effective_Java_Raw_report.md`:
- 书名
- 作者
- 章节数量
- 预计图片数量（从目录推断）

---

## Task 2: EPUB 转 Markdown

**Files:**
- Input: `books/Effective_Java_Raw.epub`
- Output: `books/Effective_Java_Raw_markdown/`

- [ ] **Step 1: 执行转换**

```bash
cd /Users/vincentruan/geek_space/github/echoepub
node .claude/skills/epub-to-markdown-converter/scripts/epub-reader/dist/index.js convert "books/Effective_Java_Raw.epub" "books/"
```

Expected: 生成 `Effective_Java_Raw_markdown/` 目录，包含章节文件和图片

- [ ] **Step 2: 验证转换结果**

```bash
ls -la books/Effective_Java_Raw_markdown/
echo "---"
ls books/Effective_Java_Raw_markdown/*.md | wc -l
echo "---"
ls books/Effective_Java_Raw_markdown/images/ | head -20
```

Expected: 章节文件数量与元数据一致，images 目录存在

- [ ] **Step 3: 抽样验证章节内容**

随机抽取 3-5 个章节文件，检查:
- 内容提取是否完整
- 图片引用是否正确
- 代码块是否被保留

- [ ] **Step 4: 提交中间结果**

```bash
git add books/Effective_Java_Raw_markdown/
git commit -m "feat: Convert Effective_Java_Raw.epub to Markdown

- Extract N chapters
- Extract M images
- Generated conversion report

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## Task 3: 封面提取

**Files:**
- Input: `books/Effective_Java_Raw.epub`
- Output: `books/original_cover.jpg`

- [ ] **Step 1: 提取封面图片**

使用 Python 从 EPUB 中提取封面:

```python
import zipfile
from pathlib import Path

epub_path = "books/Effective_Java_Raw.epub"
output_path = "books/original_cover.jpg"

with zipfile.ZipFile(epub_path, 'r') as z:
    # 查找封面图片
    for name in z.namelist():
        if 'cover' in name.lower() and any(name.lower().endswith(ext) for ext in ['.jpg', '.jpeg', '.png']):
            print(f"Found cover: {name}")
            with open(output_path, 'wb') as f:
                f.write(z.read(name))
            print(f"Cover saved to: {output_path}")
            break
    else:
        # 尝试从 OPF 文件中查找
        for name in z.namelist():
            if name.endswith('.opf'):
                print(f"OPF file: {name}")
                print(z.read(name).decode('utf-8')[:2000])
```

Expected: 封面图片提取成功并保存

- [ ] **Step 2: 验证封面**

```bash
ls -la books/original_cover.jpg
file books/original_cover.jpg
```

Expected: 文件存在且为有效图片格式

- [ ] **Step 3: 确认使用原封面**

询问用户: "检测到原书封面，是否使用原封面？[Y/n]"

记录用户选择（预期: Y）

---

## Task 4: 图片智能分类与处理

**Files:**
- Input: `books/Effective_Java_Raw_markdown/`
- Output: `books/Effective_Java_Raw_markdown/_enhanced/`

- [ ] **Step 1: 统计图片数量**

```bash
find books/Effective_Java_Raw_markdown/images -type f \( -name "*.jpg" -o -name "*.png" -o -name "*.gif" -o -name "*.webp" \) | wc -l
```

Expected: 输出图片总数

- [ ] **Step 2: 执行图片描述脚本（含智能 OCR）**

```bash
cd books/Effective_Java_Raw_markdown

# 批量处理所有章节
for chapter in *.md; do
    if [ "$chapter" != "00_目录.md" ] && [ "$chapter" != "*_report.md" ]; then
        echo "Processing: $chapter"
        python ../../.claude/skills/markdown-content-enhancer/scripts/image_descriptor.py "$chapter" "./images"
    fi
done
```

Expected: 每个章节生成 `*_with_descriptions.md` 文件

- [ ] **Step 3: 创建 _enhanced 目录并整理输出**

```bash
cd books/Effective_Java_Raw_markdown
mkdir -p _enhanced

for file in *_with_descriptions.md; do
    # 转换注释为引用块，修正图片路径
    name="${file/_with_descriptions.md/.md}"
    python -c "
import re
with open('$file') as f:
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

with open('_enhanced/$name', 'w') as f:
    f.write(content)
"
done
```

- [ ] **Step 4: 抽样验证 OCR 效果**

随机抽取 5 张被 OCR 的代码截图，对比:
- 原图片内容
- 提取的代码块
- 生成的代码说明

记录 OCR 准确率和问题

- [ ] **Step 5: 记录图片处理统计**

将以下信息添加到报告:
- 总图片数
- OCR 处理数（代码/表格截图）
- 描述生成数（架构图等）
- 跳过数（装饰性图片）

---

## Task 5: 内容增强（代码块/表格描述）

**Files:**
- Input: `books/Effective_Java_Raw_markdown/_enhanced/`
- Output: `books/Effective_Java_Raw_markdown/_enhanced/` (更新)

**说明:** 此任务由 Agent 执行，为代码块和表格添加描述。

- [ ] **Step 1: 统计待处理内容**

```bash
cd books/Effective_Java_Raw_markdown/_enhanced
echo "代码块数量:"
grep -c '```' *.md | awk -F: '{sum+=$2} END {print sum/2}'

echo "表格数量:"
grep -c '|.*|' *.md | awk -F: '{sum+=$2} END {print sum}'
```

- [ ] **Step 2: Agent 执行内容增强**

使用 `markdown-content-enhancer` skill，Agent 逐章节:
1. 识别代码块（已包裹和未包裹）
2. 为代码块添加 `> 【代码说明】...` 引用块
3. 识别表格
4. 为表格添加 `> 【表格说明】...` 引用块

- [ ] **Step 3: 验证增强结果**

抽样 3 章，检查:
- 代码说明是否准确
- 表格说明是否完整
- 是否有遗漏

---

## Task 6: 格式清理

**Files:**
- Input: `books/Effective_Java_Raw_markdown/_enhanced/`
- Output: `books/Effective_Java_Raw_markdown/_cleaned/`

- [ ] **Step 1: 执行格式清理**

Agent 使用 `markdown-format-cleaner` skill 处理:
- 空行规范化
- 列表缩进统一
- 代码块修复
- 标题格式规范
- 图片路径修正

- [ ] **Step 2: 验证清理结果**

```bash
ls books/Effective_Java_Raw_markdown/_cleaned/
```

Expected: `_cleaned/` 目录包含所有章节文件

---

## Task 7: 翻译（英文 → 中文）

**Files:**
- Input: `books/Effective_Java_Raw_markdown/_cleaned/`
- Output: `books/Effective_Java_Raw_markdown/_translated/`

- [ ] **Step 1: 检测文档语言**

Agent 读取样本章节，统计中文占比:
- 如果 > 70% 中文 → 跳过翻译
- 如果 < 30% 中文 → 全文翻译

Expected: 英文文档，需要全文翻译

- [ ] **Step 2: 执行翻译**

Agent 使用 `markdown-translator` skill 逐章节翻译:
- 保留代码块不翻译
- 保留技术术语（Item XX:）
- 翻译散文段落

- [ ] **Step 3: 抽样验证翻译质量**

随机抽取 2-3 章，检查:
- 翻译是否流畅
- 技术术语是否保留
- 是否有漏译

---

## Task 8: 生成 EPUB

**Files:**
- Input: `books/Effective_Java_Raw_markdown/_translated/`
- Input: `books/original_cover.jpg`
- Output: `books/Effective_Java_Chinese_Final.epub`

- [ ] **Step 1: 合并章节为单个 Markdown**

```python
from pathlib import Path

translated_dir = Path("books/Effective_Java_Raw_markdown/_translated")
chapters = sorted(translated_dir.glob("*.md"))

# 排除目录和报告文件
chapters = [c for c in chapters if not c.name.startswith("00_") and not c.name.endswith("_report.md")]

content_parts = []
for ch in chapters:
    with open(ch, encoding='utf-8') as f:
        content_parts.append(f.read())

final_content = "\n\n---\n\n".join(content_parts)

with open("books/Effective_Java_Chinese_Final.md", 'w', encoding='utf-8') as f:
    f.write(final_content)

print(f"Merged {len(chapters)} chapters")
```

- [ ] **Step 2: 生成 EPUB（使用原封面）**

```python
import sys
sys.path.insert(0, '.claude/skills/markdown-to-epub/scripts')

from epub_generator import create_epub_from_markdown

with open("books/Effective_Java_Chinese_Final.md", encoding='utf-8') as f:
    content = f.read()

create_epub_from_markdown(
    markdown_content=content,
    output_path="books/Effective_Java_Chinese_Final.epub",
    title="Effective Java 中文版",
    author="Joshua Bloch",
    base_path="books/Effective_Java_Raw_markdown/_translated",
    cover_path="books/original_cover.jpg",  # 使用原封面
    generate_cover=False
)

print("EPUB generated: books/Effective_Java_Chinese_Final.epub")
```

Expected: EPUB 文件生成成功

- [ ] **Step 3: 验证 EPUB 文件**

```bash
ls -la books/Effective_Java_Chinese_Final.epub
file books/Effective_Java_Chinese_Final.epub
```

Expected: 文件大小合理（> 10MB），文件类型为 EPUB

- [ ] **Step 4: 提交最终结果**

```bash
git add books/Effective_Java_Chinese_Final.epub books/original_cover.jpg
git commit -m "feat: Generate Chinese version of Effective Java EPUB

- Used original cover
- OCR processed code screenshots
- Translated to Chinese
- Optimized for audio listening

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## Task 9: 全量验证与反思

**Files:**
- Input: `books/Effective_Java_Raw.epub`
- Input: `books/Effective_Java_Chinese_Final.epub`
- Output: `books/Effective_Java_Verification_Report.md`

- [ ] **Step 1: 结构完整性验证**

```python
# 验证章节数量
import subprocess

# 原版章节
orig_toc = subprocess.run(
    ["node", ".claude/skills/epub-to-markdown-converter/scripts/epub-reader/dist/index.js", "toc", "books/Effective_Java_Raw.epub"],
    capture_output=True, text=True
)

# 新版章节
new_toc = subprocess.run(
    ["node", ".claude/skills/epub-to-markdown-converter/scripts/epub-reader/dist/index.js", "toc", "books/Effective_Java_Chinese_Final.epub"],
    capture_output=True, text=True
)

print("原版章节数:", orig_toc.stdout.count("[ch:"))
print("新版章节数:", new_toc.stdout.count("[ch:"))
```

- [ ] **Step 2: 逐章内容比对**

对每个章节执行:
1. 提取原 EPUB 章节文本
2. 提取新 EPUB 章节文本
3. 比对段落结构
4. 比对图片引用
5. 记录差异

- [ ] **Step 3: 特殊处理验证**

1. **封面验证**: 确认使用了原封面
2. **OCR 代码验证**: 全量检查代码块语法
3. **翻译验证**: 抽查技术术语保留情况

- [ ] **Step 4: 生成验证报告**

```markdown
# Effective Java 中文版验证报告

## 验证时间
2026-03-24

## 结构完整性
| 指标 | 原版 | 新版 | 状态 |
|------|------|------|------|
| 章节数 | XX | XX | ✅/❌ |
| 图片数 | XX | XX | ✅/❌ |
| 目录层级 | N | N | ✅/❌ |

## 图片处理统计
| 类型 | 数量 | 处理方式 | 成功率 |
|------|------|----------|--------|
| 代码截图 | XX | OCR | XX% |
| 表格截图 | XX | OCR | XX% |
| 架构图 | XX | 描述 | 100% |
| 装饰图 | XX | 跳过 | - |

## OCR 准确性
- 抽样数量: 10
- 准确数量: X
- 准确率: XX%
- 问题案例:
  1. [描述问题]

## 翻译质量
- 抽样章节: X
- 技术术语保留: ✅/❌
- 问题案例:
  1. [描述问题]

## 异常问题列表
1. [问题描述]
2. [问题描述]

## Skill 优化建议
### 优先级 P0
1. [建议内容]

### 优先级 P1
1. [建议内容]

### 优先级 P2
1. [建议内容]
```

- [ ] **Step 5: 提交验证报告**

```bash
git add books/Effective_Java_Verification_Report.md
git commit -m "docs: Add verification report for Effective Java Chinese version

- Structure integrity verification
- OCR accuracy statistics
- Translation quality check
- Skill optimization suggestions

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## 成功标准

- [ ] 中文版 EPUB 生成成功
- [ ] 原封面正确复用
- [ ] 代码截图 OCR 准确率 > 90%
- [ ] 目录结构与原版一致
- [ ] 全量验证报告生成
- [ ] Skill 优化建议列表完成

---

## 回滚计划

如果任何步骤失败:
1. 检查错误日志
2. 修复问题后重试
3. 如无法修复，回退到上一个成功的步骤
4. 记录问题到 Skill 优化建议