---
name: markdown-to-audioread
description: Transform standard Markdown files into audio-friendly format. Applies image descriptions, translations, table/list conversions, and speech-optimized formatting. Use after input conversion to prepare content for TTS reading.
---

# Markdown to Audioread

将标准 Markdown 文件转换为适合语音朗读的格式，包括图片描述、内容翻译、表格/列表转换等处理。

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

处理后的 Markdown 保持相同目录结构，内容已优化为适合语音朗读：

```
$原文件名_markdown/
├── 00_目录.md           # 保持不变
├── 01_章节.md           # 已优化
├── 02_章节.md           # 已优化
├── images/              # 保持不变
├── glossary.md          # 术语表（新增）
└── $原文件名_report.md  # 更新处理信息
```

## 处理策略

### 1. 图片描述生成

为每张图片生成详细的文字描述：

```markdown
# 处理前
![架构图](./images/01/arch.jpg)

# 处理后
![架构图](./images/01/arch.jpg)

> **图片说明**：这是一张系统架构图。
> **核心内容**：展示微服务架构的组件关系和数据流向。
> **关键元素**：
> - 用户层：Web端和移动端入口
> - 网关层：API Gateway 负责路由和鉴权
> - 服务层：订单服务、用户服务、支付服务
> - 数据层：MySQL 主从集群、Redis 缓存
> 
> **要点总结**：
> - 第一，采用微服务架构实现服务解耦
> - 第二，网关层统一处理跨切面关注点
> - 第三，数据层采用读写分离提升性能
```

#### 图片类型识别

| 图片类型 | 处理方式 |
|----------|----------|
| 架构图 | 描述组件、关系、数据流 |
| 流程图 | 描述步骤、条件、分支 |
| 数据图表 | 提取数据趋势、关键数值 |
| 表格截图 | 转换为文字表格或描述 |
| 代码截图 | 转录为代码块 |
| 界面截图 | 描述关键界面元素和数据 |

#### 跳过的图片类型

- 二维码
- 表情包/梗图
- 纯装饰图
- 封面图片
- 作者照片

### 2. 非中文内容翻译

翻译规则：

| 情况 | 处理方式 |
|------|----------|
| 完整英文段落 | 翻译为中文 |
| 专业术语首次出现 | 保留原文 + 中文解释 |
| 代码/变量名 | 保持原样 |
| 产品名/公司名 | 保持原样 |
| 混合句子 | 保持原样或微调 |

### 3. 表格转语音格式

```markdown
# 处理前
| 指标 | 2023年 | 2024年 |
|------|--------|--------|
| GDP | 10.2万亿 | 11.5万亿 |
| 增长率 | 5.2% | 5.0% |

# 处理后
**表格内容说明**：以下是两年经济指标对比：

关于GDP：2023年为10.2万亿，2024年为11.5万亿。
关于增长率：2023年为5.2%，2024年为5.0%。

> 原始表格数据见上图。
```

### 4. 列表转语音格式

```markdown
# 处理前
- 第一点
- 第二点
- 第三点

# 处理后
以下是三个要点：
第一，第一点。
第二，第二点。
第三，第三点。
```

### 5. 章节导语和总结

每章自动添加：

- **开头导语**：2-4句话介绍本章主题
- **结尾总结**：3-5句话回顾本章要点

### 6. 句子优化

- 长句拆分为多个短句
- 括号嵌套内容重组
- 引用添加"引用开始/结束"标记

## 使用方法

### 处理整个文件夹

```bash
python ./scripts/audioread_processor.py "<markdown-folder>"
```

### 处理单个章节

```bash
python ./scripts/audioread_processor.py "<chapter.md>"
```

## 配置选项

可通过环境变量配置：

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `SILICONFLOW_API_KEY` | 图片描述 API Key | - |
| `AUDIOREAD_LANG` | 目标语言 | zh-CN |
| `AUDIOREAD_ADD_INTRO` | 添加章节导语 | true |
| `AUDIOREAD_ADD_SUMMARY` | 添加章节总结 | true |
| `AUDIOREAD_TRANSLATE` | 翻译非中文内容 | true |

## 处理报告

更新 `$原文件名_report.md`，添加：

```markdown
## Audioread 处理

- 处理时间：2024-xx-xx
- 图片描述：N 张
- 翻译段落：N 段
- 表格转换：N 个
- 列表转换：N 个
- 章节导语：N 章
- 章节总结：N 章
```

## 术语表

生成 `glossary.md`，包含：

```markdown
# 术语表

| 术语 | 原文 | 解释 |
|------|------|------|
| API | Application Programming Interface | 应用程序接口 |
| ...
```

## 依赖

```bash
pip install requests Pillow
```

可选（用于本地翻译）：
```bash
pip install transformers torch
```

## 脚本列表

| 脚本 | 功能 |
|------|------|
| `audioread_processor.py` | 主处理脚本 |
| `image_descriptor.py` | 图片描述生成 |
| `translate_content.py` | 内容翻译 |
| `audio_rewriter.py` | 语音友好格式转换 |
| `technical_term_detector.py` | 术语检测 |
| `text_optimizer.py` | 文本优化 |

## 脚本位置

主脚本：`scripts/audioread_processor.py`
