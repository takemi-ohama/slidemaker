
import os
import subprocess
from pathlib import Path
from pdf2image import convert_from_path

def convert_pptx_to_images(pptx_path, output_dir):
    """
    Convert PPTX to images using LibreOffice to PDF then pdf2image.
    This is more reliable than using the python-pptx-interface on Linux without a display.
    """
    os.makedirs(output_dir, exist_ok=True)
    
    # 1. Convert PPTX to PDF using LibreOffice
    print(f"Converting {pptx_path} to PDF...")
    temp_pdf = str(Path(output_dir) / "temp_presentation.pdf")
    
    # Use libreoffice headless conversion
    cmd = [
        "libreoffice", 
        "--headless", 
        "--convert-to", 
        "pdf", 
        "--outdir", 
        output_dir, 
        pptx_path
    ]
    
    try:
        # セキュリティ: タイムアウトとエラーハンドリングの追加
        result = subprocess.run(
            cmd,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=60  # 60秒でタイムアウト
        )

        # プロセスの正常終了を確認
        if result.returncode != 0:
            raise subprocess.CalledProcessError(
                result.returncode, cmd, result.stdout, result.stderr
            )

    except subprocess.TimeoutExpired:
        print(f"LibreOffice conversion timed out after 60 seconds")
        raise
    except subprocess.CalledProcessError as e:
        print(f"Error running LibreOffice: {e}")
        print(f"stdout: {e.stdout.decode() if e.stdout else 'None'}")
        print(f"stderr: {e.stderr.decode() if e.stderr else 'None'}")
        raise

    try:
        
        # Rename the output if needed (LibreOffice keeps the filename but changes extension)
        base_name = Path(pptx_path).stem
        generated_pdf = str(Path(output_dir) / f"{base_name}.pdf")
        
        if os.path.exists(generated_pdf):
            if os.path.exists(temp_pdf):
                os.remove(temp_pdf)
            os.rename(generated_pdf, temp_pdf)
        elif not os.path.exists(temp_pdf):
            print(f"Failed to find generated PDF at {generated_pdf} or {temp_pdf}")
            return
            
        # 2. Convert PDF to Images
        print(f"Converting PDF to images...")
        images = convert_from_path(temp_pdf)
        
        for i, image in enumerate(images):
            # Save as slide_v10_001.png, etc. (1-based index)
            image_path = os.path.join(output_dir, f"slide_v10_{i+1:03d}.png")
            image.save(image_path, "PNG")
            print(f"Saved {image_path}")
            
        # Clean up temp PDF
        if os.path.exists(temp_pdf):
            os.remove(temp_pdf)
            
    except subprocess.CalledProcessError as e:
        print(f"Error running LibreOffice: {e}")
    except Exception as e:
        print(f"Error converting to images: {e}")

def main():
    pptx_path = "output/generated_pages3-6_v10.pptx"
    output_dir = "output/pptx_captures"
    
    if not os.path.exists(pptx_path):
        print(f"PPTX file not found: {pptx_path}")
        return
        
    convert_pptx_to_images(pptx_path, output_dir)

if __name__ == "__main__":
    main()
