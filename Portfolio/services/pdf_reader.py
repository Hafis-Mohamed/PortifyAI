# pyrefly: ignore [missing-import]
import fitz # PyMuPDF
import os
# pyrefly: ignore [missing-import]
import docx

def extractText(file_path):
    text = ""
    ext = os.path.splitext(file_path)[1].lower()
    
    if ext == '.docx':
        try:
            doc = docx.Document(file_path)
            for para in doc.paragraphs:
                if para.text.strip():
                    text += para.text.strip() + "\n"
        except Exception as e:
            print("Error reading DOCX:", e)
    else:
        # Default to PDF logic
        try:
            doc = fitz.open(file_path)
            for page in doc:
                blocks = page.get_text("blocks")
                # Filter for text blocks (block_type == 0)
                text_blocks = [b for b in blocks if b[6] == 0]
                # Sort blocks: by y0 (top-down), then x0 (left-right).
                # Rounding y0 groups blocks that are roughly on the same visual line.
                text_blocks.sort(key=lambda b: (round(b[1] / 10), b[0]))
                
                for b in text_blocks:
                    text += b[4].strip() + "\n"
        except Exception as e:
            print("Error reading PDF:", e)
            
    return text
