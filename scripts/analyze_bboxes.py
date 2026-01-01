
import asyncio
import base64
import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from slidemaker.llm.adapters.api.vertex_gemini import VertexGeminiAdapter
from slidemaker.utils.validation import validate_gcp_project_id, validate_file_path

async def analyze_image_bbox(image_path: str, page_num: int):
    # セキュリティ: GCPプロジェクトIDの検証（CWE-20）
    project_id = validate_gcp_project_id(os.environ.get("GOOGLE_CLOUD_PROJECT"))

    adapter = VertexGeminiAdapter(
        model="gemini-3-pro-image-preview",
        project_id=project_id,
        location="global",
        api_version="v1beta1",
        use_global_endpoint=True,
    )

    print(f"\nAnalyzing {image_path} (Page {page_num})...")

    # セキュリティ: ファイルパスの検証（CWE-22: Path Traversal対策）
    allowed_dir = Path(__file__).parent.parent / "output" / "temp" / "pdf_pages"
    validated_path = validate_file_path(
        image_path,
        allowed_dir=allowed_dir,
        must_exist=True,
        must_be_file=True,
    )

    with open(validated_path, "rb") as f:
        image_data = base64.b64encode(f.read()).decode("utf-8")
        
    prompt = """
    Analyze this slide image (960x540 pixels).
    Identify the main image/icon/diagram elements.
    For each element, provide the EXACT bounding box in PIXELS [ymin, xmin, ymax, xmax].
    
    CRITICAL: Ensure the bounding box includes ALL parts of the graphic, including shadows, reflections, and labels if they are visually part of the graphic.
    
    Output JSON format:
    {
      "elements": [
        {"description": "...", "bbox": [ymin, xmin, ymax, xmax]}
      ]
    }
    """
    
    try:
        response = await adapter.generate_structured(prompt, image_data=image_data)
        print(response)
        return response
    except Exception as e:
        print(f"Error: {e}")
        return None

async def main():
    await analyze_image_bbox("output/temp/pdf_pages/page_002.png", 2)
    await analyze_image_bbox("output/temp/pdf_pages/page_003.png", 3)

if __name__ == "__main__":
    asyncio.run(main())
