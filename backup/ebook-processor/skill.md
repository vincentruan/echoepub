---
name: ebook-processor
description: 电子书后处理工具。对已创建的电子书 markdown 文件夹进行图片优化、错别字纠正、文本格式优化，并生成 EPUB 电子书。作为 zhihu-extractor skill 的后处理补充。
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, Task, TodoWrite
---

# 电子书后处理器

对已初步创建的电子书 markdown 文件夹进行深度优化处理，包括图片格式转换、结构化图片内容提取、错别字纠正、文本格式优化，最终生成高质量 EPUB 电子书。

## 使用前提

1. 电子书文件夹已存在（可由 `zhihu-extractor` skill 创建或手工创建）
2. Python 环境已安装 Pillow 库（用于图片格式转换）
3. 文件夹内包含按章节命名的 markdown 文件

## 输入参数

- **电子书名称**：项目内的文件夹名称（即电子书目录名）

## 工作流程

### 第一步：扫描电子书目录

1. 验证电子书目录是否存在
2. 扫描所有 markdown 文件，按章节序号排序
3. 统计总章节数、图片数量、预估处理时间
4. 创建处理任务列表

```python
# 扫描示例
import os
import glob
import re

def scan_ebook_folder(folder_path):
    """扫描电子书文件夹"""
    md_files = glob.glob(os.path.join(folder_path, '*.md'))
    # 过滤出章节文件（格式：数字_标题.md）
    chapter_files = [f for f in md_files if re.match(r'^\d+_', os.path.basename(f))]
    chapter_files.sort(key=lambda f: int(re.match(r'^(\d+)_', os.path.basename(f)).group(1)))
    return chapter_files
```

### 第二步：图片处理

对每个章节的图片进行处理：

#### 2.1 扫描图片引用

在 markdown 文件中查找所有图片引用：
- `![alt](path)` 格式
- `<img src="path">` 格式
- 图片占位符 `<!-- 图片暂未加载 -->`

#### 2.2 图片格式转换

**重要**：使用 Python 脚本进行图片格式转换

```python
# 使用 .claude/skills/ebook-processor/scripts/convert_images.py
from PIL import Image
import os

def convert_image(input_path, output_dir, chapter_name):
    """
    转换图片格式
    - webp/gif/bmp 等格式转换为 jpg
    - 原始 jpg/png 格式保持不变
    - 备份原文件到 bak/ 目录
    """
    filename = os.path.basename(input_path)
    name, ext = os.path.splitext(filename)
    ext = ext.lower()

    # 创建目录结构
    chapter_dir = os.path.join(output_dir, 'images', chapter_name)
    bak_dir = os.path.join(chapter_dir, 'bak')
    os.makedirs(chapter_dir, exist_ok=True)
    os.makedirs(bak_dir, exist_ok=True)

    # 判断是否需要转换
    if ext in ['.jpg', '.jpeg', '.png']:
        # 直接移动，无需转换
        output_path = os.path.join(chapter_dir, filename)
        shutil.move(input_path, output_path)
        return output_path
    else:
        # 需要转换格式
        # 1. 备份原文件
        bak_path = os.path.join(bak_dir, filename)
        shutil.copy2(input_path, bak_path)

        # 2. 转换为 jpg
        output_filename = f"{name}.jpg"
        output_path = os.path.join(chapter_dir, output_filename)

        with Image.open(input_path) as img:
            # 处理透明通道
            if img.mode in ('RGBA', 'LA', 'P'):
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                img = background
            elif img.mode != 'RGB':
                img = img.convert('RGB')

            img.save(output_path, 'JPEG', quality=90)

        # 3. 删除原文件
        os.remove(input_path)

        return output_path
```

#### 2.3 结构化图片内容识别（激进策略）

**核心原则**：默认对所有图片进行内容识别和文本描述，仅跳过明确无信息价值的图片。这确保在语音播报场景下，听众不会错过任何图片中的重要信息。

##### 不需要解析的图片类型（黑名单）

只有以下类型的图片**直接跳过**，不进行文本转换：

| 类型 | 特征 | 示例 |
|------|------|------|
| **表情包/梗图** | 卡通表情、网络流行梗图 | emoji、搞笑表情包 |
| **纯人物照片** | 单纯的人物肖像，无文字信息 | 作者头像、人物特写 |
| **纯装饰图案** | 背景花纹、分隔线、无内容的装饰 | 渐变背景、抽象图案 |
| **模糊/无法识别** | 严重模糊或损坏的图片 | 加载失败的占位图 |
| **内容完全重复** | 图片信息已在正文中逐字描述 | 纯文字截图且文字已在正文 |

##### 需要解析的图片类型（默认处理）

除黑名单外，以下所有类型都应进行文本转换：

| 类型 | 处理方式 |
| ------ | ---------- |
| **数据表格/图表** | 提取所有数据和趋势 |
| **流程图/架构图** | 描述步骤和逻辑关系 |
| **公式/方程** | 转写为文本公式 |
| **截图类** | 描述截图中的关键信息、界面元素、数据 |
| **思维导图/层级图** | 转换为层级文本结构 |
| **时间线/对比图** | 按顺序或对比维度描述 |
| **带文字的图片** | 提取所有可见文字 |
| **场景/情境图** | 简要描述与上下文相关的要素 |
| **新闻图片/事件图** | 描述图片中的关键信息 |
| **有数据的界面截图** | 提取界面中显示的数据和状态 |
| **任何含信息的图片** | 只要包含可能对理解有帮助的信息都处理 |

##### 判断流程

```
1. 快速扫描图片内容
2. 判断是否属于"黑名单"类型
   - 是 → 跳过（表情包、纯装饰、纯人物照等）
   - 否 → 继续处理
3. 分析图片内容，生成文本描述
4. 检查是否与正文内容完全重复
   - 完全重复 → 跳过
   - 有补充信息 → 保留描述
```

##### 文本说明格式

```markdown
![原图描述](./images/chapter_name/image.jpg)

> **图片说明**：[描述图片中的关键信息]
```

##### 示例

**应该解析的图片**：

示例1 - 数据图表：
```markdown
![GDP增长趋势图](./images/01_经济分析/gdp_chart.jpg)

> **图片说明**：该图展示2020-2024年GDP增长率变化：
> - 2020年：2.3%
> - 2021年：8.1%
> - 2022年：3.0%
> - 2023年：5.2%
```

示例2 - 截图（包含有用信息）：
```markdown
![交易软件界面截图](./images/02_投资分析/trading_screen.jpg)

> **图片说明**：截图显示某股票交易界面，当日涨幅 3.5%，成交量 1.2亿，主力资金净流入 500万。
```

示例3 - 场景图（与上下文相关）：
```markdown
![1929年华尔街](./images/03_金融史/wall_street_1929.jpg)

> **图片说明**：1929年股市崩盘期间华尔街人群聚集的历史照片，可见大量投资者在交易所外焦急等待。
```

**不应该解析的图片**（直接跳过）：
```markdown
![](./images/01_经济分析/emoji_thinking.jpg)

<!-- 表情包，跳过 -->
```

##### 处理逻辑

```python
def should_skip_image(image_path, context):
    """
    判断图片是否应该跳过（黑名单检查）
    返回: bool

    决策原则：宁可多描述，不可遗漏重要信息
    """
    # 使用 AI 判断图片类型
    # 只有明确属于黑名单类型才返回 True
    # 黑名单：表情包、纯装饰、纯人物照片、模糊图片
    pass

def process_image(image_path, markdown_content, context):
    """
    处理图片内容识别（激进策略）
    1. 检查是否属于黑名单 → 跳过
    2. 分析图片内容，结合上下文理解意图
    3. 生成详细的文本描述
    4. 仅当描述与正文完全重复时才省略
    """
    if should_skip_image(image_path, context):
        return None  # 黑名单图片，跳过

    # 生成描述
    # 包含：图片类型、关键数据、与上下文的关联
    # 返回: { "description": str }
    pass
```

##### 激进策略的优势

1. **信息完整性**：确保语音播报时不遗漏任何可能重要的视觉信息
2. **上下文关联**：即使是普通场景图，也可能包含与文章主题相关的背景信息
3. **数据保全**：截图、界面等常被忽略，但往往包含关键数据
4. **降低遗漏风险**：宁可多解释，也不错过重要内容

#### 2.4 更新 Markdown 图片路径

将所有图片引用更新为新路径：

```markdown
# 原始
![图片](./old_path/image.webp)

# 更新后
![图片](./images/01_第一章/image.jpg)
```

### 第三步：文本纠错与优化

**重要**：为避免 token 超限，使用 subagent 逐个文件处理

#### 3.1 启动 Subagent 处理

对每个章节文件启动独立的 subagent：

```
使用 Task tool 启动 subagent，提示如下：

---
任务：优化电子书章节文本

文件路径：{chapter_file_path}
章节名称：{chapter_name}

请完成以下任务：

1. **错别字纠正**
   - 识别并纠正作者的错别字
   - 识别并纠正 OCR 产生的错别字
   - 常见错别字示例：
     - "的地得"混用
     - 形近字错误（如"已"和"己"）
     - 同音字错误
   - 记录所有纠正项

2. **OCR 排版修复**（重要）
   OCR 或网页抓取常产生以下排版问题，需要修复：

   a) **异常换行修复**
      - 句子中间的莫名换行（如"这是一个很长的句\n子"）→ 合并为完整句子
      - 段落内不应有的空行 → 删除多余空行
      - 判断依据：如果换行处没有句号/问号/感叹号等结束标点，通常是异常换行

   b) **段落识别与修复**
      - 真正的段落应该用空行分隔
      - 连续的短句如果语义连贯，应合并为段落
      - 列表项保持原有换行

   c) **空格问题**
      - 中文之间不应有空格
      - 中英文之间可保留一个空格
      - 删除行首/行尾多余空格
      - 删除连续多个空格

   d) **特殊字符清理**
      - 删除不可见的控制字符
      - 修复乱码（如果可识别）
      - 全角/半角标点统一

3. **文本格式优化**
   - 对关键概念、重要结论使用 **加粗** 标记
   - 对专业术语在首次出现时加粗
   - 对数字、百分比等关键数据加粗
   - 确保标点符号使用正确（中英文标点一致）
   - 优化段落分隔，确保阅读流畅

4. **格式规范**
   - 确保标题层级正确（# ## ###）
   - 列表格式统一
   - 引用格式规范
   - 代码块正确标记

5. **忠于原文原则**
   - 不改变原文含义
   - 不添加原文没有的内容
   - 不删除原文的核心内容
   - 保持作者的写作风格
   - 排版修复不改变语义，只改善可读性

完成后返回：
- 修改统计：纠正错别字 X 处，排版修复 Y 处，格式优化 Z 处
- 主要修改列表（最多 10 项）
- 处理状态：成功/失败
---
```

#### 3.2 批量处理

```python
def process_all_chapters(chapter_files):
    """使用 subagent 批量处理所有章节"""
    results = []
    for chapter_file in chapter_files:
        # 启动 subagent 处理
        result = process_chapter_with_subagent(chapter_file)
        results.append(result)
    return results
```

#### 3.3 纠错规则参考

```python
# 常见错别字映射（示例）
COMMON_TYPOS = {
    # 形近字
    '己经': '已经',
    '在再': '再在',  # 需要上下文判断
    '那里': '哪里',  # 疑问句中

    # 同音字
    '做作': '作',  # 需要上下文
    '副幅': '幅',

    # OCR 常见错误
    '囗': '口',
    '廾': '开',
    '亻': '人',
}

# 关键词加粗规则
BOLD_KEYWORDS = [
    # 强调词
    '重要', '关键', '核心', '必须', '注意',
    # 结论词
    '因此', '所以', '总之', '综上所述',
    # 数据格式
    r'\d+%',  # 百分比
    r'\d+亿',  # 金额
]
```

#### 3.4 OCR 排版修复规则

```python
import re

def fix_ocr_formatting(content):
    """
    修复 OCR 产生的排版问题
    """
    lines = content.split('\n')
    result = []
    buffer = ""

    for i, line in enumerate(lines):
        stripped = line.strip()

        # 跳过空行（保留段落分隔）
        if not stripped:
            if buffer:
                result.append(buffer)
                buffer = ""
            result.append("")
            continue

        # 跳过特殊行（标题、列表、引用、代码块）
        if is_special_line(stripped):
            if buffer:
                result.append(buffer)
                buffer = ""
            result.append(stripped)
            continue

        # 判断是否需要与前一行合并
        if buffer:
            # 如果前一行没有以句末标点结束，且当前行不是新段落开头
            if should_merge_lines(buffer, stripped):
                buffer += stripped  # 直接拼接，不加空格
            else:
                result.append(buffer)
                buffer = stripped
        else:
            buffer = stripped

    if buffer:
        result.append(buffer)

    return '\n'.join(result)


def is_special_line(line):
    """判断是否为特殊行（不应合并）"""
    # 标题
    if re.match(r'^#{1,6}\s', line):
        return True
    # 列表项
    if re.match(r'^[\-\*\+]\s', line) or re.match(r'^\d+\.\s', line):
        return True
    # 引用
    if line.startswith('>'):
        return True
    # 代码块标记
    if line.startswith('```'):
        return True
    # 分隔线
    if re.match(r'^[\-\*_]{3,}$', line):
        return True
    # 表格行
    if '|' in line and line.count('|') >= 2:
        return True
    return False


def should_merge_lines(prev_line, curr_line):
    """
    判断两行是否应该合并
    核心逻辑：如果前一行没有以句末标点结束，通常是异常换行
    """
    # 句末标点（中英文）
    sentence_end_marks = '。！？.!?；;：:'

    # 如果前一行以句末标点结束，不合并
    if prev_line and prev_line[-1] in sentence_end_marks:
        return False

    # 如果前一行以逗号、顿号等结束，可能是列表，不合并
    if prev_line and prev_line[-1] in '，、,':
        # 但如果当前行看起来像是句子的延续，则合并
        if not curr_line[0].isupper() and not re.match(r'^\d', curr_line):
            return True
        return False

    # 如果当前行以小写字母或中文开头，很可能是异常换行
    if curr_line and (curr_line[0].islower() or is_chinese(curr_line[0])):
        return True

    # 默认合并（保守策略是不合并，但 OCR 问题多时可以激进一些）
    return True


def is_chinese(char):
    """判断是否为中文字符"""
    return '\u4e00' <= char <= '\u9fff'


def clean_spaces(content):
    """清理空格问题"""
    # 删除中文之间的空格
    content = re.sub(r'([\u4e00-\u9fff])\s+([\u4e00-\u9fff])', r'\1\2', content)
    # 连续多个空格变为一个
    content = re.sub(r' {2,}', ' ', content)
    # 删除行首空格（markdown 缩进除外）
    lines = content.split('\n')
    result = []
    for line in lines:
        # 保留代码块和列表的缩进
        if not re.match(r'^(\s{4}|\t)', line) and not re.match(r'^\s*[\-\*\+\d]', line):
            line = line.lstrip()
        result.append(line.rstrip())
    return '\n'.join(result)


def remove_extra_blank_lines(content):
    """删除多余的连续空行"""
    # 连续 3 个以上空行变为 2 个（保留段落间隔）
    return re.sub(r'\n{3,}', '\n\n', content)
```

##### OCR 排版问题示例

| 问题类型 | 错误示例 | 修复后 |
|----------|----------|--------|
| 句中异常换行 | `经济增长的主要动力来自于投\n资和消费` | `经济增长的主要动力来自于投资和消费` |
| 段内多余空行 | `第一点是...\n\n第二点是...` | `第一点是...第二点是...`（如果是连续论述） |
| 中文间空格 | `货币 政策 的 影响` | `货币政策的影响` |
| 连续空格 | `GDP增长    达到5%` | `GDP增长达到5%` |
| 行首多余空格 | `    这是一段普通文字` | `这是一段普通文字` |

### 第四步：生成 EPUB 电子书

直接从各章节 Markdown 文件生成 EPUB 电子书（无需生成合集文件）：

```python
# 使用 Python 直接调用
import sys
import os

# 添加 skill 脚本路径
skill_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                          '.claude', 'skills', 'markdown-to-epub', 'scripts')
sys.path.insert(0, skill_path)

from epub_generator import create_epub_from_markdown

def generate_epub_from_chapters(folder_path, book_title, author):
    """从章节文件直接生成 EPUB"""
    chapter_files = scan_ebook_folder(folder_path)

    # 动态合并章节内容（仅在内存中，不生成合集文件）
    combined_parts = []
    combined_parts.append(f"# {book_title}\n")
    combined_parts.append(f"> 作者：{author}\n")
    combined_parts.append("\n---\n")

    for chapter_file in chapter_files:
        with open(chapter_file, 'r', encoding='utf-8') as f:
            content = f.read()
        combined_parts.append(content)
        combined_parts.append("\n\n---\n\n")

    markdown_content = ''.join(combined_parts)

    # 生成 EPUB（指定 base_path 以正确嵌入图片）
    output_path = os.path.join(folder_path, f'{book_title}.epub')
    create_epub_from_markdown(
        markdown_content=markdown_content,
        output_path=output_path,
        title=book_title,
        author=author,
        base_path=folder_path,  # 重要：指定图片基础目录
        generate_cover=True,    # 自动生成 AI 封面
        cover_style="modern"
    )
    return output_path
```

**参数说明**：

- `markdown_content`：动态合并的 Markdown 内容（仅在内存中）
- `output_path`：输出的 EPUB 文件路径
- `title`：电子书标题
- `author`：作者名称
- `base_path`：**图片基础目录**（用于解析相对路径图片）
- `generate_cover`：是否自动生成 AI 封面
- `cover_style`：封面风格

**图片嵌入机制**：

1. 自动扫描 Markdown 中的所有 `![alt](path)` 图片引用
2. 根据 `base_path` 解析相对路径（如 `./images/xxx.jpg`）
3. 读取图片文件并嵌入 EPUB 包中
4. 自动更新图片路径为 EPUB 内部路径

## 完整处理流程示例

```
用户输入：处理电子书 "趋势与周期3-货币债务与投资时钟"

处理步骤：
1. [扫描目录] 发现 22 个章节文件
2. [图片处理]
   - 扫描到 36 个图片引用
   - 转换 12 个 webp 图片为 jpg
   - 识别 5 个结构化图片，已添加文本描述
   - 图片已移动到 images/[章节名]/ 目录
3. [文本纠错]
   - 使用 subagent 逐章处理
   - 共纠正 45 处错别字
   - 优化 128 处格式
4. [生成 EPUB] 从章节文件直接生成 趋势与周期3-货币债务与投资时钟.epub

完成！电子书已生成。
```

## 辅助脚本

### convert_images.py

位置：`.claude/skills/ebook-processor/scripts/convert_images.py`

功能：
- 图片格式转换（webp/gif/bmp → jpg）
- 原文件备份
- 目录结构创建

### text_optimizer.py

位置：`.claude/skills/ebook-processor/scripts/text_optimizer.py`

功能：
- 错别字检测与纠正
- 关键词加粗
- 格式规范化

## 输出结构

```
电子书名称/
├── [书名]-目录.md              # 目录文件
├── [书名].epub                 # 生成的 EPUB 电子书
├── cover.jpg                   # AI 生成的封面图片
├── processing_report.md        # 处理报告
├── 01_第一章标题.md            # 优化后的章节文件
├── 02_第二章标题.md
├── ...
├── images/
│   ├── 01_第一章标题/
│   │   ├── image_001.jpg       # 转换后的图片
│   │   ├── image_002.jpg
│   │   └── bak/                # 原始图片备份
│   │       └── image_001.webp
│   ├── 02_第二章标题/
│   │   └── ...
│   └── ...
```

## 处理报告模板

```markdown
# 电子书处理报告

## 基本信息
- 电子书名称：{book_title}
- 处理时间：{timestamp}
- 章节数量：{chapter_count}

## 图片处理
- 总图片数：{total_images}
- 格式转换：{converted_count} 个
- 结构化识别：{structured_count} 个

## 文本优化
- 错别字纠正：{typo_count} 处
- OCR 排版修复：{layout_fix_count} 处
- 格式优化：{format_count} 处

## 主要修改记录
| 章节 | 类型 | 原文 | 修改后 |
|------|------|------|--------|
| ... | 错别字 | ... | ... |

## 输出文件
- EPUB 文件：{epub_file}
- 封面图片：{cover_file}
```

## 注意事项

1. **忠于原文**：纠正错别字时不改变原意，只修正明显错误
2. **保守加粗**：只对确定重要的内容加粗，避免过度标记
3. **图片备份**：转换前务必备份原始图片
4. **逐章处理**：使用 subagent 处理每个章节，避免 token 超限
5. **验证结果**：每步处理后验证结果正确性
6. **保留元数据**：保持原文链接、作者信息等脚注

## 错误处理

- **图片转换失败**：记录失败文件，继续处理其他文件
- **subagent 超时**：重试一次，失败则标记需人工检查
- **EPUB 生成失败**：检查章节文件格式，修复后重试
