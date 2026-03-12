---
name: markdown-to-audioread
description: Transform standard Markdown files into audio-friendly format optimized for TTS reading. Processes images (generates contextual Chinese descriptions via vision models), code blocks (generates functional summaries), tables, lists, math formulas, and applies speech-optimized formatting. Use after input conversion (epub/pdf/markdown) to prepare content for audio narration.
---

# Markdown to Audioread

将标准 Markdown 文件转换为适合语音朗读的格式。核心目标：让文字（后续转语音）也能清晰传达原文完整内容，**忠于原文，不得篡改**。

## 输入要求

标准 Markdown 目录结构（由 `epub-to-markdown-converter`、`pdf-to-markdown-converter` 或 `markdown-converter` 生成）：

```
$原文件名_markdown/
├── 00_目录.md
├── 01_章节.md
├── 02_章节.md
├── images/
│   └── ...
└── $原文件名_report.md
```

## 输出

处理后保持相同目录结构，内容已优化为适合语音朗读：

```
$原文件名_markdown/
├── _audioread/              # 输出目录（新增）
│   ├── 01_章节.md       # 已优化
│   ├── 02_章节.md       # 已优化
│   ├── glossary.md      # 术语表
│   └── *_report.md      # 处理报告
├── 00_目录.md           # 不修改
├── 01_章节.md           # 不修改（源文件）
├── 02_章节.md           # 不修改（源文件）
├── images/              # 不修改
└── $原文件名_report.md  # 不修改
```

> 源文件始终不会被修改，所有处理结果输出到 `_audioread/` 子文件夹。

## 处理策略

### 1. 图片描述生成

结合章节上下文和图片内容，调用第三方视觉模型生成**一段连贯的中文描述**，使读者不看图片也能理解上下文语义。

**处理方式：**
1. 提取图片前后各 5 行上下文
2. 将上下文 + 图片一起发送给视觉模型（通过 OpenAI 兼容接口）
3. 模型返回一段连贯的中文描述文字
4. 以引用块格式插入图片下方

```markdown
# 处理前
上文讨论了微服务架构的优势...

![架构图](./images/01/arch.jpg)

下文将详细介绍各组件...

# 处理后
上文讨论了微服务架构的优势...

![架构图](./images/01/arch.jpg)

> 【图片描述】这张架构图展示了一个典型的微服务系统结构，包含用户层（Web端和移动端入口）、API网关层负责统一路由和鉴权、三个核心服务（订单服务、用户服务、支付服务），以及底层的MySQL主从数据库集群和Redis缓存，各服务之间通过消息队列进行异步通信。

下文将详细介绍各组件...
```

**跳过的图片：** 二维码、表情包、纯装饰图、封面图片、作者照片、图标/Logo。

### 2. 代码块处理

当 agent 处理每个章节的 Markdown 文件时，遇到代码块需**直接分析代码内容**，生成功能总结和关键实现说明。代码说明由 agent 自身生成，不调用外部 API。

**处理原则：**
- 总结代码的功能目的（这段代码做了什么）
- 说明关键实现逻辑（怎么实现的）
- 保留原始代码块（忠于原文）
- 在代码块后添加 `【代码说明】` 引用块

````markdown
# 处理前
```python
def quicksort(arr):
    if len(arr) <= 1:
        return arr
    pivot = arr[len(arr) // 2]
    left = [x for x in arr if x < pivot]
    middle = [x for x in arr if x == pivot]
    right = [x for x in arr if x > pivot]
    return quicksort(left) + middle + quicksort(right)
```

# 处理后
```python
def quicksort(arr):
    if len(arr) <= 1:
        return arr
    pivot = arr[len(arr) // 2]
    left = [x for x in arr if x < pivot]
    middle = [x for x in arr if x == pivot]
    right = [x for x in arr if x > pivot]
    return quicksort(left) + middle + quicksort(right)
```

> 【代码说明】这段Python代码实现了快速排序算法。其核心逻辑是选取数组中间位置的元素作为基准值，将数组分为小于、等于、大于基准值的三部分，然后对左右两部分递归排序并合并结果，是一种经典的分治算法实现。
````

### 3. 非中文内容翻译

| 情况 | 处理方式 |
|------|----------|
| 完整英文段落 | 翻译为中文 |
| 专业术语首次出现 | 保留原文 + 中文解释 |
| 代码/变量名 | 保持原样 |
| 产品名/公司名 | 保持原样 |

### 4. 表格转语音格式

```markdown
# 处理前
| 指标 | 2023年 | 2024年 |
|------|--------|--------|
| GDP | 10.2万亿 | 11.5万亿 |

# 处理后（原表格保留，后接语音说明）
> 【表格内容说明】
> 关于GDP：2023年为10.2万亿，2024年为11.5万亿。
```

### 5. 列表转语音格式

```markdown
# 处理前
- 第一点
- 第二点
- 第三点

# 处理后（原列表保留，后接语音说明）
> 以下是3个要点：
第一，第一点。
第二，第二点。
第三，第三点。
```

### 6. 数学公式描述

```markdown
# 处理前
$$E = mc^2$$

# 处理后
> 【数学公式】
> 该公式为计算公式。
> 建议查看原文获取准确表达式。

$$E = mc^2$$
```

### 7. 引用块标记

为引用内容添加音频开始/结束标记（已格式化的图片描述、代码说明等保持不变）：

```markdown
> 【引用开始】
> 原文引用内容
> 【引用结束】
```

### 8. 章节导语

每章自动添加开头导语：
- `本章导读：本章"xxx"将为您讲解核心概念与要点。`

### 9. 句子优化

- 超长句（>200字）拆分为多个短句
- 优化为更适合听觉理解的结构

## 使用方法

```bash
# 处理整个文件夹（使用 subagent 并行处理）
python ./scripts/audioread_processor.py "<markdown-folder>"

# 处理单个章节
python ./scripts/audioread_processor.py "<chapter.md>"

# 禁用 subagent（顺序处理）
python ./scripts/audioread_processor.py "<markdown-folder>" --no-subagents

# 跳过翻译
python ./scripts/audioread_processor.py "<markdown-folder>" --no-translate

# 跳过章节导语
python ./scripts/audioread_processor.py "<markdown-folder>" --no-intro
```

## 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `ECHO_EPUB_OPEN_API_KEY` | API Key（必须） | - |
| `ECHO_EPUB_OPEN_AI_BASE_URL` | OpenAI 兼容 API 地址 | `https://api.siliconflow.cn/v1` |
| `ECHO_EPUB_TRANSLATE_MODEL` | 翻译模型 | `MiniMaxAI/MiniMax-M2` |
| `ECHO_EPUB_VLM_MODEL` | 视觉模型（图片描述） | `Qwen/Qwen2-VL-7B-Instruct` |

> 支持任何 OpenAI 兼容的 API 接口，通过 `ECHO_EPUB_OPEN_AI_BASE_URL` 切换。

## Agent 处理流程

当 agent 使用此技能处理章节时，按以下顺序操作：

1. **读取章节 Markdown 文件**
2. **识别代码块** → 直接分析代码，在代码块后生成 `【代码说明】`
3. **识别图片** → 调用脚本通过视觉模型生成描述
4. **处理数学公式** → 添加类型描述
5. **处理引用块** → 添加音频标记
6. **翻译非中文内容**
7. **转换表格和列表** → 语音友好格式
8. **添加章节导语**
9. **优化句子结构**
10. **写入 `_audioread/` 子文件夹**（源文件不变）

> 代码块说明由 agent 自身能力直接生成，无需调用外部 API。图片描述通过 `image_descriptor.py` 调用视觉模型生成。

## 脚本列表

| 脚本 | 功能 |
|------|------|
| `audioread_processor.py` | 主处理脚本（含 subagent 支持） |
| `image_descriptor.py` | 图片描述生成（调用视觉模型） |
| `openai_client.py` | API 客户端（翻译 + 视觉模型） |
| `audio_rewriter.py` | 语音友好格式转换 |
| `translate_content.py` | 内容翻译 |
| `technical_term_detector.py` | 术语检测（翻译依赖） |

## 处理报告

处理完成后更新 `$原文件名_report.md`：

```markdown
## Audioread 处理

- 处理时间：2026-xx-xx
- 处理章节：N 章
- 图片描述：N 张
- 翻译段落：N 段
- 表格转换：N 个
- 列表转换：N 个
- 代码块处理：N 个
- 引用处理：N 个
- 数学公式：N 个
```

## 依赖

```bash
pip install requests Pillow
```

## 脚本位置

主脚本：`scripts/audioread_processor.py`
