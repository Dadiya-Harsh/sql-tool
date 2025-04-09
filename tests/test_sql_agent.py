# test_sql_agent.py
import pytest
import logging
import os
from unittest.mock import Mock, patch
from sql_agent_tool.llm.factory import LLMFactory
from sql_agent_tool.models import LLMConfig, DatabaseConfig, QueryResult
from sql_agent_tool.core import SQLAgentTool
from sqlalchemy import make_url
from dotenv import load_dotenv

# Test fixtures
@pytest.fixture
def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        filename='test_sql_tool.log',
        filemode='a'
    )
    return logging.getLogger(__name__)

@pytest.fixture
def db_config():
    load_dotenv()
    DATABASE_URL = os.getenv("DATABASE_URL")
    url = make_url(DATABASE_URL)
    return DatabaseConfig(
        drivername=url.drivername,
        username=url.username,
        password=url.password,
        host=url.host,
        port=url.port,
        database=url.database,
        require_ssl=False
    )

@pytest.fixture
def llm_config():
    load_dotenv()
    LLM_API_KEY = os.getenv("GEMINI_API_KEY")
    return LLMConfig(
        provider="gemini",
        api_key=LLM_API_KEY,
        model="models/gemini-1.5-flash",
        max_tokens=500
    )

@pytest.fixture
def sql_agent_tool(db_config, llm_config):
    agent = SQLAgentTool(db_config, llmconfigs=llm_config, max_rows=500)
    yield agent
    agent.close()

# Unit Tests
class TestSQLAgentToolUnit:
    @patch('sql_agent_tool.core.SQLAgentTool.process_natural_language_query')
    def test_process_query_success(self, mock_process, setup_logging):
        # Arrange
        mock_result = QueryResult(
            success=True,
            data=[{'course_name': 'Python', 'student_count': 100}],
            row_count=1,
            query="SELECT * FROM courses"
        )
        mock_process.return_value = mock_result
        
        config = Mock(spec=DatabaseConfig)
        llm_config = Mock(spec=LLMConfig)
        agent = SQLAgentTool(config, llmconfigs=llm_config, max_rows=500)
        
        # Act
        result = agent.process_natural_language_query("test query")
        
        # Assert
        assert result.success is True
        assert result.row_count == 1
        assert len(result.data) == 1
        mock_process.assert_called_once_with("test query")

    @patch('sql_agent_tool.core.SQLAgentTool.process_natural_language_query')
    def test_process_query_failure(self, mock_process, setup_logging):
        # Arrange
        mock_process.side_effect = Exception("Database error")
        config = Mock(spec=DatabaseConfig)
        llm_config = Mock(spec=LLMConfig)
        agent = SQLAgentTool(config, llmconfigs=llm_config, max_rows=500)
        
        # Act & Assert
        with pytest.raises(Exception, match="Database error"):
            agent.process_natural_language_query("test query")

# Integration Tests
class TestSQLAgentToolIntegration:
    def test_top_courses_query(self, sql_agent_tool, setup_logging):
        # Act
        result = sql_agent_tool.process_natural_language_query(
            "what are top courses purchased by maximum students?"
        )
        
        # Assert
        assert result.success is True, f"Query failed: {result.error_message}"
        assert result.row_count >= 0
        assert isinstance(result.data, list)
        if result.row_count > 0:
            assert isinstance(result.data[0], dict)
        
    def test_student_name_query(self, sql_agent_tool, setup_logging):
        # Act
        result = sql_agent_tool.process_natural_language_query(
            "Are there any student named harsh?"
        )
        
        # Assert
        assert result.success is True, f"Query failed: {result.error_message}"
        assert result.row_count >= 0
        assert isinstance(result.data, list)
        
    def test_invalid_query(self, sql_agent_tool, setup_logging):
        # Act
        result = sql_agent_tool.process_natural_language_query(
            "this is an invalid query that should fail"
        )
        
        # Assert
        assert result.success is False
        assert result.error_message is not None

if __name__ == "__main__":
    pytest.main(["-v"])