#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script for SiliconFlow API integration

Tests translation and image analysis APIs.
"""

import os
import sys
from pathlib import Path

# Add scripts directory to path
script_dir = Path(__file__).parent
sys.path.insert(0, str(script_dir))


def test_translation_api():
    """Test translation API."""
    print("=" * 60)
    print("Testing Translation API")
    print("=" * 60)

    # Check for API key
    api_key = os.getenv("ECHO_EPUB_OPEN_API_KEY")
    if not api_key:
        print("\n❌ ECHO_EPUB_OPEN_API_KEY not set")
        print("\nTo set the API key:")
        print("  export ECHO_EPUB_OPEN_API_KEY='your-api-key-here'")
        print("\nSkipping translation test...")
        return False

    try:
        from siliconflow_client import get_siliconflow_client
        from technical_term_detector import TechnicalTermDetector

        client = get_siliconflow_client()
        detector = TechnicalTermDetector()

        # Test text with technical terms
        test_text = "This paper introduces CodeAct, a novel approach that uses executable code actions to elicit better LLM agents. The method combines GPT-4 with Python code execution."

        # Extract terms
        terms = detector.extract_terms(test_text)
        print(f"\n📝 Detected technical terms: {', '.join(list(terms.keys())[:10])}")

        # Translate
        print(f"\n🔤 Translating...")
        print(f"Original: {test_text}")

        translated = client.translate_text(
            test_text,
            preserve_terms=list(terms.keys())
        )

        print(f"\n✅ Translation result: {translated}")
        return True

    except Exception as e:
        print(f"\n❌ Translation test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_vlm_api():
    """Test VLM API for image analysis."""
    print("\n" + "=" * 60)
    print("Testing VLM API for Image Analysis")
    print("=" * 60)

    # Check for API key
    api_key = os.getenv("ECHO_EPUB_OPEN_API_KEY")
    if not api_key:
        print("\n❌ ECHO_EPUB_OPEN_API_KEY not set")
        print("Skipping VLM test...")
        return False

    # Find a test image
    test_image = None

    # Try to find an image from the books directory
    books_dir = Path(__file__).parent.parent.parent.parent / "books"
    if books_dir.exists():
        # Look for any image file
        for ext in ['*.png', '*.jpg', '*.jpeg']:
            images = list(books_dir.rglob(ext))
            if images:
                test_image = images[0]
                break

    if not test_image:
        print("\n❌ No test image found")
        print("Please provide a path to an image file")
        return False

    try:
        from siliconflow_client import get_siliconflow_client

        client = get_siliconflow_client()

        print(f"\n🖼️  Analyzing image: {test_image.name}")

        description = client.analyze_image(
            str(test_image),
            context="This is a test image from an academic paper.",
            image_type="general"
        )

        if description:
            print(f"\n✅ Image analysis result:")
            print(description)
            return True
        else:
            print("\n❌ No description returned")
            return False

    except Exception as e:
        print(f"\n❌ VLM test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_fallback():
    """Test fallback behavior when API is not available."""
    print("\n" + "=" * 60)
    print("Testing Fallback Behavior")
    print("=" * 60)

    # Temporarily unset API key
    original_key = os.environ.get("ECHO_EPUB_OPEN_API_KEY")
    if original_key:
        del os.environ["ECHO_EPUB_OPEN_API_KEY"]

    try:
        from translate_content import translate_with_api
        from image_descriptor import ImageDescriptor

        # Test translation fallback
        print("\n📝 Testing translation fallback...")
        test_paragraphs = [
            {"text": "This is a test paragraph with technical terms like GPU and API.", "line_num": 1}
        ]

        translations, success = translate_with_api(test_paragraphs)

        if not success:
            print("✅ Translation fallback working (API not available)")
        else:
            print("⚠️  Translation succeeded unexpectedly")

        # Test image descriptor fallback
        print("\n🖼️  Testing image descriptor fallback...")
        descriptor = ImageDescriptor()

        # Create a fake image path
        fake_path = "/tmp/nonexistent.jpg"

        # This should return placeholder
        description = descriptor.describe_image_with_vision_model(
            fake_path,
            use_vlm_api=True
        )

        if description and "图片说明" in description:
            print("✅ Image descriptor fallback working (placeholder generated)")
        else:
            print("⚠️  Image descriptor fallback unexpected")

        return True

    except Exception as e:
        print(f"\n❌ Fallback test failed: {e}")
        return False

    finally:
        # Restore API key
        if original_key:
            os.environ["ECHO_EPUB_OPEN_API_KEY"] = original_key


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("SiliconFlow API Integration Test Suite")
    print("=" * 60)

    # Check if API key is set
    api_key = os.getenv("ECHO_EPUB_OPEN_API_KEY")
    if api_key:
        print(f"\n✅ ECHO_EPUB_OPEN_API_KEY is set (length: {len(api_key)})")
    else:
        print(f"\n⚠️  ECHO_EPUB_OPEN_API_KEY not set")

    # Run tests
    results = {}

    if api_key:
        results["translation"] = test_translation_api()
        results["vlm"] = test_vlm_api()

    results["fallback"] = test_fallback()

    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)

    for test_name, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name.upper()}: {status}")

    all_passed = all(results.values())
    if all_passed:
        print("\n🎉 All tests passed!")
    else:
        print("\n⚠️  Some tests failed")

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
