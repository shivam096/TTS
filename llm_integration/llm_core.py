from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI()

def model_call(client, model= "o3-mini", query=None):
    completion = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "user",
                "content": f"{query}"
            }
        ]
    )
    return completion.choices[0].message.content



print(model_call(client, query="What is the capital of France?"))