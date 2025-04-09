from sql_agent_tool.llm.base import LLMInterface, LLMResponse
from openai import OpenAI

class OpenAILLM(LLMInterface):
    def __init__(self, api_key: str, model: str = "gpt-3.5-turbo"):
        self.client = OpenAI(api_key=api_key)
        self.model = model

    def generate_sql(self, prompt: str) -> str:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are an SQL generator. Convert the following natural language query into an SQL query."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=150
        )
        return LLMResponse(content = response.choices[0].message.content.strip())