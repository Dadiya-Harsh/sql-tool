from .core import SQLAgentTool
from .models import DatabaseConfig, QueryResult

__version__ = "0.1.9"
__all__ = ["SQLAgentTool", "DatabaseConfig", "QueryResult", "LLMConfig"]
__author__ = "Harsh Dadiya"
__name__ = "sql_agent_tool"
__license__ = "MIT"

__copyright__ = "2025 Harsh Dadiya"
__status__ = "Development"  # Development status of the project
__maintainer__ = "Harsh Dadiya"
__credits__ = ["Harsh Dadiya"]
__description__ = """
SQL Agent Tool

The SQL Agent Tool is a powerful Python-based framework designed to bridge natural language processing and database querying. It leverages large language models (LLMs) from providers like Groq, OpenAI, Gemini, and DeepSeek to convert natural language queries into executable SQL statements, enabling users to interact with PostgreSQL databases intuitively. This project offers a dual interface:

- **Script-based Usage**: A Python script (`test1.py`) allows users to test and execute sample queries (e.g., sentiment analysis, user lookups) with customizable LLM configurations and performance logging.
- **CLI Interface**: An interactive command-line tool (`sql-agent`) provides commands to initialize schemas, query databases, and manage data, with support for user-defined configurations via `config.yaml`.

Key Features:
- Supports multiple LLM providers with configurable models and parameters.
- Masks sensitive API keys in prompts for enhanced security.
- Loads configurations from the current directory's `config.yaml` or custom paths.
- Includes error handling and performance timing for query execution.
- Extensible design for developers to integrate new LLMs or database types.

Use Cases:
- Rapid prototyping of database queries without SQL expertise.
- Automated data analysis with natural language input.
- Educational tool for learning SQL through LLM assistance.

For developers, the project is modular, with a core `SQLAgentTool` class and supporting models (`DatabaseConfig`, `LLMConfig`) in the `sql_agent_tool` package. Contributions are welcome to enhance functionality or documentation. See `README.md` for setup instructions and usage examples.
"""