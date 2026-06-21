"""
test_ocr.py — DIAGNOSTIC VERSION
"""

import fitz  # PyMuPDF
from google import genai
from dotenv import load_dotenv
import os
from pathlib import Path
import base64

load_dotenv()

# === STEP 1: Find where we are ===
print("📍 DIAGNOSTIC MODE\n")
print(f"Current working directory: {os.getcwd()}\n")

# === STEP 2: Check if sample_data exists ===
print("🔍 Checking paths...\n")

paths_to_check = [
    "sample_data",
    "sample_data/my_real_semester_mess",
    Path("sample_data"),
    Path("sample_data/my_real_semester_mess"),
]

for p in paths_to_check:
    exists = Path(p).exists()
    status = "✅ EXISTS" if exists else "❌ NOT FOUND"
    print(f"{status}: {p}")
    
    if exists and Path(p).is_dir():
        files = list(Path(p).iterdir())
        print(f"         Files inside: {len(files)}")
        if files:
            for f in files[:5]:  # Show first 5
                print(f"           - {f.name}")

print("\n" + "="*60)

# === STEP 3: Search everywhere for PDFs ===
print("\n🔍 Searching for ALL PDFs in project...\n")

project_root = Path.cwd()
all_pdfs = list(project_root.rglob("*.pdf"))

if all_pdfs:
    print(f"Found {len(all_pdfs)} PDF(s):\n")
    for pdf in all_pdfs:
        print(f"📄 {pdf}")
        print(f"   Full path: {pdf.absolute()}\n")
else:
    print("❌ No PDFs found anywhere in project!")

print("="*60)

# === STEP 4: If we found PDFs, test OCR on first one ===
if all_pdfs:
    test_pdf = all_pdfs[0]
    print(f"\n🧪 Testing OCR on: {test_pdf.name}")
    
    def pdf_page_to_image_base64(pdf_path, page_num=0):
        """Convert PDF page to base64 image"""
        try:
            doc = fitz.open(str(pdf_path))
            page = doc.load_page(page_num)
            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
            img_bytes = pix.tobytes("png")
            img_base64 = base64.b64encode(img_bytes).decode('utf-8')
            doc.close()
            return img_base64
        except Exception as e:
            print(f"❌ Error: {e}")
            return None
    
    def ocr_with_gemini(image_base64):
        """OCR using Gemini Vision"""
        try:
            client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
            
            prompt = """Extract ALL text from this scanned exam paper image.
Preserve structure. Output only the extracted text."""

            response = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=[
                    {
                        "parts": [
                            {"text": prompt},
                            {
                                "inline_data": {
                                    "mime_type": "image/png",
                                    "data": image_base64
                                }
                            }
                        ]
                    }
                ]
            )
            return response.text
        except Exception as e:
            print(f"❌ OCR Error: {e}")
            return ""
    
    print("🤖 Converting page 1 to image...")
    img = pdf_page_to_image_base64(test_pdf, page_num=0)
    
    if img:
        print("✅ Image created")
        print("🤖 Sending to Gemini Vision...\n")
        
        text = ocr_with_gemini(img)
        
        print("="*60)
        print("EXTRACTED TEXT:")
        print("="*60)
        print(text[:1000])
        print("="*60)
        print(f"\nTotal: {len(text)} characters")
        
        if len(text) > 100:
            print("\n✅ OCR SUCCESS!")
        else:
            print("\n⚠️ Little/no text extracted")
            print("Try page 2 or 3 (page 1 might be blank)")

else:
    print("\n❌ Cannot test OCR — no PDFs found")
    print("\n📋 MANUAL STEPS NEEDED:")
    print("1. Open File Explorer")
    print("2. Navigate to: C:\\Users\\CONFUSED CRUSADER\\Documents\\semprep")
    print("3. Create folder: sample_data\\my_real_semester_mess")
    print("4. Put your PYQ PDFs inside that folder")
    print("5. Run this script again")