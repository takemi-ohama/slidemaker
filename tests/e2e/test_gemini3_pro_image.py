#!/usr/bin/env python3
"""Test Gemini 3 Pro Image Preview model with v1beta1 API."""

import asyncio
import base64
import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from slidemaker.llm.adapters.api.vertex_gemini import VertexGeminiAdapter


async def test_gemini3_pro_image_text():
    """Test Gemini 3 Pro Image Preview for text generation."""
    print("\n" + "=" * 80)
    print("Testing Gemini 3 Pro Image Preview (text) with v1beta1 API...")
    print("=" * 80)

    project_id = os.environ.get("GOOGLE_CLOUD_PROJECT")
    if not project_id:
        print("ERROR: GOOGLE_CLOUD_PROJECT environment variable not set")
        return False

    try:
        adapter = VertexGeminiAdapter(
            model="gemini-3-pro-image-preview",
            timeout=300,
            project_id=project_id,
            location="global",
            api_version="v1beta1",
            use_global_endpoint=True,
            max_tokens=512,
            temperature=0.7,
        )

        print(f"Project ID: {project_id}")
        print(f"Model: gemini-3-pro-image-preview")
        print(f"Location: global")
        print(f"API Version: v1beta1")
        print(f"Global Endpoint: {adapter.use_global_endpoint}")
        print(f"API URL: {adapter.api_base_url}")
        print()

        prompt = "What is 2+2? Answer in one sentence."
        print(f"Prompt: {prompt}")
        print("\nGenerating response...")

        response = await adapter.generate_text(prompt)

        print("\n✅ SUCCESS!")
        print(f"Response: {response[:200]}...")
        return True

    except Exception as e:
        print(f"\n❌ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_gemini3_pro_image_vision():
    """Test Gemini 3 Pro Image Preview for image analysis."""
    print("\n" + "=" * 80)
    print("Testing Gemini 3 Pro Image Preview (vision) with v1beta1 API...")
    print("=" * 80)

    project_id = os.environ.get("GOOGLE_CLOUD_PROJECT")
    if not project_id:
        print("ERROR: GOOGLE_CLOUD_PROJECT environment variable not set")
        return False

    try:
        adapter = VertexGeminiAdapter(
            model="gemini-3-pro-image-preview",
            timeout=300,
            project_id=project_id,
            location="global",
            api_version="v1beta1",
            use_global_endpoint=True,
            max_tokens=512,
            temperature=0.3,
        )

        print(f"Project ID: {project_id}")
        print(f"Model: gemini-3-pro-image-preview")
        print(f"Location: global")
        print(f"API Version: v1beta1")
        print(f"Global Endpoint: {adapter.use_global_endpoint}")
        print(f"API URL: {adapter.api_base_url}")
        print()

        # Create a simple test image (100x100 red square)
        import io
        from PIL import Image

        img = Image.new('RGB', (100, 100), color='red')
        img_buffer = io.BytesIO()
        img.save(img_buffer, format='PNG')
        img_data = base64.b64encode(img_buffer.getvalue()).decode('utf-8')

        prompt = "What color is this image? Answer in one word."
        print(f"Prompt: {prompt}")
        print("Image: 100x100 red square")
        print("\nGenerating response...")

        response = await adapter.generate_text(
            prompt,
            image_data=img_data
        )

        print("\n✅ SUCCESS!")
        print(f"Response: {response[:200]}...")
        return True

    except Exception as e:
        print(f"\n❌ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all tests."""
    print("\n" + "=" * 80)
    print("Gemini 3 Pro Image Preview Test Suite (v1beta1 API)")
    print("=" * 80)

    results = []

    # Test text model
    results.append(("Gemini 3 Pro Image Preview (text)", await test_gemini3_pro_image_text()))

    # Test image model
    results.append(("Gemini 3 Pro Image Preview (vision)", await test_gemini3_pro_image_vision()))

    # Summary
    print("\n" + "=" * 80)
    print("Test Summary")
    print("=" * 80)

    for name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {name}")

    all_passed = all(success for _, success in results)

    print("\n" + "=" * 80)
    if all_passed:
        print("🎉 All tests passed! Gemini 3 Pro Image Preview is working with v1beta1 API.")
    else:
        print("⚠️  Some tests failed. Check the error messages above.")
    print("=" * 80)

    return 0 if all_passed else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
