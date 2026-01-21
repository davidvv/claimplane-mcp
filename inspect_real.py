import fitz

def inspect(path):
    doc = fitz.open(path)
    page = doc[0]
    print(f"File: {path}")
    print(f"Number of images: {len(page.get_images())}")
    for i, img in enumerate(page.get_image_info()):
        print(f"Image [{i}]: Rect: {img['bbox']}")
    
    print("\n--- Text Blocks ---")
    blocks = page.get_text("blocks")
    for b in blocks:
        if "Digitally signed" in b[4] or "UA988" in b[4]:
            print(f"Rect: {b[:4]} | Text: {b[4].strip()}")

inspect("verified_poa_enc.pdf")
