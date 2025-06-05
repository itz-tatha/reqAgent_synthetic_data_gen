from extract_data import ExtractFields
from extract_text import ExtractText
import os

directory = "documents"
output_directory = "shots"

def ocr():
    documents = [f for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f))]

    textExtractor = ExtractText(directory, output_directory)

    count = 0
    for doc in documents:
        print(f"Count: {count} || Extracting {doc}")
        textExtractor.process(doc, f"extracted{str(count)}")
        count += 1
        
        
def extract():
    documents = [f for f in os.listdir(output_directory) if os.path.isfile(os.path.join(output_directory, f))]
    # print(documents)
    fieldExtractor = ExtractFields(output_directory, output_directory)

    count = 0
    for doc in documents:
        if doc[:9] == 'extracted':
            print(f"Count: {count} || Extracting Fields from {doc}")
            fieldExtractor.process(doc, f"extracted{str(count)}")
            count += 1
        if count == 2:
            break
        
extract()