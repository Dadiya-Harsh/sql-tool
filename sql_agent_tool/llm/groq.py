# sql_agent_tool/llm/groq.py
from groq import Groq
from .base import LLMInterface, LLMResponse

class GroqLLM(LLMInterface):
    def __init__(self, api_key: str, model: str = "llama-3.3-70b-versatile"):
        self.client = Groq(api_key=api_key)
        self.model = model

    def generate_sql(self, prompt: str) -> str:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=1024
        )
        return LLMResponse(content = response.choices[0].message.content.strip())
        # return response.choices[0].message.content.strip()

