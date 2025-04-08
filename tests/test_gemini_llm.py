import pytest
from unittest.mock import patch, MagicMock
from sql_agent_tool.llm.gemini import GeminiLLM

# Mock response for generate_content
mock_response = MagicMock()
mock_response.text = "SELECT * FROM test_table;"

from dotenv import load_dotenv
import os
load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Removed the fixture since it was creating the object before patches
# @pytest.fixture
# def gemini_llm():
#     return GeminiLLM(api_key=GEMINI_API_KEY, model="models/gemini-1.5-flash")

@patch("google.generativeai.configure")
@patch("google.generativeai.GenerativeModel")
def test_generate_sql_success(mock_model, mock_configure):
    # Arrange
    mock_instance = MagicMock()
    mock_instance.generate_content.return_value = mock_response
    mock_model.return_value = mock_instance
    
    # Create the object inside the test where patches are active
    gemini_llm = GeminiLLM(api_key=GEMINI_API_KEY, model="models/gemini-1.5-flash")

    # Act
    result = gemini_llm.generate_sql("Test prompt")

    # Assert
    mock_configure.assert_called_once_with(api_key=GEMINI_API_KEY)
    mock_model.assert_called_once_with("models/gemini-1.5-flash")
    mock_instance.generate_content.assert_called_once_with("Test prompt")
    assert result == "SELECT * FROM test_table;"

@patch("google.generativeai.configure")
def test_invalid_api_key(mock_configure):
    mock_configure.side_effect = ValueError("Invalid API key")
    with pytest.raises(ValueError):
        GeminiLLM(api_key="invalid_key")

@patch("google.generativeai.GenerativeModel")
def test_generate_sql_exception(mock_model):
    # Arrange
    mock_instance = MagicMock()
    mock_instance.generate_content.side_effect = Exception("API error")
    mock_model.return_value = mock_instance
    
    # Create the object inside the test where patches are active
    gemini_llm = GeminiLLM(api_key=GEMINI_API_KEY, model="models/gemini-1.5-flash")

    # Act & Assert
    with pytest.raises(Exception) as e:
        gemini_llm.generate_sql("Test prompt")
    assert str(e.value) == "API error"

def test_default_model():
    llm = GeminiLLM(api_key=GEMINI_API_KEY)
    # Check if the model is an instance of GenerativeModel and has correct model_name
    assert hasattr(llm.model, '_model_name')
    assert llm.model._model_name == "models/gemini-1.5-flash"