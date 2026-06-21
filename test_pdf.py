"""
test_pdf.py — Test PyMuPDF extraction on your real PYQs
"""

import fitz  # PyMuPDF
import os

def extract_text(pdf_path):
    """Extract all text from PDF"""
    try:
        doc = fitz.open(pdf_path)
        full_text = ""
        
        print(f"\n📄 Processing: {os.path.basename(pdf_path)}")
        print(f"   Pages: {len(doc)}")
        
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            text = page.get_text()
            full_text += text
            print(f"   Page {page_num + 1}: {len(text)} chars")
        
        doc.close()
        return full_text
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return ""


# === TEST IT ===
# Replace this path with one of YOUR actual PYQ PDFs
test_file = r"C:\Users\CONFUSED CRUSADER\Documents\semprep\sample_data\my_real_semester_mess\my_real_semester_mess\5TH MID SEM 2022[1].pdf"

if os.path.exists(test_file):
    text = extract_text(test_file)
    
    print("\n" + "="*50)
    print("EXTRACTED TEXT (first 1000 chars):")
    print("="*50)
    print(text[:1000])
    print("="*50)
    print(f"\nTotal extracted: {len(text)} characters")
    
    # Check if it's actually a text-based PDF
    if len(text.strip()) < 100:
        print("\n⚠️ WARNING: Very little text extracted!")
        print("This might be an image-based PDF (scanned).")
        print("We'll handle this with Gemini OCR later.")
    else:
        print("\n✅ SUCCESS: Text extraction works!")
        
else:
    print(f"❌ File not found: {test_file}")
    print("\nUpdate the test_file path with your actual PYQ PDF name.")