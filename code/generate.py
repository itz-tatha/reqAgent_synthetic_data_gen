from gen_ai import LLM
import os
import pandas as pd
import sys
import json
import ast
from fpdf import FPDF
import textwrap
import tiktoken
import re

DOCUMENTS = "shots"
EXTRACTIONS = "shots"
OUT_FOLDER = "generated"
DATA_FOLDER = "data"
PROMPT_TEMP = "code"
MAX_TRIES = 1

COLUMNS_TO_GEN = ['description', 'unit_price', 'type', 'service_sheet_required', 'requested_by_id', 'address_name', 'address_street1',
       'address_street2', 'address_city', 'address_state', 'address_postal_code', 'address_country_name', 'supplier_name', 'supplier_site',
       'account_name', 'account_type', 'start_date', 'end_date', 'resource_manager', 'linked_contract_name', 'currency_code']

COLUMNS_TO_STORE = ['rh_id', 'rl_id', 'supplier_id', 'account_id', 'account_type_id',
       'ship_to_address_id', 'linked_contract_id', 'currency_id']

SYSTEM_PROMPT = f"""A Statement of Work is a contract between a Buyer and Supplier/Vendor. It describes all the necessary accepts of legal binding as well.
It must include the requirements to fulfill the product or service deal, such as, address of delivery, pricing, current, start and end
date of the contract, supplier, Buyer names, account details and much more.

Your goal is to write such statement of work, given necessary information about the contract. Here is an example.

"""

INSTRUCTION_PROMPT = f"""Instructions:
- You will be given such information about contract and you have to write statement of work.
- Make the document long and detailed.
- If some part is missing, imagine that and hallucinate to create details.
- Make it atleast 5000 words.
- Don't write in structured way.
- Hide the given information in the contract text.
Information:
"""


class GenerateDocument():
    def __init__(self, model='gpt-4.1-mini', mode='test', sample_size=1, few_shot=1):
        self.mode = mode
        self.type = 'gen'
        self.few_shot_count = few_shot
        self.sample_size = sample_size
        self.model = model
        self.display = 1
        
        self.few_shot_prompt = ""
        if self.few_shot_count:
            self.few_shot_prompt = "Examples:\n"
            
        if self.model == 'gpt-4.1-mini':
            self.encoding = tiktoken.encoding_for_model('gpt-4o-mini')
        else:
            self.encoding = tiktoken.encoding_for_model(self.model)
            
        self.process()
        
    def load_data(self):
        df = pd.read_excel(f"{DATA_FOLDER}/{self.mode}5.xlsx")
        # if self.type == 'gen':
        #     COLUMNS = COLUMNS_TO_GEN
        # else:
        #     COLUMNS = COLUMNS_TO_STORE
        COLUMNS = COLUMNS_TO_GEN + COLUMNS_TO_STORE
        
            
        missing_keys = [field for field in COLUMNS if field not in list(df.columns)]
        if missing_keys:
            print("Missing keys:", missing_keys)
            sys.exit()
        
        data = df[COLUMNS]
        
        return data
    
    def get_shots(self, num):
        with open(f"{DOCUMENTS}/output{num}.txt", 'r') as file:
            document_ocr = file.read()
        with open(f"{EXTRACTIONS}/extracted{num}.txt", 'r') as file:
            information = file.read()
        
        return document_ocr, information
    
    def get_few_shots(self, document_ocr, extraction):
        prompt = f"""Information:
{extraction}
        
Statement of Work Document:
{document_ocr}
        """
        self.few_shot_prompt += prompt
    
    def get_prompt(self, row):
        information = ""
        for col in COLUMNS_TO_GEN:
            information += f"{col}: {row[col]}\n"
        information.strip()
        
        prompt = f"""{SYSTEM_PROMPT}
{self.few_shot_prompt}
        
{INSTRUCTION_PROMPT}
        
Information:
{information}
        """
        
        if self.display:
            print(information)
        
        return prompt
    
    def getErrorCode(self, exc):
        initial_dict = exc.__dict__
        interm_dict = initial_dict['message'].split('Error code:')[1].strip()[6:]
        code = initial_dict['message'].split('Error code:')[1].strip()[:3]
        
        return code

    def getBlockedURL(self, exc):
        initial_dict = exc.__dict__
        interm_dict = initial_dict['message'].split('Error code:')[1].strip()[6:]
        
        final_dict = ast.literal_eval(interm_dict)
        json_data = json.dumps(final_dict, indent=2)
        error_details = json.loads(json_data)
        
        blocked = []
        
        for i in range(len(error_details['guardrail']['results'])):
            blocked.append(error_details['guardrail']['results'][str(i+1)]['input']['response'][0]['match'])
        
        return blocked

    def generate_document(self, prompt, llm):
        trial = MAX_TRIES
        while trial:
            try:
                response = llm.getResponse(prompt)
                return response
            except Exception as e:
                exc = e
                if self.getErrorCode(exc) != '400':
                    print(exc, self.getErrorCode(exc), type(self.getErrorCode(exc)))
                    sys.exit()
                    # blocked = getBlockedURL(exc)
                trial -= 1
                if trial == 1:
                    print('Last Attempt')
        try:
            response = llm.getResponse(prompt)
            return response
        except:
            return -1
    
    def get_info(self, row):
        info_for_gen = ""
        info_to_store = ""
        
        for col in COLUMNS_TO_GEN:
            info_for_gen += f"{col}: {row[col]}\n"
        info_for_gen.strip()
        
        # self.type = 'store'
        
        for col in COLUMNS_TO_STORE:
            info_to_store += f"{col}: {row[col]}\n"
        info_to_store.strip()
        
        return info_for_gen, info_to_store
    
    def store_metadata(self, info, row):
        try:
            info = info[~((info['generated_file'] == row[0]) & (info['model_name'] == row[3]))].reset_index(drop=True)
            info = pd.concat([info, pd.DataFrame([row], columns=info.columns)], ignore_index=True)
        except TypeError:
            info.append(row)
        return info
    
    def save_generation(self, num, response):
        with open(f"{OUT_FOLDER}/document{num}_{self.model[4:]}.txt", 'w') as file:
            file.write(response)
        file.close()
    
    def wrap_text(self, text, width=90):
        return "\n".join(textwrap.fill(line, width) for line in text.splitlines())
    
    def convert_to_pdf(self, num, response):
        pdf = FPDF()
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=15)

        font_path = "/System/Library/Fonts/Supplemental/Arial.ttf"  # update path if needed
        pdf.add_font("Arial", "", font_path, uni=True)
        pdf.set_font("Arial", "", 12)

        response = response.replace('\u00A0', ' ').replace('\u2019', "'")
        wrapped_text = self.wrap_text(response, width=90)
        
        pdf.multi_cell(0, 10, wrapped_text)

        pdf.output(f"{OUT_FOLDER}/document{num}_{self.model[4:]}.pdf")
     
    def process(self):
        self.data = self.load_data()
        print("DATA HAS BEEN LOADED")
        llm = LLM(self.model)
        
        file_path = f"{OUT_FOLDER}/prompt_information.xlsx"
        if os.path.exists(file_path):
            info = pd.read_excel(file_path)
        else:
            info = []
            
        
        for index, row in self.data.iterrows():
            if index == self.sample_size:
                break
            
            num_files = len([f for f in os.listdir(DOCUMENTS) if os.path.isfile(os.path.join(DOCUMENTS, f))])
            for j in range(min(self.few_shot_count, num_files)):
                document_ocr, information = self.get_shots(j)
                self.get_few_shots(document_ocr, information)
            
            print("FEW SHOT PROMPT READY")
            
            ret1, ret2 = self.get_info(row)
            
            prompt = self.get_prompt(row)
            with open(f"{PROMPT_TEMP}/temp_prompt.txt", 'w') as file:
                file.write(prompt)
                
            print("GENERATING RESPONSE")
            
            response = self.generate_document(prompt, llm)
            self.save_generation(index, response)
            self.convert_to_pdf(index, response)
            print("RESPONSE SAVED")
            
            info = self.store_metadata(info, [f"document{index}", ret1, ret2, self.model, len(re.findall(r'\b\w+\b', response)), len(self.encoding.encode(response))])
        
        info = pd.DataFrame(info)
        print(info)
        info.to_excel(f"{OUT_FOLDER}/prompt_information.xlsx", index=False, header = ["generated_file", "information_in_prompt", "information_to_track", "model_name", "num_of_words", "num_of_tokens"])
            
            
            
                
    
    
GenerateDocument()