
from pypdf import PdfReader, PdfWriter

def extract_pages(input_path, output_path, start_page, end_page):
    reader = PdfReader(input_path)
    writer = PdfWriter()
    
    # start_page is 1-based, convert to 0-based
    start_idx = start_page - 1
    end_idx = end_page # slice is exclusive, so page 6 (index 5) needs end_idx 6
    
    for i in range(start_idx, end_idx):
        writer.add_page(reader.pages[i])
        
    with open(output_path, "wb") as f:
        writer.write(f)
    print(f"Extracted pages {start_page}-{end_page} to {output_path}")

if __name__ == "__main__":
    extract_pages(
        "samples/MDX_Strategic_Engine_2026.pdf",
        "samples/MDX_Strategic_Engine_2026_pages4-6.pdf",
        4, 6
    )
