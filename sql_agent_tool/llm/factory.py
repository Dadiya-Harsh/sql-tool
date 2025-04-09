from sql_agent_tool.llm.groq import GroqLLM
from sql_agent_tool.llm.gemini import GeminiLLM
from sql_agent_tool.llm.deepseek import DeepSeekLLM
from sql_agent_tool.models import LLMConfig

class LLMFactory:
    @staticmethod
    def get_llm(llm_config: LLMConfig):
        """
        Factory method to create an LLM instance based on the provider.

        Args:
            llm_config (LLMConfig): Configuration object for the LLM.

        Returns:
            LLMInterface: An instance of the appropriate LLM implementation.
        """
        provider = llm_config.provider.lower()
        if provider == "groq":
            return GroqLLM(api_key=llm_config.api_key, model=llm_config.model)
        elif provider == "gemini":
            return GeminiLLM(api_key=llm_config.api_key, model=llm_config.model)
        elif provider == "deepseek":
            return DeepSeekLLM(api_key=llm_config.api_key, model=llm_config.model)
        elif provider == "openai":
            from sql_agent_tool.llm.openai import OpenAILLM
            return OpenAILLM(api_key=llm_config.api_key, model=llm_config.model)
        else:
            raise ValueError(f"Unsupported LLM provider: {provider}")