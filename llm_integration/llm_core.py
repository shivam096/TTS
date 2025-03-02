from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()


class LLMCore:
    def __init__(self):
        self.client = OpenAI()

    def model_call(self, query, model="o3-mini"):
        completion = self.client.chat.completions.create(
            model=model, messages=[{"role": "user", "content": f"{query}"}]
        )
        return completion.choices[0].message.content

