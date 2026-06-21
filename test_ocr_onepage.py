# test_ocr_simple.py
"""
Simple OCR test - one page only to avoid quota
"""

import fitz
from google import genai
from dotenv import load_dotenv
import os
from pathlib import Path
import base64
import time

load_dotenv()

def test_single_page_ocr(pdf_path, page_num=0):
    """Test OCR on single page"""
    
    print(f"\n📄 Testing: {pdf_path.name}")
    print(f"   Page: {page_num + 1}")
    
    # Convert to image
    doc = fitz.open(str(pdf_path))
    page = doc.load_page(page_num)
    pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
    img_bytes = pix.tobytes("png")
    img_base64 = base64.b64encode(img_bytes).decode('utf-8')
    doc.close()
    
    print("✅ Image created")
    print("🤖 Calling Gemini Vision (waiting 60s for quota reset)...")
    
    # Wait to avoid quota
    time.sleep(60)
    
    # OCR
    try:
        client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        
        response = client.models.generate_content(
           model="gemini-1.5-flash",
            contents=[
                {
                    "parts": [
                        {"text": "Extract all text from this exam paper image. Output only the text."},
                        {
                            "inline_data": {
                                "mime_type": "image/png",
                                "data": img_base64
                            }
                        }
                    ]
                }
            ]
        )
        
        text = response.text
        
        print("\n" + "="*60)
        print("EXTRACTED TEXT:")
        print("="*60)
        print(text[:1500])  # First 1500 chars
        print("="*60)
        print(f"\nTotal: {len(text)} characters")
        
        if len(text) > 100:
            print("\n✅ OCR SUCCESS!")
            
            # Check for question paper keywords
            keywords = ["question", "marks", "exam", "answer", "semester", "time"]
            found = [k for k in keywords if k.lower() in text.lower()]
            if found:
                print(f"✅ Question paper confirmed! Found: {', '.join(found)}")
        
        return text
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return ""


# Find PDFs
project_root = Path.cwd()
pdfs = list(project_root.rglob("*CN*.pdf"))  # Find CN papers first

if not pdfs:
    pdfs = list(project_root.rglob("*.pdf"))

if pdfs:
    # Test the first CN paper (or any paper)
    test_pdf = pdfs[0]
    test_single_page_ocr(test_pdf, page_num=0)
else:
    print("❌ No PDFs found")