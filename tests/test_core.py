import pytest
from sql_agent_tool import SQLAgentTool, DatabaseConfig

def test_sql_agent_initialization():
    config = DatabaseConfig(
        drivername="postgresql",
        username="postgres",
        password="password",
        host="localhost",
        port=5433,
        database="P2"
    )
    tool = SQLAgentTool(config, groq_api_key="test_key")
    assert tool.engine is not None
    tool.close()