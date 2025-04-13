import re
from sqlalchemy import create_engine, MetaData, text
import sqlalchemy
from sqlalchemy.orm import Session
from psycopg2 import DatabaseError, Error as Psycopg2Error
import sqlparse
from sql_agent_tool.database.database_base import DatabaseBase
from typing import Dict, Any, List, Optional, Tuple
import logging
import sys
import os
# Add project root to Python path
sys.path.append(r'E:\Wappnet internship\sql-tool')
from sql_agent_tool.models import DatabaseConfig, QueryResult
import logging
logger = logging.getLogger(__name__)
logging.basicConfig(filename="postgres.log", level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


class PostgreSQLDatabase(DatabaseBase):
    def __init__(self, config: DatabaseConfig):
        super().__init__(config)
        self.engine = None
        self.metadata = None
        self.session = None

    def create_engine(self) -> 'sqlalchemy.engine.Engine':
        """Create a SQLAlchemy engine for PostgreSQL with configurable options."""
        if not self.engine:
            engine_options = getattr(self.config, 'engine_options', {
                'pool_size': 5,
                'max_overflow': 10,
                'pool_timeout': 30
            })
            self.engine = create_engine(self.config.build_connection_string(), **engine_options)
            logger.info("PostgreSQL engine created")
        return self.engine

    def reflect_schema(self) -> None:
        """Reflect the PostgreSQL database schema into SQLAlchemy metadata, only if not already reflected."""
        if self.metadata is None:
            self.metadata = MetaData()
            self.metadata.reflect(bind=self.create_engine())
            logger.info("Database schema reflected")

    def get_schema_info(self, include_sample_data: bool = False) -> Dict[str, Any]:
        """Retrieve schema information, optionally including sample data."""
        self.reflect_schema()
        schema_info = {"tables": {}}
        with self.create_engine().connect() as connection:
            for table_name, table in self.metadata.tables.items():
                columns = [{"name": col.name, "type": str(col.type)} for col in table.columns]
                schema_info["tables"][table_name] = {"columns": columns}
                if include_sample_data:
                    result = connection.execute(table.select().limit(5))
                    schema_info["tables"][table_name]["sample_data"] = [dict(row) for row in result.mappings()]
        return schema_info

    def validate_and_sanitize_sql(self, raw_sql: str, read_only: bool = False) -> str:
        """Validate and sanitize SQL queries for PostgreSQL."""
        parsed = sqlparse.parse(raw_sql)
        if not parsed:
            raise ValueError("Invalid SQL query")
        if len(parsed) > 1:
            raise ValueError("Multiple SQL statements are not allowed")
        stmt = parsed[0]
        cleaned_sql = str(stmt).strip()
        allowed_statements = ['SELECT'] if read_only else ['SELECT', 'INSERT', 'UPDATE', 'DELETE']
        stmt_type = stmt.get_type().upper()
        if stmt_type not in allowed_statements:
            raise ValueError(f"Only {', '.join(allowed_statements)} queries are allowed")
        logger.debug(f"Validated SQL: {cleaned_sql}")
        return cleaned_sql

    def generate_pagination_syntax(self, limit: int) -> str:
        """Generate pagination syntax for PostgreSQL (using LIMIT)."""
        return f"LIMIT {limit}"

    def get_case_insensitive_match(self, col_name: str, pattern: str) -> str:
        """Generate case-insensitive matching syntax for PostgreSQL (using ILIKE)."""
        return f"{self.escape_identifier(col_name)} ILIKE %s"

    def execute_query(self, query: str, parameters: Optional[Dict[str, Any]] = None) -> QueryResult:
        """Execute a SQL query safely with parameters."""
        logger.debug(f"Executing query: {query} with parameters: {parameters}")
        sanitized_query = self.validate_and_sanitize_sql(query, read_only=getattr(self, 'read_only', False))
        bound_query, bound_params = self.bind_parameters(sanitized_query, parameters or {})
        try:
            if not self.session:
                self.session = Session(self.create_engine())
            with self.session.begin():
                result = self.session.execute(text(bound_query), bound_params)
                data = result.mappings().all()
                return QueryResult(
                    data=data,
                    columns=list(result.keys()),
                    row_count=result.rowcount,
                    query=query,
                    success=True,
                    error=None
                )
        except Exception as e:
            if self.session:
                self.session.rollback()
            logger.error(f"Query execution failed: {str(e)}")
            return QueryResult(
                data=[],
                columns=[],
                row_count=0,
                query=query,
                success=False,
                error=self.normalize_error(e)
            )

    def get_foreign_keys(self) -> List[Dict[str, Any]]:
        """Retrieve foreign key relationships from PostgreSQL."""
        self.reflect_schema()
        foreign_keys = []
        for table_name, table in self.metadata.tables.items():
            for fk in table.foreign_keys:
                foreign_keys.append({
                    "constrained_table": table_name,
                    "constrained_column": fk.column.name,
                    "referred_table": fk.target_fullname.split('.')[0],
                    "referred_column": fk.target_fullname.split('.')[1]
                })
        return foreign_keys

    def close(self) -> None:
        """Clean up resources by closing the session and engine."""
        if self.session:
            self.session.close()
            self.session = None
        if self.engine:
            self.engine.dispose()
            self.engine = None
        self.metadata = None
        logger.info("PostgreSQL resources closed")


    def bind_parameters(self, sql: str, parameters: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
        """Bind parameters to the SQL query using PostgreSQL syntax."""
        placeholders = set(re.findall(r':(\w+)', sql))
        missing_params = placeholders - set(parameters.keys())
        if missing_params:
            raise ValueError(f"Missing parameters for placeholders: {missing_params}")
        return sql, parameters

    def convert_data_type(self, column_type: str) -> str:
        """Convert generic data types to PostgreSQL-specific types."""
        type_map = {
            "string": "VARCHAR",
            "integer": "INTEGER",
            "float": "FLOAT",
            "boolean": "BOOLEAN",
            "date": "DATE",
            "datetime": "TIMESTAMP"
        }
        return type_map.get(column_type.lower(), "VARCHAR")

    def handle_schema_features(self, table_info: Dict[str, Any]) -> Dict[str, Any]:
        """Handle PostgreSQL-specific schema features (e.g., JSONB)."""
        for column in table_info.get("columns", []):
            if column["type"] == "JSON":
                column["type"] = "JSONB"
        return table_info

    def begin_transaction(self):
        """Begin a transaction in PostgreSQL."""
        if not self.session:
            self.session = Session(self.create_engine())
        self.session.begin()

    def commit_transaction(self):
        """Commit a transaction in PostgreSQL."""
        if self.session:
            self.session.commit()

    def rollback_transaction(self):
        """Rollback a transaction in PostgreSQL."""
        if self.session:
            self.session.rollback()

    def normalize_error(self, error: Exception) -> str:
        """Normalize PostgreSQL-specific error messages into generic ones."""
        if isinstance(error, DatabaseError) and hasattr(error.orig, 'pgcode'):
            pg_error = error.orig
            return f"Database error: {pg_error.diag.message_primary} (PostgreSQL code: {pg_error.pgcode})"
        return f"Database error: {str(error)}"

    def get_index_recommendations(self, table_name: str) -> List[str]:
        """Generate indexing recommendations for a PostgreSQL table."""
        recommendations = []
        with self.create_engine().connect() as connection:
            result = connection.execute(text(f"EXPLAIN SELECT * FROM {table_name} WHERE 1=1"))
            recommendations.append(f"CREATE INDEX ON {table_name} (id)")  # Example
        return recommendations

    def get_connection_properties(self) -> Dict[str, Any]:
        """Return PostgreSQL-specific connection properties."""
        return {"max_connections": 100, "timeout": 30}

    def supports_feature(self, feature_name: str) -> bool:
        """Check if PostgreSQL supports a specific feature."""
        features = {"jsonb": True, "window_functions": True, "common_table_expressions": True}
        return features.get(feature_name.lower(), False)

    def escape_identifier(self, identifier: str) -> str:
        """Escape table or column identifiers with double quotes for PostgreSQL."""
        escaped = identifier.replace('"', '""')  # Replace outside f-string
        return f'"{escaped}"'

    def get_default_schema(self) -> str:
        """Return the default schema name for PostgreSQL."""
        return "public"

    def add_batch_execute(self, query: str, data: List[Dict[str, Any]]) -> int:
        """Execute a batch query with multiple rows in PostgreSQL."""
        try:
            with self.create_engine().connect() as connection:
                connection.execute(text(query), data)
                connection.commit()
                return len(data)
        except Exception as e:
            raise ValueError(f"Batch execution failed: {self.normalize_error(e)}")

if __name__ == "__main__":
    # Example usage
    config = DatabaseConfig(
        drivername="postgresql",  # Added drivername (required by DatabaseConfig)
        username="postgres",
        password="password",
        host="localhost",
        port=5433,  # Corrected to 5432 (PostgreSQL default is 5432, not 543)
        database="P1"
    )
    db = PostgreSQLDatabase(config)
    db.create_engine()
    schema_info = db.get_schema_info(include_sample_data=True)
    print(schema_info)
    db.close()