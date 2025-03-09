import os
from openai import OpenAI
from mistralai import Mistral
from dotenv import load_dotenv

load_dotenv()

api_key = os.environ["MISTRAL_API_KEY"]

class LLMCore:
    def __init__(self):
        self.client = OpenAI()
        self.client_mistral = Mistral(api_key=api_key)


    def model_call(self, query, model="o3-mini"):
        if model == "o3-mini":
            completion = self.client.chat.completions.create(
                model=model, messages=[{"role": "user", "content": f"{query}"}]
            )
            return completion.choices[0].message.content
        elif model == "codestral-latest":
            completion = self.client_mistral.chat.complete(
                model=model, messages=[{"role": "user", "content": f"{query}"}]
            )
            return completion.choices[0].message.content