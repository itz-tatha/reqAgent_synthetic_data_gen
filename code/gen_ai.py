import openai
import os
import pandas as pd
import numpy as np
from langchain_openai import AzureChatOpenAI
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage
import base64
import requests
import tiktoken
import json
from base64 import b64encode
import uuid
import os
import pandas as pd
import json
import ast
openai.api_version = "2023-07-01-preview"
openai_api_version = "2023-07-01-preview"
deployment_name="genai-gpt-35-turbo-16k"
os.environ["AZURE_OPENAI_API_KEY"] = "8c9be5e589f64743bfe34758ca6212f7"
os.environ["AZURE_OPENAI_ENDPOINT"] = "https://aicoe-openai-canada-east.openai.azure.com/"



def num_tokens_from_string(string: str, encoding_name: str) -> int:
    """Returns the number of tokens in a text string."""
    encoding = tiktoken.get_encoding(encoding_name)
    num_tokens = len(encoding.encode(string))
    return num_tokens

class SAND:
    def __init__(self, id:str, secret:str, scope:str, env:str='dev') -> None:
        self.id     = id
        self.secret = secret
        self.scope  = scope
        self.env    = env
        self._token = None
        self.sand_url = f"https://sand-{env}.io.coupadev.com"

    def encode_client_credentials(self, client_id, client_secret):
        credentials_str = f"{client_id}:{client_secret}"
        encoded_credentials = base64.b64encode(credentials_str.encode()).decode()
        return encoded_credentials

    def _get_token(self):
        url = f"{self.sand_url}/oauth2/token"
        data = {
            'grant_type': 'client_credentials',
            'scope': self.scope
        }
        credential = self.encode_client_credentials(self.id, self.secret)
        headers = {
            'Authorization': f'Basic {credential}'
        }
        response = requests.post(url, data=data, headers=headers)
        try:
            return response.json()['access_token']
        except Exception as e:
            print(f"Unable to get access token: {e}")
            raise e

    @property
    def token(self):
        if not self._token:
            # print("Re-generating token")
            self._token = self._get_token()
        return self._token


SAND_CLIENT_ID="aiassistantbot-dev-na10001-2.io.coupadev.com"
SAND_CLIENT_SECRET="TMmysZ1v0TiBlCZDpS-sHSpgx4"
sand = SAND(SAND_CLIENT_ID, SAND_CLIENT_SECRET, "coupa")
# print( sand.token )

class LLM:
    def __init__(self, model_name):
        self.model_name = model_name
    
    def getResponse(self, prompt):
        msg = prompt
        
        PLATFORM_BASE = "v1/openai"
        platform_url = "https://genai-platform-dev.io.coupadev.com/" + PLATFORM_BASE

        num_tokens_msg = num_tokens_from_string(msg,"cl100k_base")
        if num_tokens_msg >= 16384:
            print("max token size exceeded")
            return ""
        if num_tokens_msg < 16384:
            sand = SAND(SAND_CLIENT_ID, SAND_CLIENT_SECRET, "coupa")
            headers = {
                'Authorization': f'bearer {sand.token}',
                'X-Coupa-Tenant': 'myservice.io.coupadev.com',
                'X-Coupa-Application': 'default',
                'X-Coupa-Request-Id': uuid.uuid4().hex
            }
            llm = ChatOpenAI(
                model_name=self.model_name,
                default_headers=headers,
                openai_api_key='ignore',
                openai_api_base=platform_url,
                temperature=0.7
            )
            response = llm.invoke(msg)
        extracted_tax_id = response.content
        return extracted_tax_id

