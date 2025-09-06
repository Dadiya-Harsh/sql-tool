"""
Module to validate and retrieve the latest AI models from OpenAI, Groq, and Gemini APIs.
Provides fallback model lists when API keys are missing, invalid, or API calls fail.

Users must set environment variables (GROQ_API_KEY, OPENAI_API_KEY, GOOGLE_API_KEY) in their
application's environment or .env file, or pass keys directly to the functions.
"""

import requests
import json
import os 
from dotenv import load_dotenv

load_dotenv()

groq_models_url = "https://api.groq.com/openai/v1/models"
openai_models_url = "https://api.openai.com/v1/models"
gemini_models_url = "https://generativelanguage.googleapis.com/v1beta/models"

# Fallback model lists for each provider
FALLBACK_OPENAI_MODELS = [
    "gpt-4o",
    "gpt-4-turbo",
    "gpt-3.5-turbo",
    "text-embedding-ada-002"
]

FALLBACK_GROQ_MODELS = [
    "llama3-8b-8192",
    "llama3-70b-8192",
    "mixtral-8x7b-32768",
    "gemma-7b-it",
    "openai/gpt-oss-20b",
    "openai/gpt-oss-120b",
    "meta-llama/llama-4-maverick-17b-128e-instruct",
    "moonshotai/kimi-k2-instruct",
    "qwen/qwen3-32b"
]

FALLBACK_GEMINI_MODELS = [
    "gemini-1.5-pro",
    "gemini-1.5-flash",
    "gemini-1.0-pro",
    "gemini-2.5-flash",
    "text-embedding-004"
]

def get_list_groq_models(api_key: str = None) -> list:
    """
    Retrieves a list of available Groq models from the Groq API.

    Args:
        api_key (str, optional): Groq API key. If not provided, uses GROQ_API_KEY from environment.

    Returns:
        list: A list of Groq model IDs. Returns fallback models if API key is missing, invalid, or API call fails.

    Example:
        >>> from sql_agent_tool.llm.model_validation import get_list_groq_models
        >>> models = get_list_groq_models(api_key="your-groq-api-key")
        >>> print(models)
    """
    effective_api_key = api_key or os.getenv('GROQ_API_KEY')
    if not effective_api_key:
        return FALLBACK_GROQ_MODELS
        
    try:
        headers = {
            "Authorization": f"Bearer {effective_api_key}",
            "Content-Type": "application/json"
        }
        response = requests.get(groq_models_url, headers=headers)
        response.raise_for_status()
        
        result = response.json()
        list_models = [model['id'] for model in result['data']]
        return list_models
    except (requests.RequestException, KeyError, ValueError):
        return FALLBACK_GROQ_MODELS

def get_list_openai_models(api_key: str = None) -> list:
    """
    Retrieves a list of available OpenAI models from the OpenAI API.

    Args:
        api_key (str, optional): OpenAI API key. If not provided, uses OPENAI_API_KEY from environment.

    Returns:
        list: A list of OpenAI model IDs. Returns fallback models if API key is missing, invalid, or API call fails.

    Example:
        >>> from sql_agent_tool.llm.model_validation import get_list_openai_models
        >>> models = get_list_openai_models(api_key="your-openai-api-key")
        >>> print(models)
    """
    effective_api_key = api_key or os.getenv('OPENAI_API_KEY')
    if not effective_api_key:
        return FALLBACK_OPENAI_MODELS
        
    try:
        headers = {
            "Authorization": f"Bearer {effective_api_key}",
            "Content-Type": "application/json"
        }
        response = requests.get(openai_models_url, headers=headers)
        response.raise_for_status()
        
        result = response.json()
        list_models = [model['id'] for model in result['data']]
        return list_models
    except (requests.RequestException, KeyError, ValueError):
        return FALLBACK_OPENAI_MODELS

def get_list_gemini_models(api_key: str = None) -> list:
    """
    Retrieves a list of available Gemini models from the Google Generative Language API.

    Args:
        api_key (str, optional): Google API key. If not provided, uses GOOGLE_API_KEY from environment.

    Returns:
        list: A list of Gemini model names. Returns fallback models if API key is missing, invalid, or API call fails.

    Example:
        >>> from sql_agent_tool.llm.model_validation import get_list_gemini_models
        >>> models = get_list_gemini_models(api_key="your-google-api-key")
        >>> print(models)
    """
    effective_api_key = api_key or os.getenv('GOOGLE_API_KEY')
    if not effective_api_key:
        return FALLBACK_GEMINI_MODELS
        
    try:
        params = {
            "key": effective_api_key
        }
        response = requests.get(gemini_models_url, params=params)
        response.raise_for_status()
        
        result = response.json()
        list_models = [model['name'] for model in result['models']]
        return list_models
    except (requests.RequestException, KeyError, ValueError):
        return FALLBACK_GEMINI_MODELS

def main():
    """
    Combines model lists from OpenAI, Groq, and Gemini into a single set of allowed models.

    Returns:
        set: A set containing all unique model IDs/names from all providers.

    Example:
        >>> from sql_agent_tool.llm.model_validation import main
        >>> allowed_models = main()
        >>> print(allowed_models)
    """
    openai_allowed_models = get_list_openai_models()
    groq_allowed_models = get_list_groq_models()
    gemini_allowed_models = get_list_gemini_models()

    allowed_models = set()
    allowed_models.update(openai_allowed_models)
    allowed_models.update(groq_allowed_models)
    allowed_models.update(gemini_allowed_models)

    return allowed_models

available_models_list = main()

# if __name__ == '__main__':
#     main()