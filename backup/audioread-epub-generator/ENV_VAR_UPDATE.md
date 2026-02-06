# 环境变量 `ECHO_EPUB_OPEN_AI_BASE_URL` 添加说明

## 更新内容

添加了新的环境变量 `ECHO_EPUB_OPEN_AI_BASE_URL`，用于指定 OpenAI 兼容的 API 基础 URL。

## 使用方法

### 基本用法（使用默认 SiliconFlow）

```bash
export ECHO_EPUB_OPEN_API_KEY='your-api-key'

# 不需要设置 ECHO_EPUB_OPEN_AI_BASE_URL，会自动使用默认值
python .claude/skills/audioread-epub-generator/scripts/main.py "input.epub"
```

### 使用不同的 API 提供商

#### SiliconFlow（默认）
```bash
export ECHO_EPUB_OPEN_API_KEY='sk-xxxxx'
export ECHO_EPUB_OPEN_AI_BASE_URL='https://api.siliconflow.cn/v1'
```

#### OpenAI
```bash
export ECHO_EPUB_OPEN_API_KEY='sk-xxxxx'
export ECHO_EPUB_OPEN_AI_BASE_URL='https://api.openai.com/v1'
export ECHO_EPUB_TRANSLATE_MODEL='gpt-4o'
export ECHO_EPUB_VLM_MODEL='gpt-4o'
```

#### 本地 Ollama
```bash
export ECHO_EPUB_OPEN_API_KEY='ollama'
export ECHO_EPUB_OPEN_AI_BASE_URL='http://localhost:11434/v1'
export ECHO_EPUB_TRANSLATE_MODEL='llama3.1'
export ECHO_EPUB_VLM_MODEL='llava-llama3:8b'
```

## 环境变量优先级

系统按以下顺序查找 API 基础 URL：

1. **`ECHO_EPUB_OPEN_AI_BASE_URL`** (新，推荐)
2. **`ECHO_EPUB_API_BASE`** (旧，向后兼容)
3. 默认值：`https://api.siliconflow.cn/v1`

## 向后兼容性

- ✅ 如果您使用了旧的 `ECHO_EPUB_API_BASE`，系统仍然会正常工作
- ✅ 新的 `ECHO_EPUB_OPEN_AI_BASE_URL` 优先级更高
- ✅ 推荐迁移到新的环境变量名称

## 代码变更

**文件：** `scripts/siliconflow_client.py`

**修改前：**
```python
self.api_base = os.getenv("ECHO_EPUB_API_BASE", self.DEFAULT_API_BASE)
```

**修改后：**
```python
# Use ECHO_EPUB_OPEN_AI_BASE_URL, fall back to ECHO_EPUB_API_BASE for backward compatibility
self.api_base = os.getenv("ECHO_EPUB_OPEN_AI_BASE_URL") or os.getenv("ECHO_EPUB_API_BASE", self.DEFAULT_API_BASE)
```

## 优势

1. **灵活性** - 支持任何 OpenAI 兼容的 API 端点
2. **可移植性** - 可以轻松切换不同的 API 提供商
3. **本地化** - 支持本地模型服务（如 Ollama）
4. **成本优化** - 可以选择成本更低的替代服务

## 测试

测试不同配置：

```bash
# 测试 1：使用默认配置
export ECHO_EPUB_OPEN_API_KEY='test-key'
python scripts/main.py "test.epub" --no-translation

# 测试 2：使用自定义端点
export ECHO_EPUB_OPEN_AI_BASE_URL='https://custom.api.com/v1'
export ECHO_EPUB_OPEN_API_KEY='test-key'
python scripts/main.py "test.epub" --no-translation

# 测试 3：使用旧环境变量（向后兼容）
export ECHO_EPUB_API_BASE='https://old.api.com/v1'
export ECHO_EPUB_OPEN_API_KEY='test-key'
python scripts/main.py "test.epub" --no-translation
```

## 更新日期

2025-02-02
