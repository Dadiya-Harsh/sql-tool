#sql_agent_tool/models.py
from pydantic import BaseModel, field_validator
from typing import Dict, List, Any, Optional

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
        allowed = {'postgresql', 'mysql', 'sqlite', 'mssql', 'mysql+pymysql', 'oracle+cx_oracle'}
        if v not in allowed:
            raise ValueError(f'Driver must be one of {allowed}')
        return v
    
    def build_connection_string(self, driver: str = None) -> str:
        """Build a SQLAlchemy-compatible connection string, optionally overriding the driver."""
        # Handle SQLite separately
        if self.drivername == "sqlite" or (driver and "sqlite" in driver):
            return f"sqlite:///{self.database}"

        # Use provided driver or fall back to drivername
        driver = driver or self.drivername

        # Construct base connection string
        port_part = f":{self.port}" if self.port else ""
        base_url = f"{driver}://{self.username}:{self.password}@{self.host}{port_part}/{self.database}"

        # Handle query parameters
        query_params = []
        if self.require_ssl:
            query_params.append("ssl=true")
        if self.query:
            query_params.extend(f"{key}={value}" for key, value in self.query.items())

        # Combine query parameters
        if query_params:
            return f"{base_url}?{'&'.join(query_params)}"
        return base_url

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
        allowed = {'gpt-3.5-turbo', 'gpt-4', 'llama-3.3-70b-versatile', 'gemini-1.5-turbo', 'gemma2-9b-it', 'llama-3.1-8b-instant', 'llama3-70b-8192', 'gpt-4o', 'o1-mini', 'models/gemini-1.5-flash'}
        if v not in allowed:
            raise ValueError(f'Model must be one of {allowed}')
        return v
    