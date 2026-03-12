# Markdown to Audioread

将标准 Markdown 文件转换为适合语音朗读的格式，使纯文字也能完整传达原文信息。

## 核心能力

| 功能 | 说明 |
|------|------|
| 图片描述 | 结合上下文调用视觉模型生成连贯中文描述 |
| 代码说明 | Agent 直接分析代码，生成功能总结 |
| 表格语音化 | 表格转为适合听觉的文字说明 |
| 列表语音化 | 列表项添加序号化叙述 |
| 数学公式 | 识别公式类型并添加描述 |
| 引用标记 | 添加引用开始/结束标记 |
| 翻译 | 非中文段落翻译为中文 |
| 导读 | 自动添加章节导语 |

## 使用方法

```bash
# 处理文件夹（subagent 并行）
python scripts/audioread_processor.py "books/xxx_markdown"

# 处理单个文件
python scripts/audioread_processor.py "chapter.md"

# 可选参数
python scripts/audioread_processor.py "books/xxx_markdown" \
    --no-subagents --no-translate --no-intro
```

## 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `ECHO_EPUB_OPEN_API_KEY` | API Key（必须） | - |
| `ECHO_EPUB_OPEN_AI_BASE_URL` | OpenAI 兼容 API 地址 | `https://api.siliconflow.cn/v1` |
| `ECHO_EPUB_TRANSLATE_MODEL` | 翻译模型 | `MiniMaxAI/MiniMax-M2` |
| `ECHO_EPUB_VLM_MODEL` | 视觉模型 | `Qwen/Qwen2-VL-7B-Instruct` |

## 脚本

| 脚本 | 功能 |
|------|------|
| `audioread_processor.py` | 主处理脚本 |
| `image_descriptor.py` | 图片描述 |
| `openai_client.py` | API 客户端 |
| `audio_rewriter.py` | 格式转换 |
| `translate_content.py` | 翻译 |
| `technical_term_detector.py` | 术语检测 |

## 依赖

```bash
pip install requests Pillow
```
