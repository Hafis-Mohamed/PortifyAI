# pyrefly: ignore [missing-import]
import pdfplumber

def extractText(pdf_path):
    text=""
    try:
        with pdfplumber.open(pdf_path)as pdf:
            for page in pdf.pages:
                page_text=page.extract_text()
                if page_text:
                    text+=page_text
    except Exception as e:
        print("Error reading PDF:",e)
    return text
