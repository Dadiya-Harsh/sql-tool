from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy.engine import Engine, Result
# from sql_agent_tool.models import DatabaseConfig, QueryResult
# from sql_agent_tool import models
import sys
sys.path.append(r'E:\Wappnet internship\sql-tool')
from sql_agent_tool.models import DatabaseConfig, QueryResult


class DatabaseBase(ABC):
    def __init__(self, config: DatabaseConfig):
        self.config = config

    @abstractmethod
    def create_engine(self) -> Engine:
        """Create a SQLAlchemy engine for the database."""
        pass

    @abstractmethod
    def reflect_schema(self) -> None:
        """Reflect the database schema."""
        pass

    @abstractmethod
    def get_schema_info(self, include_sample_data: bool = False) -> Dict[str, Any]:
        """Retrieve schema information, optionally including sample data."""
        pass

    @abstractmethod
    def validate_and_sanitize_sql(self, raw_sql: str) -> str:
        """Validate and sanitize SQL queries for the specific database."""
        pass

    @abstractmethod
    def generate_pagination_syntax(self, limit: int) -> str:
        """Generate pagination syntax (e.g., LIMIT for PostgreSQL, TOP for MSSQL)."""
        pass

    @abstractmethod
    def get_case_insensitive_match(self, col_name: str, pattern: str) -> str:
        """Generate case-insensitive matching syntax."""
        pass

    @abstractmethod
    def execute_query(self, query: str, parameters: Optional[Dict[str, Any]] = None) -> QueryResult:
        """Execute a SQL query safely with parameters."""
        pass

    @abstractmethod
    def get_foreign_keys(self) -> List[Dict[str, Any]]:
        """Retrieve foreign key relationships."""
        pass

    @abstractmethod
    def close(self) -> None:
        """Clean up resources."""
        pass

    @abstractmethod
    def bind_parameters(self, sql: str, parameters: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
        """Bind parameters to the SQL query based on the database's syntax."""
        pass

    @abstractmethod
    def convert_data_type(self, column_type: str) -> str:
        """Convert generic data types to database-specific types."""
        pass

    @abstractmethod
    def handle_schema_features(self, table_info: Dict[str, Any]) -> Dict[str, Any]:
        """Handle database-specific schema features (e.g., JSONB, AUTO_INCREMENT)."""
        pass

    @abstractmethod
    def begin_transaction(self):
        """Begin a transaction."""
        pass

    @abstractmethod
    def commit_transaction(self):
        """Commit a transaction."""
        pass

    @abstractmethod
    def rollback_transaction(self):
        """Rollback a transaction."""
        pass

    @abstractmethod
    def normalize_error(self, error: Exception) -> str:
        """Normalize database-specific error messages into generic ones."""
        pass

    @abstractmethod
    def get_index_recommendations(self, table_name: str) -> List[str]:
        """Generate indexing recommendations for a table."""
        pass

    @abstractmethod
    def get_connection_properties(self) -> Dict[str, Any]:
        """Return database-specific connection properties."""
        pass

    @abstractmethod
    def supports_feature(self, feature_name: str) -> bool:
        """Check if the database supports a specific feature."""
        pass

    @abstractmethod
    def escape_identifier(self, identifier: str) -> str:
        """Escape table or column identifiers."""
        pass

    @abstractmethod
    def get_default_schema(self) -> str:
        """Return the default schema name."""
        pass

    @abstractmethod
    def add_batch_execute(self, query: str, data: List[Dict[str, Any]]) -> int:
        """Execute a batch query with multiple rows."""
        pass