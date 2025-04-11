#sql_agent_tool/cli/cli.py
import json
import re
import logging
import time
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
from functools import lru_cache

logger = logging.getLogger(__name__)


class SQLAgentTool:
    """A secure SQL tool for AI agents to interact with databases."""

    def __init__(self, config: DatabaseConfig, llmconfigs: LLMConfig, max_rows: int = 1000, read_only: bool = True):
        """
        Initialize the SQLAgentTool with database and LLM configurations.
        
        Args:
            config (DatabaseConfig): Configuration object for the database and LLM.
            max_rows (int): Maximum number of rows to return in query results.
            read_only (bool): Whether the tool should operate in read-only mode.
        """
        self.config = config
        self.llmconfigobj = llmconfigs

        # Dynamically initialize the LLM using the LLMFactory
        llm_config = LLMConfig(
            provider=llmconfigs.provider,
            api_key=llmconfigs.api_key,
            model=llmconfigs.model,
            temperature=llmconfigs.temperature,
            max_tokens=llmconfigs.max_tokens,
        )
        self.llm = LLMFactory.get_llm(llm_config)

        self.max_rows = max_rows
        self.read_only = read_only
        self.engine = self._create_engine()
        self.metadata = MetaData()
        self._reflect_schema()
        logger.info("SQLAgentTool initialized successfully")
        logger.info(f"Database connection established: {self.config.database}")
        logger.info(f"LLM initialized: {self.llmconfigobj.provider} ({self.llmconfigobj.model})")
        logger.info("Precaching schema information for performance")
        start_time = time.time()
        self.get_schema_info(include_sample_data=False)
        logger.info(f"Schema information cached in {time.time() - start_time:.2f} seconds")

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

    def _get_sample_data(self, table_name: str, sample_limit: int = 3) -> List[Dict]:
        """
        Safely get sample data from a table with proper error handling.
        
        Args:
            table_name (str): The name of the table to retrieve sample data from.
            sample_limit (int): The maximum number of rows to retrieve.
        
        Returns:
            List[Dict]: A list of dictionaries representing the sample rows.
        """
        try:
            # Use a safe SQL query to fetch sample data
            with self.engine.connect() as conn:
                result = conn.execute(text(f"SELECT * FROM {table_name} LIMIT {sample_limit}"))
                # Convert each row to a dictionary using _mapping for safer conversion
                return [dict(row._mapping) for row in result]
        except Exception as e:
            # Log the error and return an empty list
            logger.warning(f"Could not get sample data for {table_name}: {str(e)}")
            return []

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
                                # Handle datetime objects
                                if hasattr(value, 'isoformat'):
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

        logger.info("Schema information retrieved successfully")
        return schema
    
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
            # Call the LLM (assuming it returns an LLMResponse object from Suggestion 1)
            response = self.llm.generate_sql(prompt)  # Using generate_sql as it’s the interface method
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
            for fk in schema_info['foreign_keys']:
                if fk['table'] in relevant:
                    relevant.add(fk['referred_table'])
                elif fk['referred_table'] in relevant:
                    relevant.add(fk['table'])

            logger.debug(f"LLM-inferred relevant tables for request '{request}': {relevant}")
            return relevant

        except Exception as e:
            logger.error(f"Failed to infer relevant tables with LLM: {str(e)}")
            # Fallback to simple keyword matching if LLM fails
            request_lower = request.lower()
            fallback_relevant = set()
            for table in schema_info['tables']:
                if table in request_lower or any(col['name'] in request_lower for col in schema_info['tables'][table]['columns']):
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
        
    def _format_schema_for_prompt(self, schema_info: Dict[str, Any]) -> str:
        """Formats schema information for LLM prompt in a clear, structured way."""
        schema_text = []
        # Format tables
        for table_name, table_info in schema_info['tables'].items():
            # Format columns
            columns = []
            for col in table_info['columns']:
                col_desc = f"{col['name']} ({str(col['type'])})"
                if col['name'] in table_info.get('primary_key', []):
                    col_desc += " [PK]"
                if not col['nullable']:
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
                    f"{fk['table']}.{', '.join(fk['constrained_columns'])} → "
                    f"{fk['referred_table']}.{', '.join(fk['referred_columns'])}"
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
                    col_type = str(col['type']).lower()
                    # Look for name, text, or string-like columns
                    if ('name' in col_name or 'text' in col_name or 
                        'desc' in col_name or 'email' in col_name or
                        'varchar' in col_type or 'char' in col_type or 'text' in col_type):
                        text_field_examples.append(f"""
                        -- Example: Finding '{table_name}' by '{col_name}' pattern
                        SELECT * FROM {table_name}
                        WHERE {col_name} ILIKE :search_pattern
                        LIMIT 100
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
            FROM {tables[0]} a
            LEFT JOIN {tables[1]} b ON a.id = b.{tables[0]}_id
            GROUP BY a.id, a.name
            LIMIT 100
            -- For request: "Show count of {tables[1]} for each {tables[0]}"
            """)
        if tables:
            examples.append(f"""
            -- Example: Filtered query with parameters
            SELECT * FROM {tables[0]}
            WHERE created_at > :start_date AND status = :status
            ORDER BY created_at DESC
            LIMIT 50
            -- For request: "Show {tables[0]} with status active created after January 1st"
            -- Parameters: start_date = "2024-01-01", status = "active"
            """)
        return "\n".join(examples).strip()
        
        
    def _create_sql_generation_prompt(self, request: str, schema_info: Dict[str, Any]) -> str:
        """Enhanced prompt for generating SQL from natural language queries.
           now use filtered schema to decrease the size of the prompt.
        """
        relevent_tables = self._infer_relevant_tables(request, schema_info)
        filtered_schema ={
            'tables': {k: v for k, v in schema_info['tables'].items() if k in relevent_tables},
            'foreign_keys': [fk for fk in schema_info['foreign_keys'] if fk['table'] in relevent_tables or fk['referred_table'] in relevent_tables],
            'database_type': schema_info['database_type'],
            'read_only': schema_info['read_only']
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
        Use LIKE '%value%' for flexible text searches when appropriate.
        Rules:
            1. Use parameterized queries with :param syntax
            2. Only use tables/columns from the schema
            3. {"No modifying commands (read-only mode)" if self.read_only else "Be careful with modifications"}
            4. Add LIMIT {self.max_rows} if returning many rows
            5. Use proper JOIN syntax
            6. Include brief comments
            7. Use {self.config.drivername} syntax
            8. Format cleanly with newlines
            9. For search queries like "find user named John", use LIKE or ILIKE with parameters
            10. For flexible text searches, use pattern matching (LIKE '%:param%')
        Natural Language Request: "{request}"
        Respond ONLY with the SQL query enclosed in ```sql markers.
        """
        return prompt

    def _validate_and_sanitize_sql(self, raw_sql: str) -> str:
        """
        Validate and sanitize SQL query with multiple safety checks.
        
        Args:
            raw_sql (str): The raw SQL query to validate and sanitize.
        
        Returns:
            str: The sanitized SQL query.
        """
        # Remove comments first
        sql = re.sub(r'--.*?$', '', raw_sql, flags=re.MULTILINE)
        sql = re.sub(r'/\*.*?\*/', '', sql, flags=re.DOTALL)

        # Basic SQL injection checks
        forbidden_patterns = [
            r'(DROP\s+TABLE)',
            r'(DELETE\s+FROM)',
            r'(UPDATE\s+\w+\s+SET)',
            r'(ALTER\s+TABLE)',
            r'(CREATE\s+TABLE)',
            r'(INSERT\s+INTO)',
            r'(TRUNCATE\s+TABLE)',
            r'(;\s*--)',  # SQL comment after statement
            r'(;\s*[^\s])',  # Multiple statements
            r'(EXEC\s*\(?)',
            r'(UNION\s+ALL\s+SELECT)',
            r'(SELECT\s+\*\s+FROM\s+INFORMATION_SCHEMA)'
        ]

        if self.read_only:
            for pattern in forbidden_patterns:
                if re.search(pattern, sql, re.IGNORECASE):
                    raise ValueError(f"Query contains forbidden pattern: {pattern}")

        # Parse and validate SQL structure
        self._validate_query(sql)

        # Add LIMIT if not present (for SELECT queries)
        if (sql.upper().startswith('SELECT') and 
            'LIMIT' not in sql.upper() and 
            'TOP' not in sql.upper()):
            sql = sql.rstrip(';').strip() + f" LIMIT {self.max_rows}"

        return sql
    
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
            #ensure wildcards for ILike
            for key, value in params.items():
                if 'ILIKE' in sql.upper() and '%' not in value:
                    params[key] = f'%{value}%'
            logger.info("Extracted parameters: %s", json.dumps(params))
            # print(f"Extracted parameters: {params}")
            # print(f"SQL with parameters: {sql}")
            return sql, params
        except Exception as e:
            logger.error(f"Parameter extraction failed: {str(e)}")
            raise ValueError(f"Failed to extract parameters: {str(e)}")

    def generate_sql_from_natural_language(self, request: str, **kwargs) -> Tuple[str, Dict[str, Any]]:
        """Generate SQL from natural language using LLM with safety checks."""
        schema_info = self.get_schema_info(include_sample_data=False)
        prompt = self._create_sql_generation_prompt(request, schema_info)
        try:
            generated_sql = self._call_llm_for_sql(prompt, **kwargs)
            sql, params = self._extract_parameters(generated_sql, request)
            safe_sql = self._validate_and_sanitize_sql(sql)
            return safe_sql, params
        except ValueError as e:
            raise LLMGenerationError(prompt=prompt, error_detail=str(e))

    def _validate_query(self, query: str) -> None:
        """
        Perform comprehensive query validation.
        
        Args:
            query (str): The SQL query to validate.
        
        Raises:
            SQLValidationError: If the query fails validation.
        """
        if self.read_only:
            forbidden_commands = [
                'INSERT', 'UPDATE', 'DELETE', 'DROP', 'ALTER',
                'CREATE', 'TRUNCATE', 'GRANT', 'REVOKE'
            ]
            upper_query = query.upper()
            for cmd in forbidden_commands:
                if re.search(rf'\b{cmd}\b', upper_query):
                    raise SQLValidationError(query=query, reason=f"{cmd} commands not allowed in read-only mode")

        try:
            parsed = sqlparse.parse(query)
            if not parsed:
                raise SQLValidationError(query=query, reason="Failed to parse SQL syntax")
            if len(parsed) > 1:
                raise SQLValidationError(query=query, reason="Multiple statements not allowed")
        except Exception as e:
            raise SQLValidationError(query=query, reason=str(e))

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
        self.engine.dispose()
        logger.info("Database connection pool closed")