# test_mysql_database.py

import pytest
import pymysql
import logging
from unittest.mock import MagicMock, patch
from sql_agent_tool.models import DatabaseConfig, QueryResult
from sql_agent_tool.database.database_mysql import MySQLDatabase

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Fixture for database configuration
@pytest.fixture
def db_config():
    return DatabaseConfig(
        drivername="mysql",
        username="root",
        password="",  # Update with your test password
        host="localhost",
        port=3306,
        database="test_database"  # Use a test database
    )

# Fixture for a mock database connection
@pytest.fixture
def mock_connection():
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    return mock_conn, mock_cursor

# Test class for MySQLDatabase
class TestMySQLDatabase:
    
    def test_create_engine(self, db_config):
        """Test connection creation."""
        with patch('pymysql.connect') as mock_connect:
            mock_connect.return_value = MagicMock(open=True)
            
            db = MySQLDatabase(db_config)
            connection = db.create_engine()
            
            # Verify pymysql.connect was called with correct parameters
            mock_connect.assert_called_once()
            call_args = mock_connect.call_args[1]
            assert call_args['host'] == db_config.host
            assert call_args['user'] == db_config.username
            assert call_args['password'] == db_config.password
            assert call_args['database'] == db_config.database
            assert call_args['port'] == db_config.port
            
            # Verify connection is stored in instance
            assert db.connection == mock_connect.return_value
    
    def test_reflect_schema(self, db_config):
        """Test schema reflection."""
        with patch.object(MySQLDatabase, 'create_connection') as mock_create_conn:
            # Mock cursor and connection
            mock_conn, mock_cursor = MagicMock(), MagicMock()
            mock_create_conn.return_value = mock_conn
            mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
            
            # Mock tables query result
            mock_cursor.fetchall.side_effect = [
                [{'table_name': 'users'}, {'table_name': 'orders'}],  # Tables result
                [  # Columns for 'users'
                    {'column_name': 'id', 'data_type': 'int', 'is_nullable': 'NO', 
                     'column_key': 'PRI', 'extra': 'auto_increment', 'column_default': None},
                    {'column_name': 'name', 'data_type': 'varchar', 'is_nullable': 'YES', 
                     'column_key': '', 'extra': '', 'column_default': None}
                ],
                [  # Columns for 'orders'
                    {'column_name': 'id', 'data_type': 'int', 'is_nullable': 'NO', 
                     'column_key': 'PRI', 'extra': 'auto_increment', 'column_default': None},
                    {'column_name': 'user_id', 'data_type': 'int', 'is_nullable': 'NO', 
                     'column_key': 'MUL', 'extra': '', 'column_default': None}
                ]
            ]
            
            db = MySQLDatabase(db_config)
            db.reflect_schema()
            
            # Verify schema was cached correctly
            assert 'users' in db.schema_cache
            assert 'orders' in db.schema_cache
            assert len(db.schema_cache['users']) == 2
            assert len(db.schema_cache['orders']) == 2
            
            # Verify column data
            assert db.schema_cache['users'][0]['name'] == 'id'
            assert db.schema_cache['users'][0]['primary_key'] is True
            assert db.schema_cache['users'][1]['name'] == 'name'
            assert db.schema_cache['users'][1]['type'] == 'varchar'
    
    def test_validate_and_sanitize_sql(self, db_config):
        """Test SQL validation."""
        db = MySQLDatabase(db_config)
        
        # Test valid SELECT
        valid_select = "SELECT * FROM users WHERE id = 1"
        assert db.validate_and_sanitize_sql(valid_select) == valid_select
        
        # Test valid INSERT when not read_only
        valid_insert = "INSERT INTO users (name) VALUES ('test')"
        assert db.validate_and_sanitize_sql(valid_insert, read_only=False) == valid_insert
        
        # Test invalid INSERT when read_only
        with pytest.raises(ValueError) as excinfo:
            db.validate_and_sanitize_sql(valid_insert, read_only=True)
        assert "Only SELECT queries are allowed" in str(excinfo.value)
        
        # Test unsupported statement
        with pytest.raises(ValueError) as excinfo:
            db.validate_and_sanitize_sql("DROP TABLE users")
        assert "Only SELECT, INSERT, UPDATE, DELETE queries are allowed" in str(excinfo.value)
    
    def test_bind_parameters(self, db_config):
        """Test parameter binding."""
        db = MySQLDatabase(db_config)
        
        # Test with named parameters
        sql = "SELECT * FROM users WHERE id = :user_id AND status = :status"
        params = {"user_id": 123, "status": "active"}
        
        bound_sql, bound_params = db.bind_parameters(sql, params)
        
        # Check sql has placeholders
        assert ":user_id" not in bound_sql
        assert ":status" not in bound_sql
        assert "%s" in bound_sql
        
        # Check parameters are in the right order
        assert len(bound_params) == 2
        assert 123 in bound_params
        assert "active" in bound_params
        
        # Test with missing parameters
        sql = "SELECT * FROM users WHERE id = :user_id"
        params = {}
        
        with pytest.raises(ValueError) as excinfo:
            db.bind_parameters(sql, params)
        assert "Missing parameter" in str(excinfo.value)
        
        # Test with no parameters
        sql = "SELECT * FROM users"
        bound_sql, bound_params = db.bind_parameters(sql, {})
        assert bound_sql == sql
        assert bound_params == []
    
    @patch('pymysql.connect')
    def test_execute_query_success(self, mock_connect, db_config):
        """Test successful query execution."""
        # Setup mock cursor with successful query results
        mock_cursor = MagicMock()
        mock_cursor.description = [('id',), ('name',)]
        mock_cursor.rowcount = 2
        mock_cursor.fetchall.return_value = [
            {'id': 1, 'name': 'User 1'},
            {'id': 2, 'name': 'User 2'}
        ]
        
        # Setup mock connection
        mock_conn = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_connect.return_value = mock_conn
        mock_connect.return_value.open = True
        
        db = MySQLDatabase(db_config)
        
        # Execute query with parameters
        query = "SELECT * FROM users WHERE status = %s"
        params = {"status": "active"}
        
        with patch.object(db, 'bind_parameters', return_value=(query, ["active"])):
            result = db.execute_query(query, params)
        
        # Verify result
        assert result.success is True
        assert result.error is None
        assert result.row_count == 2
        assert len(result.data) == 2
        assert result.data[0]['name'] == 'User 1'
        assert result.data[1]['name'] == 'User 2'
    
    @patch('pymysql.connect')
    def test_execute_query_error(self, mock_connect, db_config):
        """Test query execution with error."""
        # Setup mock connection to raise exception
        mock_cursor = MagicMock()
        mock_cursor.execute.side_effect = pymysql.err.ProgrammingError("Syntax error")
        
        mock_conn = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_connect.return_value = mock_conn
        mock_connect.return_value.open = True
        
        db = MySQLDatabase(db_config)
        
        # Execute query that will fail
        query = "SELECT * FROM non_existent_table"
        
        result = db.execute_query(query)
        
        # Verify error handling
        assert result.success is False
        assert result.error is not None
        assert "SQL error" in result.error
        assert result.data == []
        assert result.row_count == 0
    
    def test_parameter_handling_fixed(self, db_config):
        """
        Test the specific case that was failing in your output.
        This tests the fix for "not enough arguments for format string" error.
        """
        with patch.object(MySQLDatabase, 'create_connection') as mock_create_conn:
            # Mock cursor and connection
            mock_conn, mock_cursor = MagicMock(), MagicMock()
            mock_create_conn.return_value = mock_conn
            mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
            
            # Set up return values
            mock_cursor.description = [('total',)]
            mock_cursor.rowcount = 1
            mock_cursor.fetchall.return_value = [{'total': 3}]
            
            db = MySQLDatabase(db_config)
            
            # The query that was failing in your example
            query = "SELECT COUNT(*) as total FROM information_schema.tables WHERE table_schema = %s"
            params = {"param1": "studentmang"}
            
            # Test with modified bind_parameters that fixes the issue
            with patch.object(db, 'bind_parameters') as mock_bind:
                # Return the correct positional parameters
                mock_bind.return_value = (query, ["studentmang"])
                
                result = db.execute_query(query, params)
                
                # Check bind_parameters was called correctly
                mock_bind.assert_called_once_with(query, params)
                
                # Check correct SQL was executed
                mock_cursor.execute.assert_called_once_with(query, ["studentmang"])
                
                # Check result
                assert result.success is True
                assert result.data == [{'total': 3}]
    
    def test_get_schema_info(self, db_config):
        """Test schema info retrieval."""
        with patch.object(MySQLDatabase, '_reflect_schema'), \
             patch.object(MySQLDatabase, 'create_connection') as mock_create_conn:
            
            # Mock cursor and connection
            mock_conn, mock_cursor = MagicMock(), MagicMock()
            mock_create_conn.return_value = mock_conn
            mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
            
            # Set up sample data return value
            mock_cursor.fetchall.return_value = [
                {'id': 1, 'name': 'Sample 1'},
                {'id': 2, 'name': 'Sample 2'}
            ]
            
            db = MySQLDatabase(db_config)
            # Create a fake schema cache
            db.schema_cache = {
                'users': [
                    {'name': 'id', 'type': 'int', 'nullable': False, 'primary_key': True},
                    {'name': 'name', 'type': 'varchar', 'nullable': True, 'primary_key': False}
                ]
            }
            
            schema_info = db.get_schema_info(include_sample_data=True)
            
            # Verify schema info structure
            assert 'tables' in schema_info
            assert 'users' in schema_info['tables']
            assert 'columns' in schema_info['tables']['users']
            assert 'sample_data' in schema_info['tables']['users']
            
            # Verify sample data
            assert len(schema_info['tables']['users']['sample_data']) == 2
    
    def test_get_foreign_keys(self, db_config):
        """Test foreign key retrieval."""
        with patch.object(MySQLDatabase, 'create_connection') as mock_create_conn:
            # Mock cursor and connection
            mock_conn, mock_cursor = MagicMock(), MagicMock()
            mock_create_conn.return_value = mock_conn
            mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
            
            # Set up foreign keys return value
            mock_cursor.fetchall.return_value = [
                {
                    'constrained_table': 'orders', 
                    'constrained_column': 'user_id',
                    'referred_table': 'users',
                    'referred_column': 'id',
                    'constraint_name': 'fk_orders_users'
                }
            ]
            
            db = MySQLDatabase(db_config)
            foreign_keys = db.get_foreign_keys()
            
            # Verify foreign keys structure
            assert len(foreign_keys) == 1
            assert foreign_keys[0]['constrained_table'] == 'orders'
            assert foreign_keys[0]['referred_table'] == 'users'
    
    def test_escape_identifier(self, db_config):
        """Test SQL identifier escaping."""
        db = MySQLDatabase(db_config)
        
        # Test normal identifier
        assert db.escape_identifier("users") == "`users`"
        
        # Test identifier with backticks
        assert db.escape_identifier("user`s") == "`user``s`"
        
        # Test empty identifier
        assert db.escape_identifier("") == "``"
        
        # Test None
        assert db.escape_identifier(None) == "``"
    
    def test_generate_pagination_syntax(self, db_config):
        """Test pagination syntax generation."""
        db = MySQLDatabase(db_config)
        
        # Test LIMIT only
        assert db.generate_pagination_syntax(10) == "LIMIT 10"
        
        # Test LIMIT with OFFSET
        assert db.generate_pagination_syntax(10, 20) == "LIMIT 10 OFFSET 20"

# Integration tests (these would run against a real database)
@pytest.mark.integration
class TestMySQLDatabaseIntegration:
    
    @pytest.fixture
    def setup_test_db(self, db_config):
        """Set up a test database with sample tables."""
        # Create a temporary connection for setup
        conn = pymysql.connect(
            host=db_config.host,
            user=db_config.username,
            password=db_config.password,
            port=db_config.port
        )
        
        try:
            with conn.cursor() as cursor:
                # Create test database
                cursor.execute(f"CREATE DATABASE IF NOT EXISTS {db_config.database}")
                
                # Use test database
                cursor.execute(f"USE {db_config.database}")
                
                # Create test tables
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS users (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        name VARCHAR(100) NOT NULL,
                        email VARCHAR(100) UNIQUE,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS orders (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        user_id INT NOT NULL,
                        amount DECIMAL(10,2) NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users(id)
                    )
                """)
                
                # Insert test data
                cursor.execute("TRUNCATE TABLE orders")
                cursor.execute("DELETE FROM users")
                cursor.execute("ALTER TABLE users AUTO_INCREMENT = 1")
                
                cursor.execute("""
                    INSERT INTO users (name, email) VALUES
                    ('User 1', 'user1@example.com'),
                    ('User 2', 'user2@example.com'),
                    ('User 3', 'user3@example.com')
                """)
                
                cursor.execute("""
                    INSERT INTO orders (user_id, amount) VALUES
                    (1, 100.50),
                    (1, 200.75),
                    (2, 50.25)
                """)
                
            conn.commit()
        finally:
            conn.close()
        
        # Return the database
        db = MySQLDatabase(db_config)
        yield db
        db.close()
    
    def test_real_connection(self, setup_test_db):
        """Test real database connection."""
        db = setup_test_db
        conn = db.create_connection()
        assert conn is not None
        assert conn.open is True
    
    def test_real_schema_reflection(self, setup_test_db):
        """Test schema reflection with real database."""
        db = setup_test_db
        db.reflect_schema()
        
        assert 'users' in db.schema_cache
        assert 'orders' in db.schema_cache
        
        # Check users table columns
        user_columns = {col['name']: col for col in db.schema_cache['users']}
        assert 'id' in user_columns
        assert 'name' in user_columns
        assert 'email' in user_columns
        assert user_columns['id']['primary_key'] is True
        
        # Check orders table columns
        order_columns = {col['name']: col for col in db.schema_cache['orders']}
        assert 'id' in order_columns
        assert 'user_id' in order_columns
        assert 'amount' in order_columns
    
    def test_real_query_execution(self, setup_test_db):
        """Test query execution with real database."""
        db = setup_test_db
        
        # Test SELECT query
        result = db.execute_query("SELECT * FROM users ORDER BY id")
        assert result.success is True
        assert len(result.data) == 3
        assert result.data[0]['name'] == 'User 1'
        assert result.data[1]['name'] == 'User 2'
        assert result.data[2]['name'] == 'User 3'
        
        # Test parameterized query
        result = db.execute_query(
        "SELECT * FROM users WHERE name = %s",
        ["User 2"]  # Use a list instead of a dictionary
    )
        assert result.success is True
        assert len(result.data) == 1
        assert result.data[0]['name'] == 'User 2'
        
        # Test JOIN query
        result = db.execute_query("""
            SELECT u.name, COUNT(o.id) as order_count
            FROM users u
            LEFT JOIN orders o ON u.id = o.user_id
            GROUP BY u.id
            ORDER BY u.id
        """)
        assert result.success is True
        assert len(result.data) == 3
        assert result.data[0]['order_count'] == 2  # User 1 has 2 orders
        assert result.data[1]['order_count'] == 1  # User 2 has 1 order
        assert result.data[2]['order_count'] == 0  # User 3 has no orders
    