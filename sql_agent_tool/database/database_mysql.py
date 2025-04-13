# -*- coding: utf-8 -*-
# sql-agent-tool/databse/database_mysql_direct.py

# -*- coding: utf-8 -*-
# sql-agent-tool/database/database_mysql_direct.py

import re
import logging
import json
from typing import Dict, Any, List, Optional, Tuple
import pymysql
from pymysql.cursors import DictCursor
from sql_agent_tool.database.database_base import DatabaseBase
from sql_agent_tool.models import DatabaseConfig, QueryResult

logger = logging.getLogger(__name__)

class MySQLDatabase(DatabaseBase):
    def __init__(self, config: DatabaseConfig):
        super().__init__(config)
        self.connection = None
        self.schema_cache = None
        self.foreign_keys_cache = None
        self.in_transaction = False

    def create_engine(self) -> pymysql.connections.Connection:
        """Create a PyMySQL connection with configurable options."""
        try:
            if not self.connection or not self.connection.open:
                connection_options = {
                    'host': self.config.host,
                    'user': self.config.username,
                    'password': self.config.password,
                    'database': self.config.database,
                    'port': self.config.port or 3306,  # Default MySQL port if not specified
                    'charset': 'utf8mb4',
                    'cursorclass': DictCursor,
                    'autocommit': True
                }

                # Add any additional connection options from config
                engine_options = getattr(self.config, 'engine_options', {})
                if engine_options and isinstance(engine_options, dict):
                    if 'connect_timeout' in engine_options:
                        connection_options['connect_timeout'] = engine_options['connect_timeout']
                
                self.connection = pymysql.connect(**connection_options)
                logger.info(f"MySQL connection created to {self.config.host}:{self.config.port}")
            return self.connection
        except pymysql.Error as e:
            logger.error(f"Failed to create MySQL connection: {str(e)}")
            raise
    
    # Alias for create_engine to maintain compatibility with other implementations
    def create_connection(self) -> pymysql.connections.Connection:
        """Alias for create_engine to maintain API compatibility."""
        return self.create_engine()
    
    def reflect_schema(self) -> None:
        """Reflect the database schema - required by the abstract base class."""
        self._reflect_schema()
    
    def get_schema_info(self, include_sample_data: bool = False) -> Dict[str, Any]:
        """Retrieve schema information, optionally including sample data."""
        if self.schema_cache is None:
            self._reflect_schema()
            
        schema_info = {"tables": {}}
        
        for table_name in self.schema_cache:
            schema_info["tables"][table_name] = {
                "columns": self.schema_cache[table_name]
            }
            
            if include_sample_data:
                try:
                    connection = self.create_connection()
                    with connection.cursor() as cursor:
                        cursor.execute(f"SELECT * FROM {self.escape_identifier(table_name)} LIMIT 5")
                        results = cursor.fetchall()
                        # Convert to list of dicts for consistent serialization
                        sample_data = []
                        for row in results:
                            # Handle non-serializable types
                            clean_row = {}
                            for k, v in row.items():
                                if isinstance(v, (bytes, bytearray)):
                                    clean_row[k] = v.hex()
                                else:
                                    clean_row[k] = v
                            sample_data.append(clean_row)
                        schema_info["tables"][table_name]["sample_data"] = sample_data
                except Exception as e:
                    logger.warning(f"Failed to fetch sample data for {table_name}: {str(e)}")
                    schema_info["tables"][table_name]["sample_data"] = []
                    
        return schema_info
    
    def _reflect_schema(self) -> None:
        """Reflect the MySQL database schema by querying information_schema."""
        self.schema_cache = {}
        connection = self.create_connection()
        
        try:
            with connection.cursor() as cursor:
                # Get list of tables
                cursor.execute("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = %s
                    AND table_type = 'BASE TABLE'
                """, (self.config.database,))
                
                tables = [row['table_name'] for row in cursor.fetchall()]
                
                # Get column information for each table
                for table_name in tables:
                    cursor.execute("""
                        SELECT 
                            column_name, 
                            data_type,
                            is_nullable,
                            column_key,
                            extra,
                            column_default
                        FROM information_schema.columns
                        WHERE table_schema = %s AND table_name = %s
                        ORDER BY ordinal_position
                    """, (self.config.database, table_name))
                    
                    columns = []
                    for col in cursor.fetchall():
                        columns.append({
                            "name": col['column_name'],
                            "type": col['data_type'],
                            "nullable": col['is_nullable'] == 'YES',
                            "primary_key": col['column_key'] == 'PRI',
                            "autoincrement": 'auto_increment' in col['extra'].lower() if col['extra'] else False,
                            "default": col['column_default']
                        })
                    
                    self.schema_cache[table_name] = columns
            
            logger.info(f"Database schema reflected: {len(self.schema_cache)} tables found")
        except Exception as e:
            logger.error(f"Failed to reflect schema: {str(e)}")
            raise
    
    def validate_and_sanitize_sql(self, raw_sql: str, read_only: bool = False) -> str:
        """Validate and sanitize SQL queries for MySQL."""
        try:
            import sqlparse
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
        except ImportError:
            # Fallback if sqlparse is not available
            logger.warning("sqlparse not available, performing basic SQL validation")
            cleaned_sql = raw_sql.strip()
            stmt_type = cleaned_sql.split(' ')[0].upper()
            allowed_statements = ['SELECT'] if read_only else ['SELECT', 'INSERT', 'UPDATE', 'DELETE']
            if stmt_type not in allowed_statements:
                raise ValueError(f"Only {', '.join(allowed_statements)} queries are allowed")
            return cleaned_sql
    
    def generate_pagination_syntax(self, limit: int, offset: int = 0) -> str:
        """Generate pagination syntax for MySQL (using LIMIT and OFFSET)."""
        return f"LIMIT {limit} OFFSET {offset}" if offset > 0 else f"LIMIT {limit}"
    
    def get_case_insensitive_match(self, col_name: str, pattern: str) -> str:
        """Generate case-insensitive matching syntax for MySQL (using LIKE)."""
        return f"{self.escape_identifier(col_name)} LIKE %s"
    
    def bind_parameters(self, sql: str, parameters: Dict[str, Any]) -> Tuple[str, List[Any]]:
        """Convert named parameters to PyMySQL positional parameters."""
        if not parameters:
            return sql, []
            
        # Find all named parameters in the SQL query
        named_params = re.findall(r':(\w+)', sql)
        if not named_params:
            return sql, []
            
        # Check for missing parameters
        for param in named_params:
            if param not in parameters:
                raise ValueError(f"Missing parameter value for placeholder :{param}")
        
        # Replace named parameters with PyMySQL placeholders (%)
        param_values = []
        for param in named_params:
            sql = sql.replace(f":{param}", "%s")
            param_values.append(parameters[param])
            
        return sql, param_values
    
    def execute_query(self, query: str, parameters: Optional[Dict[str, Any]] = None) -> QueryResult:
        """Execute a SQL query safely with parameters."""
        start_time = __import__('time').time()
        logger.debug(f"Executing query: {query} with parameters: {parameters}")
        try:
            sanitized_query = self.validate_and_sanitize_sql(query, read_only=getattr(self, 'read_only', False))
            
            if parameters:
                bound_query, bound_params = self.bind_parameters(sanitized_query, parameters)
            else:
                bound_query, bound_params = sanitized_query, []
                
            connection = self.create_connection()
            with connection.cursor() as cursor:
                cursor.execute(bound_query, bound_params)
                
                # Get column names
                columns = [col[0] for col in cursor.description] if cursor.description else []
                
                # Get result data
                data = cursor.fetchall() if cursor.description else []
                
                # Convert any non-serializable types to strings 
                serializable_data = []
                for row in data:
                    serialized_row = {}
                    for key, value in row.items():
                        if isinstance(value, (bytes, bytearray)):
                            serialized_row[key] = value.hex()
                        else:
                            serialized_row[key] = value
                    serializable_data.append(serialized_row)
                
                execution_time = __import__('time').time() - start_time
                return QueryResult(
                    data=serializable_data,
                    columns=columns,
                    row_count=cursor.rowcount,
                    query=query,
                    success=True,
                    error=None,
                    execution_time=execution_time
                )
        except Exception as e:
            if hasattr(self, 'in_transaction') and self.in_transaction:
                self.rollback_transaction()
            
            logger.error(f"Query execution failed: {str(e)}")
            execution_time = __import__('time').time() - start_time
            return QueryResult(
                data=[],
                columns=[],
                row_count=0,
                query=query,
                success=False,
                error=self.normalize_error(e),
                execution_time=execution_time
            )
    
    def get_foreign_keys(self) -> List[Dict[str, Any]]:
        """Retrieve foreign key relationships from MySQL."""
        if self.foreign_keys_cache is None:
            self.foreign_keys_cache = []
            connection = self.create_connection()
            
            try:
                with connection.cursor() as cursor:
                    cursor.execute("""
                        SELECT 
                            TABLE_NAME as constrained_table,
                            COLUMN_NAME as constrained_column,
                            REFERENCED_TABLE_NAME as referred_table,
                            REFERENCED_COLUMN_NAME as referred_column,
                            CONSTRAINT_NAME as constraint_name
                        FROM information_schema.KEY_COLUMN_USAGE
                        WHERE 
                            REFERENCED_TABLE_SCHEMA = %s
                            AND REFERENCED_TABLE_NAME IS NOT NULL
                    """, (self.config.database,))
                    
                    self.foreign_keys_cache = cursor.fetchall()
                    logger.info(f"Retrieved {len(self.foreign_keys_cache)} foreign key relationships")
            except Exception as e:
                logger.warning(f"Failed to retrieve foreign keys: {str(e)}")
        
        return self.foreign_keys_cache
    
    def close(self) -> None:
        """Clean up resources by closing the connection."""
        if hasattr(self, 'connection') and self.connection and hasattr(self.connection, 'open') and self.connection.open:
            self.connection.close()
            self.connection = None
            logger.info("MySQL connection closed")
        self.schema_cache = None
        self.foreign_keys_cache = None
    
    def convert_data_type(self, column_type: str) -> str:
        """Convert generic data types to MySQL-specific types."""
        type_map = {
            "string": "VARCHAR(255)",
            "text": "TEXT",
            "integer": "INT",
            "float": "FLOAT",
            "double": "DOUBLE",
            "decimal": "DECIMAL(10,2)",
            "boolean": "TINYINT(1)",
            "date": "DATE",
            "datetime": "DATETIME",
            "timestamp": "TIMESTAMP",
            "json": "JSON",
            "blob": "BLOB"
        }
        return type_map.get(column_type.lower(), "VARCHAR(255)")
    
    def handle_schema_features(self, table_info: Dict[str, Any]) -> Dict[str, Any]:
        """Handle MySQL-specific schema features (e.g., AUTO_INCREMENT, JSON)."""
        for column in table_info.get("columns", []):
            if column.get("type", "").lower() == "json":
                column["type"] = "JSON"
            if column.get("autoincrement"):
                column["type"] = f"{column['type']} AUTO_INCREMENT"
            if column.get("primary_key"):
                column["constraint"] = "PRIMARY KEY"
        return table_info
    
    def begin_transaction(self):
        """Begin a transaction in MySQL."""
        connection = self.create_connection()
        connection.begin()
        self.in_transaction = True
        logger.info("Transaction started")
    
    def commit_transaction(self):
        """Commit a transaction in MySQL."""
        if self.connection and self.in_transaction:
            self.connection.commit()
            self.in_transaction = False
            logger.info("Transaction committed")
    
    def rollback_transaction(self):
        """Rollback a transaction in MySQL."""
        if self.connection and self.in_transaction:
            self.connection.rollback()
            self.in_transaction = False
            logger.info("Transaction rolled back")
    
    def normalize_error(self, error: Exception) -> str:
        """Normalize MySQL-specific error messages into generic ones."""
        if isinstance(error, pymysql.err.OperationalError):
            # Handle connection errors
            error_code = getattr(error, 'args', (None,))[0]
            error_msg = str(error)
            if error_code == 2003:  # Can't connect to MySQL server
                return f"Connection error: Unable to connect to MySQL server. Check host, port, and network."
            elif error_code == 1045:  # Access denied for user
                return f"Authentication error: Access denied. Check username and password."
            elif error_code == 1049:  # Unknown database
                return f"Database error: Database '{self.config.database}' does not exist."
            return f"Operational error: {error_msg} (MySQL code: {error_code})"
        elif isinstance(error, pymysql.err.ProgrammingError):
            # Handle SQL syntax errors
            error_code = getattr(error, 'args', (None,))[0]
            error_msg = str(error)
            return f"SQL error: {error_msg} (MySQL code: {error_code})"
        elif isinstance(error, pymysql.Error):
            # Generic MySQL errors
            error_code = getattr(error, 'args', (None,))[0]
            error_msg = str(error)
            return f"Database error: {error_msg} (MySQL code: {error_code})"
        return f"Error: {str(error)}"
    
    def get_index_recommendations(self, table_name: str) -> List[str]:
        """Generate indexing recommendations for a MySQL table."""
        recommendations = []
        if not table_name:
            return recommendations
            
        connection = self.create_connection()
        
        try:
            # Get column information
            with connection.cursor() as cursor:
                # Check existing indices first
                cursor.execute("""
                    SELECT 
                        index_name,
                        column_name
                    FROM information_schema.statistics
                    WHERE 
                        table_schema = %s 
                        AND table_name = %s
                    ORDER BY index_name, seq_in_index
                """, (self.config.database, table_name))
                
                existing_indices = {}
                for row in cursor.fetchall():
                    idx_name = row['index_name']
                    if idx_name not in existing_indices:
                        existing_indices[idx_name] = []
                    existing_indices[idx_name].append(row['column_name'])
                
                # Get column information
                cursor.execute("""
                    SELECT 
                        column_name,
                        column_key,
                        data_type
                    FROM information_schema.columns
                    WHERE 
                        table_schema = %s 
                        AND table_name = %s
                """, (self.config.database, table_name))
                
                # Recommend indices for likely join or filter columns
                for col in cursor.fetchall():
                    # Skip columns already in an index
                    already_indexed = False
                    for idx_cols in existing_indices.values():
                        if col['column_name'] in idx_cols:
                            already_indexed = True
                            break
                    
                    if already_indexed:
                        continue
                        
                    # Recommend index for likely candidate columns
                    if (col['column_name'].lower().endswith('_id') or
                        col['column_name'].lower() in ('id', 'code', 'key', 'slug', 'status', 'type') or
                        col['data_type'] in ('varchar', 'char', 'int', 'bigint', 'date', 'datetime')):
                        
                        recommendations.append(
                            f"CREATE INDEX idx_{table_name}_{col['column_name']} ON {self.escape_identifier(table_name)} ({self.escape_identifier(col['column_name'])})"
                        )
            
            # Check for potential composite indices
            if len(recommendations) >= 2:
                fk_columns = [col for col in existing_indices.get('PRIMARY', []) 
                             if col.lower().endswith('_id')]
                if fk_columns:
                    recommendations.append(
                        f"CREATE INDEX idx_{table_name}_composite ON {self.escape_identifier(table_name)} ({', '.join([self.escape_identifier(col) for col in fk_columns])})"
                    )
        except Exception as e:
            logger.warning(f"Failed to generate index recommendations for {table_name}: {str(e)}")
            
        return recommendations
    
    def get_connection_properties(self) -> Dict[str, Any]:
        """Return MySQL-specific connection properties."""
        properties = {}
        connection = self.create_connection()
        
        try:
            with connection.cursor() as cursor:
                # Get system variables
                variables_to_fetch = [
                    'max_connections', 
                    'wait_timeout',
                    'max_allowed_packet',
                    'innodb_buffer_pool_size',
                    'version'
                ]
                
                placeholders = ', '.join(['%s'] * len(variables_to_fetch))
                cursor.execute(f"SHOW VARIABLES WHERE Variable_name IN ({placeholders})", variables_to_fetch)
                
                for row in cursor.fetchall():
                    properties[row['Variable_name']] = row['Value']
                
                # Get process list count
                cursor.execute("SELECT COUNT(*) AS connection_count FROM information_schema.processlist")
                properties["active_connections"] = cursor.fetchone()['connection_count']
                
        except Exception as e:
            logger.warning(f"Failed to fetch connection properties: {str(e)}")
            # Fallback with default values
            properties = {
                "max_connections": "151", 
                "wait_timeout": "28800",
                "version": "Unknown"
            }
            
        return properties
    
    def supports_feature(self, feature_name: str) -> bool:
        """Check if MySQL supports a specific feature."""
        connection = self.create_connection()
        
        feature_map = {
            "json": False,
            "window_functions": False,
            "common_table_expressions": False,
            "fulltext_search": False,
            "stored_procedures": False,
            "triggers": False,
            "views": False
        }
        
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT VERSION()")
                version_str = cursor.fetchone()['VERSION()']
                
                # Extract the major and minor version
                match = re.match(r'(\d+)\.(\d+)\.', version_str)
                if match:
                    major_version = int(match.group(1))
                    minor_version = int(match.group(2))
                    
                    # Set feature availability based on version
                    feature_map["json"] = (major_version > 5) or (major_version == 5 and minor_version >= 7)
                    feature_map["window_functions"] = major_version >= 8
                    feature_map["common_table_expressions"] = major_version >= 8
                    feature_map["fulltext_search"] = True  # Available in all supported MySQL versions
                    feature_map["stored_procedures"] = (major_version > 5) or (major_version == 5 and minor_version >= 0)
                    feature_map["triggers"] = (major_version > 5) or (major_version == 5 and minor_version >= 0)
                    feature_map["views"] = (major_version > 5) or (major_version == 5 and minor_version >= 0)
                
                return feature_map.get(feature_name.lower(), False)
        except Exception as e:
            logger.warning(f"Failed to check feature support: {str(e)}")
            return feature_map.get(feature_name.lower(), False)
    
    def escape_identifier(self, identifier: str) -> str:
        """Escape table or column identifiers with backticks for MySQL."""
        if not identifier:
            return '``'
        escaped = identifier.replace('`', '``')
        return f"`{escaped}`"
    
    def get_default_schema(self) -> str:
        """Return the default schema name for MySQL (database name)."""
        return self.config.database
    
    def add_batch_execute(self, query: str, data: List[Dict[str, Any]]) -> int:
        """Execute a batch query with multiple rows in MySQL."""
        if not data:
            return 0
            
        try:
            sanitized_query = self.validate_and_sanitize_sql(query, read_only=False)
            connection = self.create_connection()
            
            # Extract column names from the first data item
            column_names = list(data[0].keys())
            
            # Start transaction
            connection.begin()
            affected_rows = 0
            
            try:
                # Prepare the placeholder part
                placeholders = ", ".join(["%s"] * len(column_names))
                
                # Construct the final query
                if sanitized_query.upper().startswith('INSERT'):
                    # For INSERT queries, we need to add the columns and values
                    columns_str = ", ".join([self.escape_identifier(col) for col in column_names])
                    final_query = f"{sanitized_query} ({columns_str}) VALUES ({placeholders})"
                else:
                    final_query = sanitized_query
                
                # Execute the query for each data item
                with connection.cursor() as cursor:
                    for item in data:
                        # For each item, extract values in the same order as column_names
                        values = [item.get(col) for col in column_names]
                        cursor.execute(final_query, values)
                        affected_rows += cursor.rowcount
                
                # Commit the transaction
                connection.commit()
                logger.info(f"Batch execution completed, {affected_rows} rows affected")
                return affected_rows
                
            except Exception as e:
                connection.rollback()
                logger.error(f"Batch execution failed: {str(e)}")
                raise
        except Exception as e:
            logger.error(f"Batch execution preparation failed: {str(e)}")
            raise ValueError(f"Batch execution failed: {self.normalize_error(e)}")
