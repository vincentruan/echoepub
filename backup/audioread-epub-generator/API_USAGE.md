# SiliconFlow API 集成使用文档

## 概述

`audioread-epub-generator` 技能现已集成 SiliconFlow API，提供以下功能：

1. **智能翻译** - 使用外部大模型进行翻译，避免技能内容过大
2. **图片分析** - 使用 VLM（视觉语言模型）生成图片描述

## 环境变量配置

在使用 API 功能前，需要配置以下环境变量：

```bash
# 必需：API 密钥
export ECHO_EPUB_OPEN_API_KEY='your-api-key'

# 可选：自定义 API 基础地址（默认：https://api.siliconflow.cn/v1）
# 支持任何 OpenAI 兼容的 API 端点
export ECHO_EPUB_OPEN_AI_BASE_URL='https://api.siliconflow.cn/v1'

# 可选：自定义翻译模型（默认：MiniMaxAI/MiniMax-M2）
export ECHO_EPUB_TRANSLATE_MODEL='MiniMaxAI/MiniMax-M2'

# 可选：自定义图片分析模型（默认：PaddlePaddle/PaddleOCR-VL-1.5）
export ECHO_EPUB_VLM_MODEL='PaddlePaddle/PaddleOCR-VL-1.5'
```

### 环境变量说明

| 变量名 | 必需 | 默认值 | 说明 |
|--------|------|--------|------|
| `ECHO_EPUB_OPEN_API_KEY` | ✅ 是 | - | API 密钥（支持 SiliconFlow 或其他 OpenAI 兼容服务）|
| `ECHO_EPUB_OPEN_AI_BASE_URL` | ❌ 否 | `https://api.siliconflow.cn/v1` | OpenAI 兼容 API 的基础 URL |
| `ECHO_EPUB_TRANSLATE_MODEL` | ❌ 否 | `MiniMaxAI/MiniMax-M2` | 翻译模型名称 |
| `ECHO_EPUB_VLM_MODEL` | ❌ 否 | `PaddlePaddle/PaddleOCR-VL-1.5` | 图片分析模型名称 |

**注意：** 如果使用旧的环境变量名 `ECHO_EPUB_API_BASE`，系统仍然支持（向后兼容）。

### 获取 API 密钥

1. 访问 [SiliconFlow 控制台](https://cloud.siliconflow.cn/)
2. 注册/登录账户
3. 进入 API Keys 页面
4. 创建新的 API 密钥
5. 将密钥设置到环境变量 `ECHO_EPUB_OPEN_API_KEY`

## 功能说明

### 1. 智能翻译

**特点：**
- 自动检测和保护技术术语（GPU、API、LLM 等）
- 批量翻译优化（每批 5 个段落）
- 优雅的降级处理（API 不可用时保留原文）

**工作流程：**
1. 使用 `TechnicalTermDetector` 提取技术术语
2. 构建包含术语保护的翻译提示词
3. 调用 SiliconFlow 翻译 API
4. 返回翻译结果

**API 端点：** `https://api.siliconflow.cn/v1/chat/completions`

**默认模型：** `MiniMaxAI/MiniMax-M2`

### 2. 图片分析

**特点：**
- 自动分类图片类型（图表、流程图、架构图、截图等）
- 生成结构化的音频友好描述
- 支持上下文感知分析
- 优雅的降级处理（API 不可用时生成占位描述）

**描述格式：**

```
> **图片说明**：这是一张[图片类型]。
> 核心结论是：[1-2 句话总结核心内容]
> 关键元素包括：[关键视觉元素]
> 要点总结：
> - 第一，[要点 1]
> - 第二，[要点 2]
> - 第三，[要点 3]
> - 第四，[要点 4]
> - 第五，[要点 5]
```

**API 端点：** `https://api.siliconflow.cn/v1/chat/completions#vlm`

**默认模型：** `PaddlePaddle/PaddleOCR-VL-1.5`

## 使用示例

### 基本用法

```bash
# 设置 API 密钥
export ECHO_EPUB_OPEN_API_KEY='sk-xxxxx'

# 处理 EPUB 文件（启用翻译和图片分析）
python .claude/skills/audioread-epub-generator/scripts/main.py \
  "books/架构师之路（58沈剑）.epub"
```

### 使用不同的 API 提供商

`ECHO_EPUB_OPEN_AI_BASE_URL` 支持任何 OpenAI 兼容的 API 端点：

#### 1. 使用 SiliconFlow（默认）

```bash
export ECHO_EPUB_OPEN_API_KEY='your-siliconflow-key'
export ECHO_EPUB_OPEN_AI_BASE_URL='https://api.siliconflow.cn/v1'
```

#### 2. 使用 OpenAI

```bash
export ECHO_EPUB_OPEN_API_KEY='your-openai-key'
export ECHO_EPUB_OPEN_AI_BASE_URL='https://api.openai.com/v1'
export ECHO_EPUB_TRANSLATE_MODEL='gpt-4o'
export ECHO_EPUB_VLM_MODEL='gpt-4o'
```

#### 3. 使用 Azure OpenAI

```bash
export ECHO_EPUB_OPEN_API_KEY='your-azure-key'
export ECHO_EPUB_OPEN_AI_BASE_URL='https://your-resource.openai.azure.com/openai/deployments/your-deployment'
```

#### 4. 使用其他兼容服务

```bash
# 例如：使用本地 Ollama 服务
export ECHO_EPUB_OPEN_API_KEY='ollama'  # Ollama 不需要真实密钥
export ECHO_EPUB_OPEN_AI_BASE_URL='http://localhost:11434/v1'

# 例如：使用自建的代理服务
export ECHO_EPUB_OPEN_API_KEY='your-proxy-key'
export ECHO_EPUB_OPEN_AI_BASE_URL='https://your-proxy.com/v1'
```

### 禁用翻译

```bash
python .claude/skills/audioread-epub-generator/scripts/main.py \
  "books/架构师之路（58沈剑）.epub" \
  --no-translation
```

### 自定义模型

```bash
export ECHO_EPUB_TRANSLATE_MODEL='Qwen/Qwen2.5-7B-Instruct'
export ECHO_EPUB_VLM_MODEL='OpenGVLab/InternVL2-Llama3-76B'

python .claude/skills/audioread-epub-generator/scripts/main.py \
  "books/input.pdf"
```

## API 调用详解

### 翻译 API 调用

**文件：** `siliconflow_client.py`

```python
from siliconflow_client import get_siliconflow_client

# 获取客户端实例
client = get_siliconflow_client()

# 单文本翻译
translated = client.translate_text(
    text="This is a test with GPU and API terms.",
    source_lang="English",
    target_lang="Chinese",
    preserve_terms=["GPU", "API"]  # 保护这些术语不翻译
)

# 批量翻译
texts = ["Paragraph 1", "Paragraph 2", "Paragraph 3"]
translations = client.translate_batch(
    texts,
    source_lang="English",
    target_lang="Chinese",
    preserve_terms=["GPU", "API"],
    batch_size=5  # 每批 5 个段落
)
```

**API 参数：**
- `model`: 翻译模型名称
- `messages`: 翻译提示词
- `temperature`: 0.3（较低温度以保持一致性）
- `max_tokens`: 4096（最大响应长度）

### 图片分析 API 调用

```python
from siliconflow_client import get_siliconflow_client

client = get_siliconflow_client()

description = client.analyze_image(
    image_path="/path/to/image.png",
    context="This is a chart showing performance comparison.",
    image_type="chart"  # chart, flowchart, architecture, general, etc.
)

print(description)
```

**API 参数：**
- `model`: VLM 模型名称
- `messages`: 包含图片 base64 编码和分析提示词
- `temperature`: 0.3
- `max_tokens`: 2048

## 降级策略

当 API 不可用时，系统会优雅降级：

### 翻译降级

```python
# API 调用失败
❌ SiliconFlow API 不可用
✅ 保留原文文本
✅ 记录警告信息
✅ 继续处理
```

### 图片分析降级

```python
# VLM API 调用失败
❌ SiliconFlow VLM 不可用
✅ 生成结构化占位描述
✅ 包含图片类型信息
✅ 标注"需要视觉模型分析"
```

## 性能优化

### 批量翻译

- 默认每批翻译 5 个段落
- 减少API调用次数
- 提高处理速度

```python
# 自定义批大小
translations, success = translate_with_api(
    paragraphs,
    batch_size=10  # 更大的批次
)
```

### 技术术语保护

- 自动提取前 20 个最常见的技术术语
- 在提示词中明确标注需要保留
- 避免错误翻译专业术语

## 费用说明

SiliconFlow API 按使用量计费：

- **翻译模型**：MiniMax-M2 约每 1M tokens ¥0.15
- **图片分析**：PaddleOCR-VL-1.5 按图片大小计费

建议：
- 对于小文件，直接使用默认配置
- 对于大文件，考虑先测试少量章节
- 查看处理报告中的统计信息

## 测试

运行测试套件验证 API 集成：

```bash
cd .claude/skills/audioread-epub-generator/scripts

# 设置 API 密钥
export ECHO_EPUB_OPEN_API_KEY='your-api-key'

# 运行测试
python test_api_integration.py
```

**测试内容：**
1. 翻译 API 调用
2. 图片分析 API 调用
3. 降级行为验证

## 故障排查

### 问题：API 密钥错误

```
Error: API key not found
```

**解决方案：**
```bash
# 检查环境变量
echo $ECHO_EPUB_OPEN_API_KEY

# 重新设置
export ECHO_EPUB_OPEN_API_KEY='your-api-key'
```

### 问题：API 调用超时

```
Error: Request timeout
```

**解决方案：**
- 检查网络连接
- 尝试使用代理
- 减少批处理大小

### 问题：翻译结果为空

```
Translation result: (empty)
```

**解决方案：**
- 检查 API 配额
- 查看模型是否可用
- 尝试使用不同的模型

## 文件结构

```
.claude/skills/audioread-epub-generator/
├── scripts/
│   ├── siliconflow_client.py      # API 客户端
│   ├── translate_content.py       # 翻译模块（使用 API）
│   ├── image_descriptor.py         # 图片分析模块（使用 VLM API）
│   ├── test_api_integration.py    # API 测试脚本
│   └── ...
└── API_USAGE.md                   # 本文档
```

## 更多资源

- [SiliconFlow API 文档](https://docs.siliconflow.cn/cn/api-reference/chat-completions/chat-completions)
- [SiliconFlow VLM 文档](https://docs.siliconflow.cn/cn/api-reference/chat-completions/chat-completions#vlm)
- [模型列表](https://cloud.siliconflow.cn/models)

## 版本历史

- **v2.0** (2025-02-02)
  - ✅ 集成 SiliconFlow 翻译 API
  - ✅ 集成 SiliconFlow VLM 图片分析 API
  - ✅ 实现优雅降级策略
  - ✅ 添加技术术语保护
  - ✅ 批量翻译优化

- **v1.0** (2025-01-29)
  - 初始版本
  - 占位符翻译和图片描述
