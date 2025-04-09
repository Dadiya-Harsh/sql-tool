# sql_agent_tool/llm/base.py
from abc import ABC, abstractmethod
from dataclasses import dataclass

@dataclass
class LLMResponse:
    """Model for LLM response"""
    content: str
    
class LLMInterface(ABC):
    @abstractmethod
    def generate_sql(self, prompt: str) -> str:
        pass