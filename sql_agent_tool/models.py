from pydantic import BaseModel, field_validator
from typing import Dict, List, Any, Optional
from .llm.model_validation import available_models_list

class DatabaseConfig(BaseModel):
    """Configuration model for database connection"""
    drivername: str
    username: str
    password: str
    host: str
    port: int
    database: str
    query: Dict[str, str] = {}
    require_ssl: bool = False

    @field_validator('drivername')
    def validate_drivername(cls, v):
        allowed = {'postgresql', 'mysql', 'sqlite', 'mssql'}
        if v not in allowed:
            raise ValueError(f'Driver must be one of {allowed}')
        return v

class QueryResult(BaseModel):
    """Model for query results"""
    data: List[Dict[str, Any]]
    columns: List[str]
    row_count: int
    query: str
    success: bool
    error: Optional[str] = None

class LLMConfig(BaseModel):
    """Configuration model for LLM settings"""
    provider: str  # e.g., 'openai', 'gemini', 'microsoft', etc.
    api_key: str
    model: str  # e.g., 'gpt-3.5-turbo'
    temperature: float = 0.7
    max_tokens: int = 1500

    @field_validator('provider')
    def validate_provider(cls, v):
        allowed = {'openai', 'gemini', 'microsoft', 'deepseek', 'llama', 'groq'}
        if v not in allowed:
            raise ValueError(f'Provider must be one of {allowed}')
        return v
    
    @field_validator('model')
    def validate_model(cls, v):
        allowed =available_models_list
        if v not in allowed:
            raise ValueError(f'Model must be one of {allowed}')
        return v
    