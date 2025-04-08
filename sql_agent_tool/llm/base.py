# sql_agent_tool/llm/base.py
from abc import ABC, abstractmethod

class LLMInterface(ABC):
    @abstractmethod
    def generate_sql(self, prompt: str) -> str:
        pass