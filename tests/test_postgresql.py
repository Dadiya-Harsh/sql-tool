import pytest
import os
import sys
from unittest.mock import MagicMock, patch
from sqlalchemy import create_engine, MetaData
from sql_agent_tool.models import DatabaseConfig, QueryResult
from sql_agent_tool.database.database_postgresql import PostgreSQLDatabase

# Add project root to sys.path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Fixture for DatabaseConfig
@pytest.fixture
def db_config():
    return DatabaseConfig(
        drivername="postgresql",
        username="postgres",
        password="password",
        host="localhost",
        port=5432,
        database="P1"
    )

# Fixture for PostgreSQLDatabase instance
@pytest.fixture
def pg_db(db_config):
    return PostgreSQLDatabase(db_config)

# Mocked engine and connection
@pytest.fixture
def mock_engine():
    engine = MagicMock()
    connection = MagicMock()
    engine.connect.return_value = connection
    connection.execute.return_value = MagicMock(mappings=lambda: [{"id": 1, "name": "Vivek"}])
    connection.keys.return_value = ["id", "name"]
    connection.rowcount = 1
    return engine

# Test create_engine
def test_create_engine(pg_db, mock_engine):
    with patch("sqlalchemy.create_engine", return_value=mock_engine):
        engine = pg_db.create_engine()
        assert engine == mock_engine
        assert pg_db.engine == mock_engine

# Test reflect_schema
def test_reflect_schema(pg_db, mock_engine):
    with patch("sqlalchemy.create_engine", return_value=mock_engine):
        with patch.object(MetaData, "reflect"):
            pg_db.create_engine()
            pg_db.reflect_schema()
            assert pg_db.metadata is not None

# Test get_schema_info
def test_get_schema_info(pg_db, mock_engine):
    with patch("sqlalchemy.create_engine", return_value=mock_engine):
        pg_db.create_engine()
        pg_db.metadata = MetaData()
        pg_db.metadata.tables = {"employees": MagicMock(columns=[MagicMock(name="id", type="INTEGER"), MagicMock(name="name", type="VARCHAR")])}
        with patch.object(mock_engine.connect(), "execute") as mock_execute:
            mock_execute.return_value = MagicMock(mappings=lambda: [{"id": 1, "name": "Vivek"}])
            schema_info = pg_db.get_schema_info(include_sample_data=True)
            assert "tables" in schema_info
            assert "employees" in schema_info["tables"]
            assert schema_info["tables"]["employees"]["columns"][0]["name"] == "id"
            assert schema_info["tables"]["employees"]["sample_data"][0]["name"] == "Vivek"

# Test execute_query
def test_execute_query(pg_db, mock_engine):
    with patch("sqlalchemy.create_engine", return_value=mock_engine):
        pg_db.create_engine()
        result = pg_db.execute_query("SELECT * FROM employees")
        assert isinstance(result, QueryResult)
        assert result.success
        assert result.data[0]["id"] == 1
        assert result.columns == ["id", "name"]

# Test validate_and_sanitize_sql (valid query)
def test_validate_and_sanitize_sql_valid(pg_db):
    query = "SELECT * FROM employees"
    sanitized = pg_db.validate_and_sanitize_sql(query)
    assert sanitized == query

# Test validate_and_sanitize_sql (invalid query)
def test_validate_and_sanitize_sql_invalid(pg_db):
    query = "DROP TABLE employees"
    with pytest.raises(ValueError):
        pg_db.validate_and_sanitize_sql(query)

# Optional: Test with real database (uncomment and configure when ready)
# @pytest.mark.integration
# def test_real_database_connection(pg_db):
#     pg_db.create_engine()
#     schema_info = pg_db.get_schema_info()
#     assert "tables" in schema_info
#     pg_db.close()

if __name__ == "__main__":
    pytest.main([__file__])