from gen_ai import LLM
import tiktoken
import json
import os


SYSTEM_PROMPT = f"""To fill a requisition, we need the following information:
- Buyer
- Ship-to-Address - Address of the Buyer or Service Location
- Descriotion / Item (Mandatory) - Description of the Item
- Supplier (Mandatory) - Supplier Name
- Billing Account
- Linked Contract
- Start and End Date
- Service Sheet Requirements
- Item Type (Mandatory)
- Supplier sites (Mandatory) - Website of supplier
- Unit price (Mandatory)
- Currency (Mandatory)
- Transmission method (Mandatory)
- UOM (Only mandatory for quantity & resource type)
- identify Service Line Type
    - Amount-based service → line_type: RequisitionAmountLine, service_type: amount_deliverable
    - Quantity-based service → line_type: RequisitionQuantityLine, service_type: quantity_deliverable
    - Resource-based service → line_type: RequisitionQuantityLine, service_type: resource

From the statement of work below, try to find out as many of the above fields as possible.
Do not assume or add any information that is not present already.

Statement of Work:
"""

class ExtractFields():
    def __init__(self, model='gpt-4.1-mini', input_folder="ocr_output", output_folder="extracted"):
        self.model = model
        self.input_folder = input_folder
        self.output_folder = output_folder
    
    def process(self, doc_name, output_file_name=""):
        self.doc_name = doc_name
        self.doc_path = f"{self.input_folder}/{self.doc_name}"
        
        if output_file_name == "":
            self.output_file = f"{self.doc_name}_extracted"
        else:
            self.output_file = output_file_name
        
        self.load_doc()
        self.extract_data()
        tokens = self.token_count()
        self.save_token_count(self.doc_name, tokens)
        
    def load_doc(self):
        with open(self.doc_path, 'r') as file:
            sow = file.read()
        file.close()
        self.prompt = SYSTEM_PROMPT + sow

    def extract_data(self):
        llm = LLM(self.model)
        response = llm.getResponse(self.prompt)

        with open(f"{self.output_folder}/{self.output_file}.txt", 'w') as file:
            file.write(response)
        file.close()
        
    def token_count(self):
        model = "gpt-4o-mini"
        encoding = tiktoken.encoding_for_model(model)

        num_tokens = len(encoding.encode(self.full_text))
        # print(f"Token count: {num_tokens}")
        return num_tokens
        
    def save_token_count(self, filename, token_count, json_path="shot_token_counts.json"):
        data = {}
        
        if os.path.exists(json_path):
            with open(json_path, "r") as f:
                data = json.load(f)

        if filename in data:
            print(f"Token count for '{filename}' already exists.")
            return

        data[filename] = token_count
        with open(json_path, "w") as f:
            json.dump(data, f, indent=4)

