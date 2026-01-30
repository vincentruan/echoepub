# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This project (echoepub) reads epub, pdf, and markdown files and regenerates new epub files optimized for audiobook-style reading. Key features include:

- Extracting and adding text explanations for images, charts, and other visual content
- Translating non-Chinese content (English, Japanese, etc.) to Chinese
- Generating EPUB files with improved accessibility for audio-based consumption

## Architecture Notes

The codebase is organized around a document processing pipeline:

1. **Input Parsing** - Modules for reading different source formats (epub, pdf, markdown)
2. **Content Enhancement** - Services for image analysis, chart description generation, and translation
3. **EPUB Generation** - Creating the enhanced EPUB output

When working with this codebase, understand that:
- The core transformation pipeline applies the same enhancement logic regardless of input format
- Image analysis and translation are separate concerns that can be toggled or configured
- Output EPUB structure maintains original content hierarchy while adding new explanatory sections

## Development Commands

*Commands will be added here once the project is initialized.*
