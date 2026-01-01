
import asyncio
import base64
import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from slidemaker.llm.adapters.api.vertex_gemini import VertexGeminiAdapter

async def evaluate_comparison(image_path: str, label: str):
    project_id = os.environ.get("GOOGLE_CLOUD_PROJECT")
    adapter = VertexGeminiAdapter(
        model="gemini-3-pro-image-preview",
        project_id=project_id,
        location="global",
        api_version="v1beta1",
        use_global_endpoint=True,
    )
    
    print(f"\nEvaluating {label}...")
    
    with open(image_path, "rb") as f:
        image_data = base64.b64encode(f.read()).decode("utf-8")
        
    prompt = """
    Compare the 'Original PDF' (left) and 'Generated PPTX' (right) in this image.
    Identify any discrepancies in:
    1. **Font Size**: Is the text in PPTX significantly larger or smaller?
    2. **Layout**: Are elements aligned correctly? Are text boxes overflowing?
    3. **Images**: Are images cut off (cropped)? Is there double text (ghosting)?
    4. **Z-Order**: Is text hidden behind images?
    
    Provide a score from 1 to 10 (10 is perfect match) and a brief summary of issues.
    """
    
    try:
        response = await adapter.generate_text(prompt, image_data=image_data)
        print(response)
        return response
    except Exception as e:
        print(f"Error: {e}")
        return str(e)

async def main():
    report = "# Self-Evaluation Report\n\n"
    
    slides = ["Slide 1", "Slide 2", "Slide 3"]
    for label in slides:
        path = f"output/reports/comparisons_v9/compare_{label.replace(' ', '_')}.png"
        if os.path.exists(path):
            evaluation = await evaluate_comparison(path, label)
            report += f"## {label}\n\n{evaluation}\n\n"
            
    with open("output/reports/self_evaluation_v9.md", "w") as f:
        f.write(report)
    print("\nReport saved to output/reports/self_evaluation_v9.md")

if __name__ == "__main__":
    asyncio.run(main())
