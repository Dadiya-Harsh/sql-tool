# sql_agent_tool/core.py
import json
import re
import logging
import time
from typing import Dict, List, Any, Optional, Tuple
from sqlalchemy.exc import SQLAlchemyError
import sqlparse

from .llm.base import LLMInterface
from .models import DatabaseConfig, QueryResult, LLMConfig
from .exceptions import (
    LLMGenerationError,
    QueryExecutionError,
    SQLValidationError,
    ParameterExtractionError,
    SchemaReflectionError,
)
from .llm.factory import LLMFactory
from .database.factory import DatabaseFactory  # Import the DatabaseFactory
from functools import lru_cache

logger = logging.getLogger(__name__)


class SQLAgentTool:
    """A secure SQL tool for AI agents to interact with databases."""

    def __init__(self, config: DatabaseConfig, llmconfigs: LLMConfig, max_rows: int = 1000, read_only: bool = True):
        """
        Initialize the SQLAgentTool with database and LLM configurations.
        
        Args:
            config (DatabaseConfig): Configuration object for the database.
            llmconfigs (LLMConfig): Configuration object for the LLM.
            max_rows (int): Maximum number of rows to return in query results.
            read_only (bool): Whether the tool should operate in read-only mode.
        """
        self.config = config
        self.llmconfigobj = llmconfigs
        self.max_rows = max_rows
        self.read_only = read_only

        # Dynamically initialize the LLM using the LLMFactory
        llm_config = LLMConfig(
            provider=llmconfigs.provider,
            api_key=llmconfigs.api_key,
            model=llmconfigs.model,
            temperature=llmconfigs.temperature,
            max_tokens=llmconfigs.max_tokens,
        )
        self.llm = LLMFactory.get_llm(llm_config)

        # Initialize the appropriate database implementation
        self.db = DatabaseFactory.get_database(config)
        
        # Create engine and reflect schema
        self.db.create_engine()
        self.db.reflect_schema()
        
        logger.info("SQLAgentTool initialized successfully")
        logger.info(f"Database connection established: {self.config.database}")
        logger.info(f"LLM initialized: {self.llmconfigobj.provider} ({self.llmconfigobj.model})")
        logger.info("Precaching schema information for performance")
        start_time = time.time()
        self.get_schema_info(include_sample_data=False)
        logger.info(f"Schema information cached in {time.time() - start_time:.2f} seconds")

    @lru_cache(maxsize=1)
    def get_schema_info(self, include_sample_data: bool = False, sample_limit: int = 3) -> Dict[str, Any]:
        """
        Get comprehensive schema information with robust sample data handling.
        
        Args:
            include_sample_data (bool): Whether to include sample data for tables.
            sample_limit (int): The maximum number of rows to include as sample data.
        
        Returns:
            Dict[str, Any]: A dictionary containing schema information.
        """
        try:
            schema_info = self.db.get_schema_info(include_sample_data=include_sample_data)
            # Ensure the schema has all required fields for compatibility
            if 'read_only' not in schema_info:
                schema_info['read_only'] = self.read_only
            if 'database_type' not in schema_info:
                schema_info['database_type'] = self.config.drivername
            return schema_info
        except Exception as e:
            raise SchemaReflectionError(
                database=self.config.database,
                error_detail=str(e),
            )
    
    def _create_table_inference_prompt(self, request: str, schema_info: Dict[str, Any]) -> str:
        """Create a prompt for the LLM to infer relevant tables."""
        table_summaries = []
        for table_name, table_info in schema_info['tables'].items():
            columns = [col['name'] for col in table_info['columns']]
            table_summaries.append(f"- {table_name}: Columns: {', '.join(columns)}")
        
        prompt = f"""
        Given the following database schema and a natural language request, identify the tables that are most relevant to answering the request. Return your answer as a JSON list of table names only (e.g., ```json\n["table1", "table2"]\n```).

        Schema:
        {chr(10).join(table_summaries)}

        Natural Language Request: "{request}"

        Task:
        - Analyze the request and schema.
        - Select tables that contain data needed to fulfill the request.
        - Consider relationships (e.g., joins) if applicable.
        - Respond with a JSON list of table names enclosed in ```json markers.
        """
        return prompt
    
    def _infer_relevant_tables(self, request: str, schema_info: Dict[str, Any]) -> set:
        """
        Infer tables relevant to the natural language request using an LLM.
        
        Args:
            request (str): The natural language query.
            schema_info (Dict[str, Any]): Full schema information.
        
        Returns:
            set: Set of relevant table names.
        """
        prompt = self._create_table_inference_prompt(request, schema_info)
        try:
            # Call the LLM
            response = self.llm.generate_sql(prompt)
            generated_content = response.content.strip()

            # Extract JSON from the response
            match = re.search(r'```json\s*(.*?)\s*```', generated_content, re.DOTALL)
            if not match:
                logger.warning(f"No JSON found in LLM response for table inference: {generated_content}")
                return set()  # Fallback to empty set

            json_str = match.group(1).strip()
            table_list = json.loads(json_str)
            if not isinstance(table_list, list):
                raise ValueError("LLM response is not a list")

            # Validate table names against schema
            relevant = set()
            all_tables = set(schema_info['tables'].keys())
            for table in table_list:
                if table in all_tables:
                    relevant.add(table)
                else:
                    logger.warning(f"LLM suggested invalid table: {table}")

            # Expand with related tables via foreign keys
            for fk in schema_info.get('foreign_keys', []):
                if fk['constrained_table'] in relevant:
                    relevant.add(fk['referred_table'])
                elif fk['referred_table'] in relevant:
                    relevant.add(fk['constrained_table'])

            logger.debug(f"LLM-inferred relevant tables for request '{request}': {relevant}")
            return relevant

        except Exception as e:
            logger.error(f"Failed to infer relevant tables with LLM: {str(e)}")
            # Fallback to simple keyword matching if LLM fails
            request_lower = request.lower()
            fallback_relevant = set()
            for table in schema_info['tables']:
                if table.lower() in request_lower or any(col['name'].lower() in request_lower for col in schema_info['tables'][table]['columns']):
                    fallback_relevant.add(table)
            logger.info(f"Using fallback method, relevant tables: {fallback_relevant}")
            return fallback_relevant

    def process_natural_language_query(self, query: str) -> QueryResult:
        """Process a natural language query from start to finish."""
        try:
            sql, params = self.generate_sql_from_natural_language(query)
            print(f"Generated SQL: {sql}")
            print(f"Parameters: {params}")
            logger.info(f"Generated SQL: {sql}")
            logger.info(f"Parameters: {params}")
            return self.db.execute_query(sql, parameters=params)
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
        
    def _format_schema_for_prompt(self, schema_info: Dict[str, Any]) -> str:
        """Formats schema information for LLM prompt in a clear, structured way."""
        schema_text = []
        # Format tables
        for table_name, table_info in schema_info['tables'].items():
            # Format columns
            columns = []
            for col in table_info['columns']:
                col_desc = f"{col['name']} ({str(col['type'])})"
                if 'primary_key' in table_info and col['name'] in table_info.get('primary_key', []):
                    col_desc += " [PK]"
                if 'nullable' in col and not col['nullable']:
                    col_desc += " [NOT NULL]"
                columns.append(col_desc)
            # Format table description
            table_desc = [
                f"Table: {table_name}",
                f"Columns: {', '.join(columns)}"
            ]
            # Add primary key if exists
            if table_info.get('primary_key'):
                table_desc.append(f"Primary Key: {', '.join(table_info['primary_key'])}")
            # Add sample data if available
            if table_info.get('sample_data'):
                samples = table_info.get('sample_data', [])
                if samples:
                    sample_str = "\nSample Data:"
                    for row in samples:
                        sample_str += f"\n  {json.dumps(row)}"
                    table_desc.append(sample_str)
            schema_text.append("\n".join(table_desc))
        # Format foreign key relationships
        if schema_info.get('foreign_keys'):
            fk_text = ["\nForeign Key Relationships:"]
            for fk in schema_info['foreign_keys']:
                fk_text.append(
                    f"{fk.get('constrained_table')}.{', '.join(fk.get('constrained_column', []) if isinstance(fk.get('constrained_column'), list) else [fk.get('constrained_column', '')])}"
                    f" → {fk.get('referred_table')}.{', '.join(fk.get('referred_column', []) if isinstance(fk.get('referred_column'), list) else [fk.get('referred_column', '')])}"
                )
            schema_text.append("\n".join(fk_text))
        return "\n".join(schema_text)
    
    def _get_example_queries(self, schema_info: Dict[str, Any]) -> str:
        """Generate example queries based on schema, including natural language searches."""
        examples = []
        tables = list(schema_info['tables'].keys())
        # Add general example for natural language searching
        if tables:
            # Find a table that might have a name or text field
            text_field_examples = []
            for table_name, table_info in schema_info['tables'].items():
                for col in table_info['columns']:
                    col_name = col['name'].lower()
                    col_type = str(col.get('type', '')).lower()
                    # Look for name, text, or string-like columns
                    if ('name' in col_name or 'text' in col_name or 
                        'desc' in col_name or 'email' in col_name or
                        'varchar' in col_type or 'char' in col_type or 'text' in col_type):
                        # Use database-specific case-insensitive match syntax
                        match_syntax = self.db.get_case_insensitive_match(col['name'], ":search_pattern")
                        text_field_examples.append(f"""
                        -- Example: Finding '{table_name}' by '{col_name}' pattern
                        SELECT * FROM {self.db.escape_identifier(table_name)}
                        WHERE {match_syntax}
                        {self.db.generate_pagination_syntax(100)}
                        -- For request: "find {table_name} with {col_name} containing example"
                        -- Parameter: search_pattern = "%example%"
                        """)
                        break
            if text_field_examples:
                examples.extend(text_field_examples[:2])  # Limit to 2 examples
        if len(tables) >= 2:
            examples.append(f"""
            -- Example: Join between {tables[0]} and {tables[1]}
            SELECT a.id, a.name, COUNT(b.id) as count
            FROM {self.db.escape_identifier(tables[0])} a
            LEFT JOIN {self.db.escape_identifier(tables[1])} b ON a.id = b.{tables[0]}_id
            GROUP BY a.id, a.name
            {self.db.generate_pagination_syntax(100)}
            -- For request: "Show count of {tables[1]} for each {tables[0]}"
            """)
        if tables:
            examples.append(f"""
            -- Example: Filtered query with parameters
            SELECT * FROM {self.db.escape_identifier(tables[0])}
            WHERE created_at > :start_date AND status = :status
            ORDER BY created_at DESC
            {self.db.generate_pagination_syntax(50)}
            -- For request: "Show {tables[0]} with status active created after January 1st"
            -- Parameters: start_date = "2024-01-01", status = "active"
            """)
        return "\n".join(examples).strip()
        
    def _create_sql_generation_prompt(self, request: str, schema_info: Dict[str, Any]) -> str:
        """Enhanced prompt for generating SQL from natural language queries.
           Uses filtered schema to decrease the size of the prompt.
        """
        relevant_tables = self._infer_relevant_tables(request, schema_info)
        filtered_schema = {
            'tables': {k: v for k, v in schema_info['tables'].items() if k in relevant_tables},
            'foreign_keys': [fk for fk in schema_info.get('foreign_keys', []) 
                          if fk.get('constrained_table') in relevant_tables or fk.get('referred_table') in relevant_tables],
            'database_type': schema_info.get('database_type', self.config.drivername),
            'read_only': schema_info.get('read_only', self.read_only)
        }

        schema_text = self._format_schema_for_prompt(filtered_schema)
        # Include example queries for better results
        example_queries = self._get_example_queries(filtered_schema)
        prompt = f"""
        Database Schema:
        {schema_text}
        Example Queries:
        {example_queries}
        Task: Convert the following natural language request into a safe, parameterized SQL query.
        Use appropriate syntax for {self.config.drivername} database for text searches.
        Rules:
            1. Use parameterized queries with :param syntax
            2. Only use tables/columns from the schema
            3. {"No modifying commands (read-only mode)" if self.read_only else "Be careful with modifications"}
            4. Add appropriate pagination syntax
            5. Use proper JOIN syntax
            6. Include brief comments
            7. Use {self.config.drivername} syntax
            8. Format cleanly with newlines
            9. For search queries like "find user named John", use appropriate case-insensitive matching with parameters
            10. For text searches, use appropriate pattern matching syntax for {self.config.drivername}
        Natural Language Request: "{request}"
        Respond ONLY with the SQL query enclosed in ```sql markers.
        """
        return prompt

    def generate_sql_from_natural_language(self, request: str, **kwargs) -> Tuple[str, Dict[str, Any]]:
        """Generate SQL from natural language using LLM with safety checks."""
        schema_info = self.get_schema_info(include_sample_data=False)
        prompt = self._create_sql_generation_prompt(request, schema_info)
        try:
            generated_sql = self._call_llm_for_sql(prompt, **kwargs)
            sql, params = self._extract_parameters(generated_sql, request)
            safe_sql = self.db.validate_and_sanitize_sql(sql)
            return safe_sql, params
        except ValueError as e:
            raise LLMGenerationError(prompt=prompt, error_detail=str(e))

    def _call_llm_for_parameters(self, sql: str, request: str, schema_text: str) -> Dict[str, Any]:
        """
        Enhanced parameter extraction to better handle general natural language queries.
        
        Args:
            sql (str): SQL query with parameter placeholders.
            request (str): Natural language request.
            schema_text (str): Formatted database schema information.
        
        Returns:
            Dict[str, Any]: Dictionary of parameters with inferred values.
        """
        # Construct a robust prompt for parameter extraction
        prompt = f"""
        Database Schema:
        {schema_text}
        Generated SQL Query:
        ```sql
        {sql}
        ```
        Natural Language Request:
        "{request}"
        Task:
        Extract all parameters from the SQL query and find their values in the natural language request.
        Parameters in the SQL are prefixed with ':' (e.g., :name, :user_id).
        For each parameter:
            1. Find the most likely value from the natural language request
            2. Convert to appropriate data type (string, number, date, etc.)
            3. For text search parameters, extract just the core value (not the wildcards)
        Example Request: "Find me users with email containing gmail"
        Example SQL: SELECT * FROM users WHERE email LIKE :email_pattern
        Parameter extraction: {{"email_pattern": "%gmail%"}}
        Example Request: "Show me users named John"
        Example SQL: SELECT * FROM users WHERE name ILIKE :name_pattern
        Parameter extraction: {{"name_pattern": "%John%"}}
        Example Request: "Get product with id 123"
        Example SQL: SELECT * FROM products WHERE id = :product_id
        Parameter extraction: {{"product_id": 123}}
        Return ONLY a valid JSON object with parameter names as keys and extracted values:
        ```json
        {{"param1": "value1", "param2": 42, ...}}
        ```
        """
        try:
            # Call the LLM to generate the parameters
            start_time = time.time()
            response = self.llm.generate_sql(prompt)
            logger.info(f"LLM parameter extraction took: {time.time() - start_time:.2f} seconds")
            generated_content = response.content.strip()

            # Extract JSON from the response
            match = re.search(r'```json\s*(.*?)\s*```', generated_content, re.DOTALL)
            if match:
                json_str = match.group(1).strip()
                try:
                    params = json.loads(json_str)
                    if not isinstance(params, dict):
                        raise ValueError("JSON response is not a dictionary")
                    return params
                except json.JSONDecodeError:
                    logger.error("Failed to parse JSON from LLM response")
                    return {}
            else:
                logger.error("No JSON found in LLM response")
                return {}
        except Exception as e:
            logger.error(f"Failed to call LLM for parameters: {str(e)}")
            raise ValueError(f"LLM parameter extraction failed: {str(e)}")
    
    def _extract_parameters(self, sql: str, request: Optional[str] = None) -> Tuple[str, Dict[str, Any]]:
        """
        Extract parameters from SQL and infer values from the natural language request.
        
        Args:
            sql (str): SQL query with parameter placeholders.
            request (Optional[str]): Natural language request.
        
        Returns:
            Tuple[str, Dict[str, Any]]: The SQL query and a dictionary of extracted parameters.
        """
        # Handle case where there are no parameters or no request
        if not request or ':' not in sql:
            return sql, {}

        # Extract all parameter placeholders from the SQL
        param_matches = re.findall(r':(\w+)', sql)
        if not param_matches:
            return sql, {}

        # For each parameter, use LLM to determine value from request
        schema_info = self.get_schema_info(include_sample_data=False)
        schema_text = self._format_schema_for_prompt(schema_info)
        try:
            # Use LLM to extract parameters
            params = self._call_llm_for_parameters(sql, request, schema_text)
            
            # Apply database-specific parameter binding
            sql, params = self.db.bind_parameters(sql, params)
            
            logger.info("Extracted parameters: %s", json.dumps(params))
            return sql, params
        except Exception as e:
            logger.error(f"Parameter extraction failed: {str(e)}")
            raise ValueError(f"Failed to extract parameters: {str(e)}")

    def _call_llm_for_sql(self, prompt: str, **kwargs) -> str:
        """Call the LLM to generate SQL from natural language."""
        try:
            start_time = time.time()
            response = self.llm.generate_sql(prompt)  # Use the dynamically selected LLM
            logger.info(f"LLM SQL generation took: {time.time() - start_time:.2f} seconds")
            sql_query = self._extract_sql_from_response(response.content)
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
        self.db.close()
        logger.info("Database connection closed")