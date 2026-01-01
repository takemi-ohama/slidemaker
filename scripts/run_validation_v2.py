
import asyncio
import base64
import os
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from slidemaker.llm.adapters.api.vertex_gemini import VertexGeminiAdapter

def create_comparison(original_path, generated_path, output_path, label):
    try:
        if not os.path.exists(original_path):
            print(f"Missing original: {original_path}")
            return False
        if not os.path.exists(generated_path):
            print(f"Missing generated: {generated_path}")
            return False

        img1 = Image.open(original_path)
        img2 = Image.open(generated_path)
        
        # Resize img2 to match img1 height if necessary, maintaining aspect ratio
        if img1.size != img2.size:
            # print(f"Resizing {generated_path} from {img2.size} to {img1.size}")
            img2 = img2.resize(img1.size, Image.Resampling.LANCZOS)

        # Create a new image with side-by-side placement
        total_width = img1.width + img2.width
        max_height = max(img1.height, img2.height) + 50 # Add space for labels
        
        new_im = Image.new('RGB', (total_width, max_height), color='white')
        
        # Paste images
        new_im.paste(img1, (0, 50))
        new_im.paste(img2, (img1.width, 50))
        
        # Add labels
        draw = ImageDraw.Draw(new_im)
        try:
            font = ImageFont.truetype("Arial.ttf", 24)
        except IOError:
            font = ImageFont.load_default()
            
        draw.text((10, 10), f"Original PDF ({label})", fill="black", font=font)
        draw.text((img1.width + 10, 10), f"Generated PPTX ({label})", fill="black", font=font)
        
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        new_im.save(output_path)
        print(f"Saved comparison to {output_path}")
        return True
        
    except Exception as e:
        print(f"Failed to create comparison for {label}: {e}")
        return False

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
    output format:
    ## Score: X/10
    ## Issues:
    - ...
    ## Summary:
    ...    """
    
    try:
        response = await adapter.generate_text(prompt, image_data=image_data)
        return response
    except Exception as e:
        print(f"Error: {e}")
        return str(e)

async def main():
    report = "# Evaluation Report v2 (Pages 1-3)\n\n"
    
    slides = [
        ("output/temp/pdf_pages/page_001.png", "output/pptx_captures/slide_v2_001.png", "Slide 1"),
        ("output/temp/pdf_pages/page_002.png", "output/pptx_captures/slide_v2_002.png", "Slide 2"),
        ("output/temp/pdf_pages/page_003.png", "output/pptx_captures/slide_v2_003.png", "Slide 3"),
    ]
    
    for orig, gen, label in slides:
        comp_path = f"output/reports/comparisons_v2/compare_{label.replace(' ', '_')}.png"
        if create_comparison(orig, gen, comp_path, label):
            evaluation = await evaluate_comparison(comp_path, label)
            report += f"## {label}\n\n{evaluation}\n\n"
            print(f"--- {label} Evaluation ---\n{evaluation}\n--------------------------")
            
    with open("output/reports/report_v2.md", "w") as f:
        f.write(report)
    print("\nReport saved to output/reports/report_v2.md")

if __name__ == "__main__":
    asyncio.run(main())
