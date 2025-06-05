import fitz
import pytesseract
from PIL import Image
import io
import tiktoken


class ExtractText():
    def __init__(self, input_folder="generated", output_folder="ocr_output"):
        self.input_folder = input_folder
        self.output_folder = output_folder
        
    def process(self, pdf_name, output_name=""):
        self.pdf_name = pdf_name
        self.pdf_path = f"{self.input_folder}/{pdf_name}"
        
        if output_name == "":
            self.output_name = f"{self.pdf_name}_output"
        else:
            self.output_name = output_name
        
        self.extract_text_pdf_doc()
        self.token_count()

        
    def extract_text_pdf_doc(self):
        doc = fitz.open(self.pdf_path)

        self.full_text = ""

        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            pix = page.get_pixmap(dpi=300)  # High-res image
            img = Image.open(io.BytesIO(pix.tobytes("png")))
            text = pytesseract.image_to_string(img)
            self.full_text += f"\n--- Page {page_num+1} ---\n{text}"

        with open(f"{self.output_folder}/{self.output_name}.txt", 'w') as file:
            file.write(self.full_text)
    

    def token_count(self):
        model = "gpt-4o-mini"
        encoding = tiktoken.encoding_for_model(model)

        num_tokens = len(encoding.encode(self.full_text))
        print(f"Token count: {num_tokens}")

