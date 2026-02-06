# Translation Rules Reference

## Core Principle

Translate only "full sentences or paragraphs that are clearly non-Chinese". Preserve embedded English terms, acronyms, code, and technical notations.

## What to Translate

### DO Translate

- Complete paragraphs in English, Japanese, Korean, etc.
- Stand-alone sentences not in Chinese
- Full foreign language sections

Example:
```
Original:
This is a complete paragraph in English that should be translated.

Translated:
这是一个完整的英文段落，应该被翻译。
```

## What NOT to Translate

### DO NOT Translate

1. **Proper nouns and product names**
   - Company names: Apple, Google, Tesla
   - Product names: iPhone, ChatGPT, YouTube
   - Person names: John Smith, Einstein

2. **Acronyms and initialisms**
   - GPU, CPU, AI, LLM, TTS
   - HTTP, API, SDK, JSON

3. **Code elements**
   - Variable names: `user_name`, `data_list`
   - Function names: `calculate_total()`, `save_file()`
   - Class names: `UserSession`, `DataProcessor`
   - Command line: `pip install`, `npm start`
   - File paths: `/usr/local/bin`, `C:\Program Files`
   - URLs: `https://example.com`

4. **Technical notations**
   - RFC standards: RFC 2119, RFC 8259
   - Protocol names: HTTP/2, WebSocket, TCP/IP
   - Standard codes: HTTP 404, ISO 9001

5. **Embedded English in Chinese**

Example (keep as-is):
```
这个 API 的 latency 很低，响应速度很快。
```

Minor smoothing is acceptable if it improves flow:
```
这个 API 的延迟（latency）很低，响应速度很快。
```

## First Occurrence Exception

On first occurrence of a term, you may add a brief explanation in parentheses:

Example:
```
第一次提到：
我们使用 GPU（图形处理器）来加速计算。

后续使用：
我们使用 GPU 来加速计算。
```

## Multiple Translation Variants

When a term has multiple valid translations:
1. Prefer industry-standard translation
2. Log -> chosen translation in glossary
3. Maintain consistency throughout document

Example:
```
"Machine Learning" -> "机器学习" (not "学习机器")
"Artificial Intelligence" -> "人工智能" (not "人造智能")
```

## Code Block Handling

Never translate code blocks, even if they contain strings:

```
# Do NOT translate this
def calculate_score(user_data):
    return len(user_data.items)
```

Only translate comments if they are in a foreign language:

```
def calculate_score(user_data):
    # Calculate total number of items  -> 计算项目总数
    return len(user_data.items)
```

## Glossary Maintenance

For each translation decision, record:

| Term (Original) | Translation | Note |
|------------------|------------|-------|
| Machine Learning | 机器学习 | Industry standard |
| Deep Learning | 深度学习 | Industry standard |

This ensures consistency across -> entire document.
