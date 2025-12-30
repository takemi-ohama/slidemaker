
from PIL import Image, ImageDraw, ImageFont
import os

def create_comparison(original_path, generated_path, output_path, label):
    try:
        img1 = Image.open(original_path)
        img2 = Image.open(generated_path)
        
        # Resize img2 to match img1 height if necessary, maintaining aspect ratio
        if img1.size != img2.size:
            print(f"Resizing {generated_path} from {img2.size} to {img1.size}")
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
        # Try to load a default font, otherwise use default
        try:
            font = ImageFont.truetype("Arial.ttf", 24)
        except IOError:
            font = ImageFont.load_default()
            
        draw.text((10, 10), f"Original PDF ({label})", fill="black", font=font)
        draw.text((img1.width + 10, 10), f"Generated PPTX ({label})", fill="black", font=font)
        
        new_im.save(output_path)
        print(f"Saved comparison to {output_path}")
        
    except Exception as e:
        print(f"Failed to create comparison for {label}: {e}")

def main():
    os.makedirs("output/reports/comparisons", exist_ok=True)
    
    slides = [
        ("output/temp/pdf_pages/page_001.png", "output/pptx_captures/slide_v8_001.png", "Slide 1"),
        ("output/temp/pdf_pages/page_002.png", "output/pptx_captures/slide_v8_002.png", "Slide 2"),
        ("output/temp/pdf_pages/page_003.png", "output/pptx_captures/slide_v8_003.png", "Slide 3"),
    ]
    
    for orig, gen, label in slides:
        if os.path.exists(orig) and os.path.exists(gen):
            create_comparison(orig, gen, f"output/reports/comparisons/compare_{label.replace(' ', '_')}.png", label)
        else:
            print(f"Missing files for {label}: {orig} or {gen}")

if __name__ == "__main__":
    main()
