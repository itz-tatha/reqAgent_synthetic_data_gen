from gen_ai import LLM
from generate import GenerateDocument
from extract_text import ExtractText
from extract_data import ExtractFields
import os
import sys

class Pipeline():
    def __init__(self):
        model = 'gpt-4.1-mini'
        mode = 'test'
        sample_size = 1
        few_shot = 1
        syntheticGenerator = GenerateDocument(model, mode, sample_size, few_shot)
        print(f"\n###Synthetic Document Generation Done")
        
        self.generated_directory = "generated"
        self.ocr_directory = "ocr_output"
        self.extractor_model = 'gpt-4.1-mini'
        self.perform_ocr()
        self.field_extraction()
        self.summarise()
    
    def perform_ocr(self):
        pdf_files = [f for f in os.listdir(self.generated_directory) if f.lower().endswith('.pdf')]
        textExtractor = ExtractText()
        
        for file in pdf_files:
            textExtractor.process(file)
        print(f"\n###OCR Has Been on Synethetically Generated Documents")
            
    
    def field_extraction(self):
        ocr_documents = [f for f in os.listdir(self.ocr_directory) if f.lower().endswith('.txt')]
        fieldExtractor = ExtractFields(self.extractor_model)
        
        for doc in ocr_documents:
            fieldExtractor.process(doc)
        print(f"\n###Field Extractions Have Been Performed")
        
    def summarise(self):
        pass
        