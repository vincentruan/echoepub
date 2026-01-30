---
name: audioread-epub-generator
description: End-to-end audiobook-optimized EPUB generator. Reads EPUB/PDF/Markdown files or folders, converts to audiobook-friendly Chinese EPUB with image descriptions, translations, and TTS-optimized formatting. Use when creating or converting ebooks for audio reading/listening.
---

# Audio-Optimized EPUB Generator

Transform EPUB, PDF, or Markdown files into audiobook-friendly EPUB ebooks optimized for TTS reading. Core differentiation: all content is converted to spoken-friendly formats with image descriptions, translations, and structural adaptations for listening.

## Input Support

| Format | Parser Used | Notes |
|---------|--------------|-------|
| EPUB | `epub` skill | Extracts chapters, text, images |
| PDF | `pdf-to-markdown-converter` skill | Converts to markdown with image markers |
| Markdown | Direct processing | No parsing needed |
| Folder | Multi-format | Processes each file by type, combines |

## Default Processing Strategy

Apply these defaults unless user specifies otherwise:

- **Language**: Simplified Chinese (zh-CN)
- **Reading style**: Clear, natural, moderately conversational; shorter sentences, clearer paragraphs
- **Chapter structure**: Preserve original hierarchy; add optional chapter intro/summary
- **Images/Charts**: Generate readable descriptions (see [Image Description Rules](#image-description-rules))
- **Translation**: Translate only full sentences/paragraphs clearly non-Chinese (English, Japanese, etc.); preserve embedded English terms, acronyms, code, variable names
- **Terminology protection**: Build glossary for frequent terms; add Chinese explanation on first occurrence
- **Tables**: Convert to "readable summary + key points narration"; avoid large tables unless small
- **Code**: Keep but fold to "oral explanation + key snippets"; long code to "Appendix: Code/References"

## File/Chapter Ordering (Critical)

For multi-file or folder inputs, determine reading order by priority:

1. **Index files first**: README, index, toc, 目录, contents, SUMMARY, _sidebar, _toc, nav, catalog (any extension)
2. **Use explicit order**: If SUMMARY.md or explicit catalog exists, follow that order exactly
3. **Natural sort**: Sort by filename (handle numeric prefixes: 01, 1, 001), recursive for subdirectories
4. **Deduplication**: If duplicate chapters exist, prefer longer/newer/complete version; log in processing report

## Workflow

### Phase A: Input Recognition and Extraction

1. Identify input type: EPUB / PDF / MD / Folder
2. Execute parsing:
   - **EPUB** -> Call `epub` skill: extract chapters, text, image references
   - **PDF** -> Call `pdf-to-markdown-converter` skill: convert to markdown, preserve chapter hierarchy, mark images with placeholders (include page hints if possible)
   - **Markdown** -> Direct to intermediate layer
   - **Folder** -> Iterate each file, apply respective parser, merge into unified intermediate layer
3. Normalize to "markdown intermediate layer":
   - Preserve heading hierarchy (# / ## / ###)
   - Preserve lists, blockquotes, footnotes (where possible)
   - Standardize images: `![](path)` or `[FIGURE: source=xxx page=12 id=3]`
   - Build resource manifest and chapter mapping for later description insertion

### Phase B: Chapter-Level Processing

4. Split intermediate markdown into chapter-level files (one md per chapter)
5. Execute "chapter processor" subtask on each (can be parallelized):

   - Correct typos and obvious formatting errors
   - Below each image/chart, add "readable description paragraph"
   - For charts with key information, add "key points summary (3-7 items)"
   - For flowcharts/architecture/contrast diagrams, add "structured narration" (overview then details)
   - Translate clearly non-Chinese paragraphs (follow [Translation Rules](#translation-rules-strict))
   - Preserve original meaning; do not add/delete conclusions; add "Translator's note:" for clarifications (brief)

### Phase C: Audiobook-Mode Rewrite (Key Differentiation)

6. Secondary "speech-friendly" processing on chapter-processed md:

   - **Sentence length**: Split long sentences; rewrite nested brackets for easier listening order
   - **Lists**: Convert to "point-by-point narration" format (e.g., "First... second... third...")
   - **Tables**: Convert to "state table theme -> describe dimensions -> narrate key values/conclusions"
   - **Quotes**: Keep content, add "quote begins/ends" markers (brief)
   - **Chart references**: When text says "see below/see figure", add "Please note: following is oral description of Figure X..."
   - **Chapter start**: Add 2-4 sentences "chapter intro"
   - **Chapter end**: Add 2-6 sentences "chapter summary/review"
   - Maintain heading hierarchy (H1/H2/H3) for EPUB TOC and listening segments

7. Generate "Glossary/Abbreviation Table" if frequent terms exist:
   - Only include high-frequency, important terms
   - Format: Term (original) — Chinese explanation (notes if needed)

### Phase D: Merge and Package

8. Merge processed chapter md by [ordering rules](#filechapter-ordering-critical), generate final EPUB:
   - metadata: title/author/language(zh-CN)/identifier/date
   - toc: Based on heading hierarchy
   - cover: Generate AI cover (style: clean, suitable for listening; include title and author; abstract graphics only; no clutter)
   - styling: Better for reading/listening (larger line-height, paragraph spacing, clear heading hierarchy)

9. Output processing report (required):
   - Input type and file list
   - Final chapter order and rationale
   - Translation rules and terminology protection strategy
   - Image description strategy (how generated, where key points added)
   - Audiobook rewrites done (sentence splits, list narration, table conversion, etc.)
   - Known limitations (e.g., blurry images causing incomplete descriptions; PDF lacking TOC causing inference issues)

## Translation Rules (Strict)

- Translate only "full sentence/paragraph clearly non-Chinese" content (English, Japanese, etc.)
- **Do not translate** or only explain on first occurrence:
  - Proper nouns, product names, company names, person names, standard numbers, protocol names (RFC/ISO/IEEE)
  - Acronyms/initialisms (GPU/LLM/TTS)
  - Code, variable names, function names, command lines, paths, URLs, citation formats
  - Small English embedded in Chinese (e.g., "this API's latency is low"), keep as-is or minor smoothing
- If translation needed with multiple variants, prefer industry standard; log in glossary

## Image Description Rules (Must be Readable)

For each image/chart, generate at least:

1. One-sentence description of what it is (e.g., line chart/bar chart/flowchart/architecture diagram/screenshot)
2. Core conclusion it expresses (1-2 sentences)
3. Key elements narration:
   - **Charts**: X-axis/Y-axis meaning, trends, peaks/inflection points, comparison items
   - **Flowcharts**: Start -> steps -> branch conditions -> end
   - **Architecture diagrams**: Components -> relationships -> data flow direction
4. Key points summary (3-7 items, short sentences)
5. If uncertain (e.g., blurry image), state "details uncertain" to avoid fabrication

## Quality Thresholds (Self-check Before Output)

- **TOC usable**: Chapter hierarchy correct, TOC navigable
- **Speech-friendly**: Long sentences reduced; lists/tables converted to narratable structure
- **Translation consistent**: Non-Chinese paragraphs translated; terms not mistranslated
- **Images complete**: Every image/chart has readable description + key points (where needed)
- **No fabrication**: Do not add facts/data/conclusions not in original; explanations are "for understanding only", use "explanation/interpretation" phrasing to distinguish

## Interaction Principles

- Minimize questions: Unless critical metadata missing (e.g., title completely unknown), proceed with defaults
- Prioritize user preferences: When user specifies style (more conversational/more formal/shorter/longer), honor it
- Auto-decision for multi-file: If order unclear, auto-determine by rules, document rationale in processing report

## Failure and Degradation Strategies

- **EPUB/PDF parsing failure**: Output available markdown合集 + processing report; note failure reason, preserve successful parts
- **Image unparseable**: Still output structured description, mark "details uncertain"
- **Non-content folders** (build, node_modules): Auto-ignore common irrelevant directories and binaries; only process actual content

## Final Deliverable

- Return: Final EPUB + Processing Report
- Ensure content "suitable for listening", not just "suitable for reading"

## Implementation Notes

This skill is self-contained: does NOT depend on `markdown-to-epub` or `ebook-processor` skills at runtime. Required capabilities are internalized:

- EPUB generation logic (ebooklib-based) -> in `scripts/epub_generator.py`
- Markdown parsing and HTML conversion -> in `scripts/markdown_processor.py`
- Cover generation (AI) -> in `scripts/cover_generator.py`
- Image format conversion -> in `scripts/convert_images.py`
- Text optimization rules -> in `scripts/text_optimizer.py`
- Audio-specific rewrite patterns -> in `scripts/audio_rewriter.py`

### Key Scripts

| Script | Purpose |
|---------|-----------|
| `epub_generator.py` | EPUB file creation with metadata, TOC, styling |
| `markdown_processor.py` | Markdown parsing to chapter structure, HTML conversion |
| `cover_generator.py` | AI book cover generation (SiliconFlow API) |
| `convert_images.py` | Image format normalization (webp/gif/bmp -> jpg) |
| `text_optimizer.py` | Typo detection, formatting rules |
| `audio_rewriter.py` | Speech-friendly transformations (new for this skill) |

### Dependency Requirements

```bash
pip install ebooklib Pillow PyMuPDF requests
```

Optional for syntax highlighting:
```bash
pip install pygments
```

For AI cover generation, set:
```bash
export SILICONFLOW_API_KEY=your_api_key
```
