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