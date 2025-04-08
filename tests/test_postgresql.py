import pytest
import os
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError  # Import SQLAlchemyError
from sql_agent_tool import SQLAgentTool, DatabaseConfig
from sql_agent_tool.exceptions import (
    SchemaReflectionError, SQLValidationError, QueryExecutionError
)

# Replace with your actual Groq API key or set it in an environment variable
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "test_key")


# Fixture for PostgreSQL configuration
@pytest.fixture
def postgresql_config():
    """Provide a PostgreSQL database configuration using environment variables."""
    return DatabaseConfig(
        drivername="postgresql",
        username=os.getenv("PG_USER", "postgres"),
        password=os.getenv("PG_PASSWORD", "password"),
        host=os.getenv("PG_HOST", "localhost"),
        port=int(os.getenv("PG_PORT", 5433)),
        database=os.getenv("PG_DATABASE", "P2")
    )


# Fixture to initialize SQLAgentTool with PostgreSQL
@pytest.fixture
def sql_tool_postgresql(postgresql_config):
    """Initialize SQLAgentTool with a PostgreSQL database."""
    tool = SQLAgentTool(postgresql_config, groq_api_key=GROQ_API_KEY)
    yield tool
    tool.close()


# Test initialization
def test_sql_agent_initialization(sql_tool_postgresql):
    """Test that SQLAgentTool initializes correctly with PostgreSQL."""
    assert sql_tool_postgresql.engine is not None
    assert sql_tool_postgresql.config.drivername == "postgresql"
    assert sql_tool_postgresql.read_only is True
    assert sql_tool_postgresql.max_rows == 1000


# Test schema reflection with a temporary table
def test_schema_reflection(sql_tool_postgresql):
    """Test schema reflection with a temporary table in PostgreSQL."""
    test_table = "test_users_schema"  # Unique name to avoid conflicts
    with sql_tool_postgresql.engine.connect() as conn:
        # Clean up if the test table exists (safe to drop since it’s temporary)
        conn.execute(text(f"DROP TABLE IF EXISTS {test_table}"))
        conn.execute(text(f"CREATE TABLE {test_table} (id SERIAL PRIMARY KEY, name TEXT)"))
        conn.commit()

    sql_tool_postgresql._reflect_schema()
    schema = sql_tool_postgresql.get_schema_info()
    assert test_table in schema["tables"]
    assert len(schema["tables"][test_table]["columns"]) == 2
    assert schema["tables"][test_table]["columns"][0]["name"] == "id"

    # Clean up after the test
    with sql_tool_postgresql.engine.connect() as conn:
        conn.execute(text(f"DROP TABLE {test_table}"))
        conn.commit()


# Test schema reflection failure
def test_schema_reflection_failure(mocker, postgresql_config):
    """Test schema reflection failure handling in PostgreSQL."""
    tool = SQLAgentTool(postgresql_config, groq_api_key=GROQ_API_KEY)
    # Mock the reflect method to raise an SQLAlchemyError
    mocker.patch(
        "sqlalchemy.sql.schema.MetaData.reflect",
        side_effect=SQLAlchemyError("Mocked DB error")  # Use SQLAlchemyError instead of Exception
    )

    with pytest.raises(SchemaReflectionError) as exc_info:
        tool._reflect_schema()
    assert "Mocked DB error" in str(exc_info.value)
    tool.close()


# Test executing a valid query
def test_execute_query_success(sql_tool_postgresql):
    """Test executing a valid SQL query in PostgreSQL."""
    test_table = "test_query_table"  # Unique name for this test
    with sql_tool_postgresql.engine.connect() as conn:
        conn.execute(text(f"DROP TABLE IF EXISTS {test_table}"))
        conn.execute(text(f"CREATE TABLE {test_table} (id SERIAL PRIMARY KEY, value TEXT)"))
        conn.execute(text(f"INSERT INTO {test_table} (value) VALUES ('test_value') RETURNING id"))
        conn.commit()

    result = sql_tool_postgresql.execute_query(f"SELECT * FROM {test_table} WHERE id = :id", {"id": 1})
    assert result.success is True
    assert result.row_count == 1
    assert result.data[0]["value"] == "test_value"
    assert "id" in result.columns

    # Clean up
    with sql_tool_postgresql.engine.connect() as conn:
        conn.execute(text(f"DROP TABLE {test_table}"))
        conn.commit()


# Test executing an invalid query (read-only violation)
def test_execute_query_validation_failure(sql_tool_postgresql):
    """Test executing an invalid SQL query raises SQLValidationError."""
    with pytest.raises(SQLValidationError) as exc_info:
        sql_tool_postgresql.execute_query("INSERT INTO nonexistent (id) VALUES (1)")
    assert "INSERT commands not allowed" in str(exc_info.value)


# Test query execution failure (nonexistent table)
def test_execute_query_execution_failure(sql_tool_postgresql):
    """Test executing a query on a nonexistent table raises QueryExecutionError."""
    with pytest.raises(QueryExecutionError) as exc_info:
        sql_tool_postgresql.execute_query("SELECT * FROM nonexistent_table")
    assert "nonexistent_table" in str(exc_info.value)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])