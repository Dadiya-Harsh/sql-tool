import json
import re
import logging
from typing import Dict, List, Any, Optional, Tuple
import sqlalchemy
import sqlparse
from sqlalchemy import create_engine, inspect, MetaData, text
from sqlalchemy.exc import SQLAlchemyError
from .llm.base import LLMInterface
from .models import DatabaseConfig, QueryResult, LLMConfig
from .exceptions import (
    LLMGenerationError,
    QueryExecutionError,
    SQLValidationError,
    ParameterExtractionError,
    SchemaReflectionError,
)
from .llm.factory import LLMFactory  # Import the LLMFactory

logger = logging.getLogger(__name__)


class SQLAgentTool:
    """A secure SQL tool for AI agents to interact with databases."""

    def __init__(self, config: DatabaseConfig, max_rows: int = 1000, read_only: bool = True):
        """
        Initialize the SQLAgentTool with database and LLM configurations.
        
        Args:
            config (DatabaseConfig): Configuration object for the database and LLM.
            max_rows (int): Maximum number of rows to return in query results.
            read_only (bool): Whether the tool should operate in read-only mode.
        """
        self.config = config

        # Dynamically initialize the LLM using the LLMFactory
        llm_config = LLMConfig(
            provider=config.llm_provider,
            api_key=config.llm_api_key,
            model=config.llm_model,
            temperature=config.llm_temperature,
            max_tokens=config.llm_max_tokens,
        )
        self.llm = LLMFactory.get_llm(llm_config)

        self.max_rows = max_rows
        self.read_only = read_only
        self.engine = self._create_engine()
        self.metadata = MetaData()
        self._reflect_schema()

    def _create_engine(self) -> 'sqlalchemy.engine.Engine':
        """Create a SQLAlchemy engine for database connection."""
        connection_url = sqlalchemy.URL.create(
            drivername=self.config.drivername,
            username=self.config.username,
            password=self.config.password,
            host=self.config.host,
            port=self.config.port,
            database=self.config.database,
            query=self.config.query,
        )
        engine_args = {
            'pool_size': 5,
            'max_overflow': 10,
            'pool_timeout': 30,
            'pool_recycle': 3600,
            'echo': False,
        }
        if self.config.drivername == 'postgresql':
            engine_args['connect_args'] = {'sslmode': 'require' if self.config.require_ssl else 'prefer'}
        return create_engine(connection_url, **engine_args)

    def _reflect_schema(self) -> None:
        """Reflect the database schema."""
        try:
            self.metadata.reflect(bind=self.engine)
            logger.info("Successfully reflected database schema")
        except SQLAlchemyError as e:
            raise SchemaReflectionError(
                database=self.config.database,
                error_detail=str(e),
            )

    def get_schema_info(self, include_sample_data: bool = False, sample_limit: int = 3) -> Dict[str, Any]:
        """Get comprehensive schema information with robust sample data handling."""
        inspector = inspect(self.engine)
        schema = {
            'tables': {},
            'foreign_keys': [],
            'database_type': self.config.drivername,
            'read_only': self.read_only,
        }

        # Get table information
        for table_name in inspector.get_table_names():
            schema['tables'][table_name] = {
                'columns': [],
                'primary_key': inspector.get_pk_constraint(table_name).get('constrained_columns', []),
                'indexes': inspector.get_indexes(table_name),
                'sample_data': [],
            }

            # Get column information
            for column in inspector.get_columns(table_name):
                schema['tables'][table_name]['columns'].append({
                    'name': column['name'],
                    'type': str(column['type']),
                    'nullable': column['nullable'],
                    'default': column.get('default'),
                    'autoincrement': column.get('autoincrement', False),
                })

            # Get sample data if requested
            if include_sample_data:
                try:
                    sample_data = self._get_sample_data(table_name, sample_limit)
                    if sample_data:
                        clean_samples = []
                        for row in sample_data:
                            clean_row = {}
                            for key, value in row.items():
                                if hasattr(value, 'isoformat'):  # Handle datetime
                                    clean_row[key] = value.isoformat()
                                else:
                                    clean_row[key] = str(value) if value is not None else None
                            clean_samples.append(clean_row)
                        schema['tables'][table_name]['sample_data'] = clean_samples
                except Exception as e:
                    logger.warning(f"Could not process sample data for {table_name}: {str(e)}")

        # Get foreign key relationships
        for table_name in inspector.get_table_names():
            for fk in inspector.get_foreign_keys(table_name):
                schema['foreign_keys'].append({
                    'table': table_name,
                    'constrained_columns': fk['constrained_columns'],
                    'referred_table': fk['referred_table'],
                    'referred_columns': fk['referred_columns'],
                })

        return schema

    def process_natural_language_query(self, query: str) -> QueryResult:
        """Process a natural language query from start to finish."""
        try:
            sql, params = self.generate_sql_from_natural_language(query)
            logger.info(f"Generated SQL: {sql}")
            logger.info(f"Parameters: {params}")
            return self.execute_query(sql, parameters=params)
        except (
            SQLValidationError,
            ParameterExtractionError,
            LLMGenerationError,
            QueryExecutionError,
        ) as e:
            logger.error(f"Natural language query processing failed: {str(e)}")
            return QueryResult(
                data=[],
                columns=[],
                row_count=0,
                query=query,
                success=False,
                error=str(e),
            )

    def generate_sql_from_natural_language(self, request: str, **kwargs) -> Tuple[str, Dict[str, Any]]:
        """Generate SQL from natural language using LLM with safety checks."""
        schema_info = self.get_schema_info(include_sample_data=True, sample_limit=2)
        prompt = self._create_sql_generation_prompt(request, schema_info)
        try:
            generated_sql = self._call_llm_for_sql(prompt, **kwargs)
            sql, params = self._extract_parameters(generated_sql, request)
            safe_sql = self._validate_and_sanitize_sql(sql)
            return safe_sql, params
        except ValueError as e:
            raise LLMGenerationError(prompt=prompt, error_detail=str(e))

    def execute_query(self, query: str, parameters: Optional[Dict[str, Any]] = None) -> QueryResult:
        """Execute a SQL query safely with parameters."""
        try:
            self._validate_query(query)
            with self.engine.connect() as connection:
                stmt = text(query)
                if parameters:
                    result = connection.execute(stmt, parameters)
                else:
                    result = connection.execute(stmt)
                if result.returns_rows:
                    data = [dict(row._mapping) for row in result]
                    columns = list(result.keys())
                    return QueryResult(
                        data=data,
                        columns=columns,
                        row_count=len(data),
                        query=query,
                        success=True,
                    )
                else:
                    return QueryResult(
                        data=[],
                        columns=[],
                        row_count=result.rowcount,
                        query=query,
                        success=True,
                    )
        except SQLAlchemyError as e:
            raise QueryExecutionError(query=query, error_detail=str(e))
        except SQLValidationError as e:
            raise  # Re-raise validation errors directly

    def _call_llm_for_sql(self, prompt: str, **kwargs) -> str:
        """Call the LLM to generate SQL from natural language."""
        try:
            response = self.llm.generate_sql(prompt)  # Use the dynamically selected LLM
            sql_query = self._extract_sql_from_response(response)
            if not sql_query:
                raise LLMGenerationError(prompt=prompt, error_detail="No valid SQL generated")
            return sql_query
        except Exception as e:
            raise LLMGenerationError(prompt=prompt, error_detail=str(e))

    def _extract_sql_from_response(self, response: str) -> str:
        """Extract SQL query from LLM response enclosed in ```sql markers."""
        sql_match = re.search(r'```sql\s*(.*?)\s*```', response, re.DOTALL)
        if sql_match:
            sql = sql_match.group(1).strip()
            if not sql:
                raise LLMGenerationError(prompt="Unknown", error_detail="Empty SQL query in response")
            return sql
        raise LLMGenerationError(prompt="Unknown", error_detail="No SQL query found in LLM response")

    def close(self) -> None:
        """Clean up resources."""
        self.engine.dispose()
        logger.info("Database connection pool closed")