from sql_agent_tool.llm.base import LLMInterface
import openai

class OpenAILLM(LLMInterface):
    def __init__(self, api_key: str, model: str = "gpt-3.5-turbo"):
        self.api_key = api_key
        self.model = model
        openai.api_key = api_key

    def generate_sql(self, prompt: str) -> str:
        response = openai.ChatCompletion.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are an SQL generator. Convert the following natural language query into an SQL query."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=150
        )
        return response.choices[0].message['content'].strip()