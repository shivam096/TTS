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

    def model_call(self, query, model="openai"):
        if model == "openai":
            completion = self.client.chat.completions.create(
                model="o3-mini", messages=[{"role": "user", "content": f"{query}"}]
            )
            return completion.choices[0].message.content
        elif model == "mistralai":
            completion = self.client_mistral.chat.complete(
                model="mistral-small-2501", messages=[{"role": "user", "content": f"{query}"}]
            )
            return completion.choices[0].message.content
