# sql_agent_tool/llm/deepseek.py
import requests
from .base import LLMInterface

class DeepSeekLLM(LLMInterface):
    def __init__(self, api_key: str, model: str = "deepseek-70b"):
        self.api_key = api_key
        self.model = model
        self.base_url = "https://api.deepseek.com/v1/chat/completions"

    def generate_sql(self, prompt: str) -> str:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        data = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.3,
            "max_tokens": 1024
        }
        response = requests.post(self.base_url, headers=headers, json=data)
        return response.json()["choices"][0]["message"]["content"]