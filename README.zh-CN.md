# 有声读物优化 EPUB 生成器

> 将 EPUB、PDF 和 Markdown 文件转换为适合有声读物的 EPUB 电子书，具有 AI 驱动的图片描述、智能翻译和 TTS 优化格式。

[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

## 🌟 项目概述

**有声读物优化 EPUB 生成器** 是一个端到端的处理管道，可将电子书和文档转换为适合有声读物的 EPUB 文件。它从多种格式提取内容，使用 AI 生成的图片描述进行增强，在翻译非中文内容时保护技术术语，并优化结构以支持文本转语音（TTS）播放。

### 核心特色

- **AI 驱动的图片分析** - 使用 VLM（视觉语言模型）为图表、流程图和截图生成结构化的音频友好描述
- **智能翻译** - 在翻译过程中检测并保护 40+ 技术术语（GPU、API、LLM 等）
- **TTS 优化** - 将长句子、表格和列表转换为自然的语音模式
- **格式无关** - 支持 EPUB、PDF、Markdown 和多文件文件夹作为输入

## ✨ 主要功能

### 📖 内容增强

- **图片描述** - 自动分析图片并生成结构化描述：
  - 图表类型分类（折线图、柱状图、饼图、流程图、架构图等）
  - 核心结论提取
  - 关键元素叙述
  - 3-7 个要点用于音频播放

- **智能翻译** - 翻译非中文内容：
  - 自动技术术语检测（40+ 术语）
  - 术语密度分析，避免不必要的翻译
  - 批处理优化
  - API 不可用时优雅降级

- **有声读物优化** - 为倾听重新表达内容：
  - 拆分长句子
  - 将表格转换为可叙述格式
  - 将列表转换为"逐点叙述"
  - 添加章节介绍和总结

### 🔧 输入支持

| 格式 | 状态 | 说明 |
|------|------|------|
| **EPUB** | ✅ 原生支持 | 提取章节、文本、图片和元数据 |
| **PDF** | ✅ 支持 | 转换为 markdown，保留层次结构 |
| **Markdown** | ✅ 支持 | 直接处理 |
| **文件夹** | ✅ 支持 | 多格式处理，自动排序 |

### 🌍 翻译与本地化

- **目标语言**：简体中文 (zh-CN)
- **源语言**：英语、日语和其他非中文内容
- **术语保护**：GPU、API、LLM、GPT、Claude、框架、协议等
- **智能检测**：跳过技术术语密度高的内容（>15%）

## 🚀 快速开始

### 安装

```bash
# 克隆仓库
git clone https://github.com/yourusername/echoepub.git
cd echoepub

# 安装依赖
pip install -r requirements.txt
```

### 基本用法

```bash
# 设置 API 密钥（翻译和图片分析需要）
export ECHO_EPUB_OPEN_API_KEY='your-api-key-here'

# 处理 EPUB 文件
python .claude/skills/audioread-epub-generator/scripts/main.py \
  "books/input.epub"

# 处理 PDF
python .claude/skills/audioread-epub-generator/scripts/main.py \
  "documents/paper.pdf"

# 使用选项处理
python .claude/skills/audioread-epub-generator/scripts/main.py \
  "books/input.epub" \
  "output/book_audio.epub" \
  --style conversational
```

### 输出

- **EPUB 文件**：`books/input_audio.epub`
- **处理报告**：`books/input_audio_report.md`

## ⚙️ 配置

### 环境变量

| 变量 | 必需 | 默认值 | 说明 |
|------|------|--------|------|
| `ECHO_EPUB_OPEN_API_KEY` | ✅ 是 | - | 翻译和图片分析的 API 密钥 |
| `ECHO_EPUB_OPEN_AI_BASE_URL` | ❌ 否 | `https://api.siliconflow.cn/v1` | OpenAI 兼容 API 基础 URL |
| `ECHO_EPUB_TRANSLATE_MODEL` | ❌ 否 | `MiniMaxAI/MiniMax-M2` | 翻译模型名称 |
| `ECHO_EPUB_VLM_MODEL` | ❌ 否 | `PaddlePaddle/PaddleOCR-VL-1.5` | 图片分析模型名称 |

### API 提供商

技能支持任何 OpenAI 兼容的 API：

```bash
# SiliconFlow（默认）
export ECHO_EPUB_OPEN_AI_BASE_URL='https://api.siliconflow.cn/v1'

# OpenAI
export ECHO_EPUB_OPEN_AI_BASE_URL='https://api.openai.com/v1'
export ECHO_EPUB_TRANSLATE_MODEL='gpt-4o'

# 本地 Ollama
export ECHO_EPUB_OPEN_AI_BASE_URL='http://localhost:11434/v1'
export ECHO_EPUB_TRANSLATE_MODEL='llama3.1'

# Azure OpenAI
export ECHO_EPUB_OPEN_AI_BASE_URL='https://your-resource.openai.azure.com/...'
```

## 📊 处理流程

### 阶段 A：输入识别

1. 识别输入类型（EPUB/PDF/Markdown/文件夹）
2. 提取内容和结构
3. 标准化为 markdown 中间层

### 阶段 B：内容增强

4. 检测并提取技术术语
5. 翻译非中文段落（保护术语）
6. 生成 AI 驱动的图片描述
7. 添加章节介绍和总结

### 阶段 C：有声读物优化

8. 拆分长句子
9. 将表格和列表转换为可叙述格式
10. 优化标题层次结构以适应 TTS

### 阶段 D：EPUB 生成

11. 合并处理后的内容
12. 使用元数据和目录生成最终 EPUB
13. 创建处理报告

## 📝 图片描述格式

所有图片都获得结构化描述：

```
> **图片说明**：这是一张[图表类型]。
> 核心结论是：[1-2 句话总结核心结论]
> 关键元素包括：[关键视觉元素]
> 要点总结：
> - 第一，[要点 1]
> - 第二，[要点 2]
> - 第三，[要点 3]
> - 第四，[要点 4]
> - 第五，[要点 5]
```

### 支持的图片类型

- **图表** - 折线图、柱状图、饼图、散点图，包含坐标轴和趋势
- **流程图** - 包含步骤和分支的处理流程
- **架构图** - 系统组件和关系
- **截图** - UI 界面和关键字段
- **表格** - 数据摘要和关键洞察

## 🛡️ 技术术语保护

### 检测类别

- **缩略词**：GPU、CPU、LLM、API、HTTP、JSON 等
- **模型名称**：GPT-4、Claude、Llama、BERT、Mistral 等
- **框架**：TensorFlow、PyTorch、React、Django 等
- **语言**：Python、JavaScript、Go、Rust 等
- **协议**：HTTP、HTTPS、TCP、IP、DNS、SSL 等

### 翻译逻辑

```
如果中文比例 >= 30%：
    跳过（已是中文）
否则如果技术术语密度 > 15%：
    跳过（保留技术内容）
否则如果技术术语密度 > 5% 且中文 < 15%：
    翻译（保护术语）
否则：
    标准翻译
```

## 📈 性能表现

### 测试结果

在 `架构师之路（58沈剑）.epub` 上测试：

| 指标 | 结果 |
|------|------|
| 总图片数 | 914 |
| 有描述的图片 | 456 (100%) |
| 翻译段落数 | 206 |
| 拆分句子数 | 693 |
| 图片警告 | 0 |
| 处理时间 | ~2 分钟 |

### 改进效果

| 问题 | 优化前 | 优化后 | 改进幅度 |
|------|--------|--------|----------|
| 图片未找到 | 458 个警告 | 0 个警告 | ✅ 100% 修复 |
| 翻译段落数 | 234 | 206 | ✅ 减少 12% |
| 图片描述 | 占位符 | AI 生成 | ✅ 真实分析 |
| 上下文占用 | 大 | 小 | ✅ 基于 API |

## 🔍 高级用法

### 禁用翻译

```bash
python scripts/main.py "input.epub" --no-translation
```

### 自定义阅读风格

```bash
# 更对话式
python scripts/main.py "input.epub" --style conversational

# 更正式
python scripts/main.py "input.epub" --style formal
```

### 自定义输出路径

```bash
python scripts/main.py "input.epub" "custom_output.epub"
```

### 处理文件夹

```bash
# 处理文件夹中的所有文件
python scripts/main.py "documents/chapter1/"
```

## 🧪 测试

### 运行测试套件

```bash
cd .claude/skills/audioread-epub-generator/scripts

# 测试 API 集成
python test_api_integration.py

# 使用示例文件测试
python main.py "test.epub" --no-translation
```

## 📚 文档

- **[API_USAGE.md](.claude/skills/audioread-epub-generator/API_USAGE.md)** - API 集成指南
- **[UPDATE_SUMMARY.md](.claude/skills/audioread-epub-generator/UPDATE_SUMMARY.md)** - 更新总结
- **[ENV_VAR_UPDATE.md](.claude/skills/audioread-epub-generator/ENV_VAR_UPDATE.md)** - 环境变量更新

## 🔧 开发

### 项目结构

```
echoepub/
├── .claude/skills/audioread-epub-generator/
│   ├── scripts/
│   │   ├── main.py                    # 主入口
│   │   ├── epub_extractor.py          # EPUB 内容提取
│   │   ├── siliconflow_client.py     # API 客户端
│   │   ├── translate_content.py       # 翻译模块
│   │   ├── technical_term_detector.py # 术语检测
│   │   ├── image_descriptor.py        # 图片分析
│   │   ├── markdown_processor.py      # Markdown 处理
│   │   ├── epub_generator.py          # EPUB 生成
│   │   ├── audio_rewriter.py          # TTS 优化
│   │   └── test_api_integration.py    # 测试套件
│   ├── references/
│   │   └── image_description_rules.md
│   └── SKILL.md
├── books/                            # 输入/输出目录
└── CLAUDE.md                         # 项目概述
```

### 核心脚本

| 脚本 | 用途 |
|------|------|
| `main.py` | CLI 入口点，协调整个管道 |
| `epub_extractor.py` | 从 EPUB 文件提取内容 |
| `siliconflow_client.py` | 处理翻译和 VLM 的 API 调用 |
| `technical_term_detector.py` | 检测和保护技术术语 |
| `image_descriptor.py` | 生成 AI 驱动的图片描述 |
| `translate_content.py` | 管理翻译工作流 |
| `epub_generator.py` | 使用元数据创建最终 EPUB |
| `audio_rewriter.py` | 优化内容以适应 TTS 播放 |

## 🤝 贡献

欢迎贡献！请：

1. Fork 仓库
2. 创建功能分支
3. 进行更改
4. 添加测试（如适用）
5. 提交 pull request

## 📄 许可证

MIT License - 详见 LICENSE 文件

## 🙏 致谢

- **SiliconFlow** - 翻译和图片分析的 API 平台
- **ebooklib** - EPUB 文件生成
- **PyMuPDF** - PDF 内容提取
- **html2text** - HTML 到 Markdown 转换

## 📞 支持

如有问题、疑问或建议：

1. 查看 [API_USAGE.md](.claude/skills/audioread-epub-generator/API_USAGE.md)
2. 阅读 [UPDATE_SUMMARY.md](.claude/skills/audioread-epub-generator/UPDATE_SUMMARY.md)
3. 在 GitHub 上提 issue

## 📖 更新历史

### v2.0 (2025-02-02)

主要优化：

- ✅ 集成 SiliconFlow API 进行翻译和图片分析
- ✅ 添加技术术语检测和保护机制
- ✅ 修复图片路径问题（从 458 个警告到 0 个）
- ✅ 实现优雅的 API 降级策略
- ✅ 支持任何 OpenAI 兼容的 API 端点
- ✅ 创建完整的文档和测试套件

### v1.0 (2025-01-29)

初始版本：
- ✅ EPUB/PDF/Markdown 输入支持
- ✅ 占位符翻译和图片描述
- ✅ TTS 优化基础功能

---

**用 ❤️ 为有声读物爱好者制作**
