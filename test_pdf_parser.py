# test_pdf_parser.py
from src.pdf_parser import PDFParser

if __name__ == "__main__":
    pdf_path = "path/to/your/figma_export.pdf"  # <-- Replace with your PDF file path
    parser = PDFParser()
    elements = parser.parse_pdf(pdf_path)
    for idx, element in enumerate(elements, 1):
        print(f"\n--- Element {idx} ---")
        for k, v in element.items():
            print(f"{k}: {v}")

# python test_pdf_parser.py