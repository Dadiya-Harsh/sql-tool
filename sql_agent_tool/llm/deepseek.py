# sql_agent_tool/llm/deepseek.py
from openai import OpenAI
from .base import LLMInterface, LLMResponse

class DeepSeekLLM(LLMInterface):
    def __init__(self, api_key: str, model: str = "deepseek-chat"):
        self.client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")
        self.model = model

    def generate_sql(self, prompt: str) -> LLMResponse:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are an SQL generator. Convert the following natural language query into an SQL query."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=1024,
            stream=False
        )
        return LLMResponse(content=response.choices[0].message.content.strip())