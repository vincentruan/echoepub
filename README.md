# Audio-Optimized EPUB Generator

> Transform EPUB, PDF, and Markdown files into audiobook-friendly EPUB ebooks with AI-powered image descriptions, smart translation, and TTS-optimized formatting.

[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

## 🌟 Overview

**Audio-Optimized EPUB Generator** is an end-to-end processing pipeline that converts ebooks and documents into audiobook-friendly EPUB files. It extracts content from multiple formats, enhances it with AI-generated image descriptions, translates non-Chinese content while preserving technical terms, and optimizes the structure for text-to-speech (TTS) playback.

### Key Differentiators

- **AI-Powered Image Analysis** - Uses VLM (Vision Language Model) to generate structured, audio-friendly descriptions for charts, diagrams, and screenshots
- **Smart Translation** - Detects and protects 40+ technical terms (GPU, API, LLM, etc.) during translation
- **TTS Optimization** - Converts long sentences, tables, and lists into natural speech patterns
- **Format Agnostic** - Supports EPUB, PDF, Markdown, and multi-file folders as input

## ✨ Features

### 📖 Content Enhancement

- **Image Description** - Automatically analyzes images and generates structured descriptions:
  - Chart type classification (line, bar, pie, flowchart, architecture, etc.)
  - Core conclusion extraction
  - Key elements narration
  - 3-7 bullet points for audio playback

- **Smart Translation** - Translates non-Chinese content with:
  - Automatic technical term detection (40+ terms)
  - Term density analysis to avoid unnecessary translation
  - Batch processing optimization
  - Graceful fallback when API unavailable

- **Audiobook Optimization** - Rephrases content for listening:
  - Splits long sentences
  - Converts tables to narratable format
  - Transforms lists to "point-by-point narration"
  - Adds chapter intros and summaries

### 🔧 Input Support

| Format | Status | Notes |
|--------|--------|-------|
| **EPUB** | ✅ Native | Extracts chapters, text, images with metadata |
| **PDF** | ✅ Supported | Converts to markdown, preserves hierarchy |
| **Markdown** | ✅ Supported | Direct processing |
| **Folder** | ✅ Supported | Multi-format processing with auto-ordering |

### 🌍 Translation & Localization

- **Target Language**: Simplified Chinese (zh-CN)
- **Source Languages**: English, Japanese, and other non-Chinese content
- **Term Preservation**: GPU, API, LLM, GPT, Claude, frameworks, protocols, etc.
- **Intelligent Detection**: Skips content with high technical term density (>15%)

## 🚀 Quick Start

### Installation

```bash
# Clone repository
git clone https://github.com/yourusername/echoepub.git
cd echoepub

# Install dependencies
pip install -r requirements.txt
```

### Basic Usage

```bash
# Set API key (required for translation and image analysis)
export ECHO_EPUB_OPEN_API_KEY='your-api-key-here'

# Process an EPUB file
python .claude/skills/audioread-epub-generator/scripts/main.py \
  "books/input.epub"

# Process a PDF
python .claude/skills/audioread-epub-generator/scripts/main.py \
  "documents/paper.pdf"

# Process with options
python .claude/skills/audioread-epub-generator/scripts/main.py \
  "books/input.epub" \
  "output/book_audio.epub" \
  --style conversational
```

### Output

- **EPUB File**: `books/input_audio.epub`
- **Processing Report**: `books/input_audio_report.md`

## ⚙️ Configuration

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `ECHO_EPUB_OPEN_API_KEY` | ✅ Yes | - | API key for translation and image analysis |
| `ECHO_EPUB_OPEN_AI_BASE_URL` | ❌ No | `https://api.siliconflow.cn/v1` | OpenAI-compatible API base URL |
| `ECHO_EPUB_TRANSLATE_MODEL` | ❌ No | `MiniMaxAI/MiniMax-M2` | Translation model name |
| `ECHO_EPUB_VLM_MODEL` | ❌ No | `PaddlePaddle/PaddleOCR-VL-1.5` | Image analysis model name |

### API Providers

The skill supports any OpenAI-compatible API:

```bash
# SiliconFlow (default)
export ECHO_EPUB_OPEN_AI_BASE_URL='https://api.siliconflow.cn/v1'

# OpenAI
export ECHO_EPUB_OPEN_AI_BASE_URL='https://api.openai.com/v1'
export ECHO_EPUB_TRANSLATE_MODEL='gpt-4o'

# Local Ollama
export ECHO_EPUB_OPEN_AI_BASE_URL='http://localhost:11434/v1'
export ECHO_EPUB_TRANSLATE_MODEL='llama3.1'

# Azure OpenAI
export ECHO_EPUB_OPEN_AI_BASE_URL='https://your-resource.openai.azure.com/...'
```

## 📊 Processing Pipeline

### Phase A: Input Recognition

1. Identify input type (EPUB/PDF/Markdown/Folder)
2. Extract content and structure
3. Normalize to markdown intermediate layer

### Phase B: Content Enhancement

4. Detect and extract technical terms
5. Translate non-Chinese paragraphs (preserving terms)
6. Generate AI-powered image descriptions
7. Add chapter intros and summaries

### Phase C: Audiobook Optimization

8. Split long sentences
9. Convert tables and lists to narratable format
10. Optimize heading hierarchy for TTS

### Phase D: EPUB Generation

11. Merge processed content
12. Generate final EPUB with metadata and TOC
13. Create processing report

## 📝 Image Description Format

All images receive structured descriptions:

```
> **图片说明**：This is a [chart type].
> 核心结论是：[Main conclusion in 1-2 sentences]
> 关键元素包括：[Key visual elements]
> 要点总结：
> - 第一，[Key insight 1]
> - 第二，[Key insight 2]
> - 第三，[Key insight 3]
> - 第四，[Key insight 4]
> - 第五，[Key insight 5]
```

### Supported Image Types

- **Charts** - Line, bar, pie, scatter plots with axes and trends
- **Flowcharts** - Process flows with steps and branches
- **Architecture Diagrams** - System components and relationships
- **Screenshots** - UI interfaces and key fields
- **Tables** - Data summaries with key insights

## 🛡️ Technical Term Protection

### Detected Categories

- **Acronyms**: GPU, CPU, LLM, API, HTTP, JSON, etc.
- **Model Names**: GPT-4, Claude, Llama, BERT, Mistral, etc.
- **Frameworks**: TensorFlow, PyTorch, React, Django, etc.
- **Languages**: Python, JavaScript, Go, Rust, etc.
- **Protocols**: HTTP, HTTPS, TCP, IP, DNS, SSL, etc.

### Translation Logic

```
IF Chinese ratio >= 30%:
    SKIP (already Chinese)
ELSE IF Technical term density > 15%:
    SKIP (preserve technical content)
ELSE IF Technical term density > 5% AND Chinese < 15%:
    TRANSLATE with term preservation
ELSE:
    Standard translation
```

## 📈 Performance

### Test Results

Tested on `架构师之路（58沈剑）.epub`:

| Metric | Result |
|--------|--------|
| Total Images | 914 |
| Images with Descriptions | 456 (100%) |
| Translated Paragraphs | 206 |
| Sentences Split | 693 |
| Image Warnings | 0 |
| Processing Time | ~2 minutes |

### Improvements

| Issue | Before | After | Improvement |
|-------|--------|-------|-------------|
| Image not found | 458 warnings | 0 warnings | ✅ 100% fixed |
| Translation count | 234 | 206 | ✅ 12% reduction |
| Image descriptions | Placeholders | AI-generated | ✅ Real analysis |
| Context usage | Large | Small | ✅ API-based |

## 🔍 Advanced Usage

### Disable Translation

```bash
python scripts/main.py "input.epub" --no-translation
```

### Custom Reading Style

```bash
# More conversational
python scripts/main.py "input.epub" --style conversational

# More formal
python scripts/main.py "input.epub" --style formal
```

### Custom Output Path

```bash
python scripts/main.py "input.epub" "custom_output.epub"
```

### Processing Folders

```bash
# Process all files in a folder
python scripts/main.py "documents/chapter1/"
```

## 🧪 Testing

### Run Test Suite

```bash
cd .claude/skills/audioread-epub-generator/scripts

# Test API integration
python test_api_integration.py

# Test with sample file
python main.py "test.epub" --no-translation
```

## 📚 Documentation

- **[API_USAGE.md](.claude/skills/audioread-epub-generator/API_USAGE.md)** - API integration guide
- **[UPDATE_SUMMARY.md](.claude/skills/audioread-epub-generator/UPDATE_SUMMARY.md)** - Update summary
- **[ENV_VAR_UPDATE.md](.claude/skills/audioread-epub-generator/ENV_VAR_UPDATE.md)** - Environment variable updates

## 🔧 Development

### Project Structure

```
echoepub/
├── .claude/skills/audioread-epub-generator/
│   ├── scripts/
│   │   ├── main.py                    # Main entry point
│   │   ├── epub_extractor.py          # EPUB content extraction
│   │   ├── siliconflow_client.py     # API client
│   │   ├── translate_content.py       # Translation module
│   │   ├── technical_term_detector.py # Term detection
│   │   ├── image_descriptor.py        # Image analysis
│   │   ├── markdown_processor.py      # Markdown processing
│   │   ├── epub_generator.py          # EPUB generation
│   │   ├── audio_rewriter.py          # TTS optimization
│   │   └── test_api_integration.py    # Test suite
│   ├── references/
│   │   └── image_description_rules.md
│   └── SKILL.md
├── books/                            # Input/output directory
└── CLAUDE.md                         # Project overview
```

### Key Scripts

| Script | Purpose |
|--------|---------|
| `main.py` | CLI entry point, orchestrates pipeline |
| `epub_extractor.py` | Extracts content from EPUB files |
| `siliconflow_client.py` | Handles API calls for translation and VLM |
| `technical_term_detector.py` | Detects and protects technical terms |
| `image_descriptor.py` | Generates AI-powered image descriptions |
| `translate_content.py` | Manages translation workflow |
| `epub_generator.py` | Creates final EPUB with metadata |
| `audio_rewriter.py` | Optimizes content for TTS playback |

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

MIT License - see LICENSE file for details

## 🙏 Acknowledgments

- **SiliconFlow** - API platform for translation and image analysis
- **ebooklib** - EPUB file generation
- **PyMuPDF** - PDF content extraction
- **html2text** - HTML to Markdown conversion

## 📞 Support

For issues, questions, or suggestions:

1. Check the [API_USAGE.md](.claude/skills/audioread-epub-generator/API_USAGE.md)
2. Review the [UPDATE_SUMMARY.md](.claude/skills/audioread-epub-generator/UPDATE_SUMMARY.md)
3. Open an issue on GitHub

---

**Made with ❤️ for audiobook enthusiasts**
