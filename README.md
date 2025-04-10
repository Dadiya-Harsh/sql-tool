# SQL Agent Tool

[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://pypi.org/project/sql-agent-tool/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](https://github.com/Dadiya-Harsh/sql-tool/blob/main/LICENSE)
[![Tests](https://img.shields.io/badge/tests-pytest-brightgreen.svg)](https://github.com/Dadiya-Harsh/sql-tool/actions)
[![Anaconda-Server Badge](https://anaconda.org/dadiya-harsh/sql-agent-tool/badges/version.svg)](https://anaconda.org/dadiya-harsh/sql-agent-tool)

The **SQL Agent Tool** is a Python-based utility designed to interact with PostgreSQL databases, allowing users to execute SQL queries safely and efficiently. It integrates with multiple LLM providers (Groq, Google Gemini, OpenAI, DeepSeek) to convert natural language queries into SQL, and includes a robust test suite to ensure reliability.

## Purpose or Objective of Project:

SQL Agent Tool is designed to bridge the gap between AI agents and live SQL databases. Its primary goal is to eliminate the repetitive and error-prone process of writing boilerplate code for database interactions in AI-driven projects. Specifically, it addresses the following challenges:

1. **Schema Discovery**: Automatically extracts and translates database schemas into a format that AI agents can understand, reducing the need for manual schema definitions.
2. **Query Execution**: Simplifies the execution of SQL queries, allowing AI agents to retrieve and manipulate data without requiring deep knowledge of SQL syntax.
3. **Boilerplate Reduction**: Minimizes the amount of custom code developers need to write for database connections, query building, and result parsing.
4. **AI-Friendly Interface**: Provides a standardized interface for AI agents to interact with databases, making it easier to integrate AI workflows with live data.

Whether you're building an AI-powered chatbot, a data analysis tool, or any application that requires real-time database access, SQL Agent Tool streamlines the process and accelerates development.

## Features

- **Database Connection**: Connects to PostgreSQL databases using SQLAlchemy.
- **Query Execution**: Safely executes read-only SQL queries with parameter binding.
- **Schema Reflection**: Retrieves and reflects database schema information.
- **Natural Language Processing**: Converts natural language queries to SQL using LLMs.
- **Error Handling**: Custom exceptions for schema reflection, query validation, and execution errors.
- **Testing**: Comprehensive test suite using `pytest` with temporary table management to preserve production data.

## Project Structure

```
sql-tool/
├── sql_agent_tool/
│   ├── __init__.py
│   ├── core.py          # Main SQLAgentTool implementation
│   ├── exceptions.py    # Custom exceptions
│   ├── models.py        # Database configuration models (e.g., DatabaseConfig)
│   └── llm/             # LLM integrations
│       ├── base.py
│       ├── groq.py
│       ├── gemini.py
│       ├── openai.py
│       ├── deepseek.py
│       └── factory.py
├── tests/
│   └── test_postgresql.py  # Test suite for PostgreSQL integration
├── pyproject.toml       # Project configuration and dependencies
├── test1.py             # Example script for usage
└── README.md            # This file
```

## Prerequisites

- **Python**: 3.10 or higher
- **PostgreSQL**: A running PostgreSQL server (e.g., local or AWS RDS).
- **Dependencies**: Install required packages:

  ```bash
  pip install -r requirements.txt
  ```

  Example `requirements.txt`:

  ```
  sqlalchemy>=2.0
  psycopg2-binary>=2.9
  pydantic>=2.0
  python-dotenv>=1.0
  groq>=0.4
  google-generativeai>=0.5
  openai>=1.0
  ```

- **API Keys**: Obtain API keys for your chosen LLM providers:
  - Groq: [Get your API key](https://console.groq.com/keys)
  - Google Gemini: [Get your API key](https://ai.google.dev/)
  - OpenAI: [Get your API key](https://platform.openai.com/account/api-keys)
  - DeepSeek: [Get your API key](https://platform.deepseek.com/api_keys)

## Installation

You can install the SQL Agent Tool either via PyPI or by cloning the repository.

### Option 1: Install via PyPI

```bash
pip install sql-agent-tool
```

### Option 2: Clone the Repository

1. **Clone the Repository**:

   ```bash
   git clone https://github.com/Dadiya-Harsh/sql-tool.git
   cd sql-tool
   ```

2. **Set Up a Virtual Environment**:

   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install Dependencies**:

   ```bash
   pip install .
   ```

   For development (including tests):

   ```bash
   pip install .[dev]
   ```

4. **Configure Environment Variables**:
   Create a `.env` file in the project root:
   ```plaintext
   GROQ_API_KEY=<your-groq-api-key>
   GEMINI_API_KEY=<your-gemini-api-key>
   OPENAI_API_KEY=<your-openai-api-key>
   DEEPSEEK_API_KEY=<your-deepseek-api-key>
   DATABASE_URL=postgresql://<username>:<password>@<host>:<port>/<database>
   ```
   Example:
   ```plaintext
   GROQ_API_KEY=<your-groq-api-key>
   DATABASE_URL=postgresql://postgres:yourpassword@localhost:5432/yourdatabase
   ```

### Option 3: Conda

```bash
conda install dadiya-harsh::sql-agent-tool
```

## Usage

The SQL Agent Tool converts natural language queries into SQL and executes them against your PostgreSQL database, supporting multiple LLM providers for flexibility.

### Running the Tool

Use the provided `test1.py` script to run example queries. The script connects to your database and processes two sample queries using your chosen LLM provider.

1. **Set Up Your Environment**:
   Ensure your `.env` file contains the necessary API key and database URL.

2. **Run with Default LLM (Groq)**:

   ```bash
    #this are contents of test1.py for testing of tool
    import time
    from sql_agent_tool.models import DatabaseConfig, LLMConfig
    from sql_agent_tool import SQLAgentTool

    config = DatabaseConfig(
          drivername="postgresql",
          username="postgres",
          password="root",
          host="localhost",
          port=5432,
          database="test_sentiment_analysis"
       )
    llm_config = LLMConfig(provider="gemini", api_key="your-api-key", model="models/gemini-1.5-flash", max_tokens=500)

    agent_tool = SQLAgentTool(config, llm_config)
    start_time = time.time()
    try:
        print("\nQuery 1:")
        q1_start = time.time()
        result = agent_tool.process_natural_language_query("what is the overall sentiment score of Vivek")
        print(f"Query 1 total time: {time.time() - q1_start:.2f} seconds")
        if result.success:
            print(f"Query executed successfully, found {result.row_count} results:")
            for row in result.data:
                print(row)

        print("\nQuery 2:")
        q2_start = time.time()
        result2 = agent_tool.process_natural_language_query("Are there any employee name Vivek?")
        print(f"Query 2 total time: {time.time() - q2_start:.2f} seconds")
        if result2.success:
            print(f"Query executed successfully, found {result2.row_count} results:")
            for row in result2.data:
                print(row)
    except Exception as e:
      print(f"Error processing queries: {e}")
    finally:
        agent_tool.close()
        print(f"Total time: {time.time() - start_time:.2f} seconds")
   ```

   - Executes:
     - "What are top courses purchased by maximum students?"
     - "Are there any student named harsh?"
   - Logs results to `sql_tool.log`.

   - ## Output:

   ```
     (harsh) D:\Multi_job_analysis>
     Parameters: {'name_param': '%Vivek%'}
     Query 2 total time: 3.14 seconds
     Query executed successfully, found 1 results:
     {'id': 1, 'name': 'Vivek', 'email': 'vivek@gmail.com', 'phone': '9304034054', 'status': 'active', 'role': 'Manager'}
     Total time: 6.71 seconds

     Parameters: {'name_param': '%Vivek%'}
     Query 2 total time: 3.14 seconds
     Query executed successfully, found 1 results:
     {'id': 1, 'name': 'Vivek', 'email': 'vivek@gmail.com', 'phone': '9304034054', 'status': 'active', 'role': 'Manager'}
     Total time: 6.71 seconds
     Parameters: {'name_param': '%Vivek%'}
     Query 2 total time: 3.14 seconds
     Query executed successfully, found 1 results:
     Parameters: {'name_param': '%Vivek%'}
     Query 2 total time: 3.14 seconds
     Parameters: {'name_param': '%Vivek%'}
     Parameters: {'name_param': '%Vivek%'}
     Query 2 total time: 3.14 seconds
     Query executed successfully, found 1 results:
     {'id': 1, 'name': 'Vivek', 'email': 'vivek@gmail.com', 'phone': '9304034054', 'status': 'active', 'role': 'Manager'}
     Total time: 6.71 seconds

   ```

3. **Switch LLM Provider**:
   Edit `script` to use a different LLM. Example for OpenAI:
   ```python
   LLM_API_KEY = os.getenv("OPENAI_API_KEY")
   llm_config = LLMConfig(provider="openai", api_key=LLM_API_KEY, model="gpt-3.5-turbo", max_tokens=150)
   ```
   Then run:
   ```bash
   python test1.py
   ```
   Example for DeepSeek:
   ```python
   LLM_API_KEY = os.getenv("DEEPSEEK_API_KEY")
   llm_config = LLMConfig(provider="deepseek", api_key=LLM_API_KEY, model="deepseek-chat", max_tokens=1024)
   ```
   Then run:
   ```bash
   python test1.py
   ```

### Example Output

```
LLM config: provider='groq' api_key='<your-groq-api-key>' model='llama-3.3-70b-versatile' temperature=0.7 max_tokens=500

Query 1:
Generated SQL:
SELECT c.id, c.title, COUNT(p.id) as purchase_count
FROM courses c
JOIN payments p ON c.id = p.course_id
GROUP BY c.id, c.title
ORDER BY purchase_count DESC
LIMIT 500;
Parameters: {}
Query 1 total time: 2.56 seconds
Query executed successfully, found 14 results:
{'id': ..., 'title': 'Social Media Marketing (SMM)', 'purchase_count': 6}
...

Query 2:
Generated SQL:
SELECT * FROM users WHERE full_name ILIKE :search_pattern LIMIT 500;
Parameters: {'search_pattern': '%harsh%'}
Query 2 total time: 4.61 seconds
Query executed successfully, found 2 results:
{'id': ..., 'full_name': 'Harsh Dadiya', ...}
...
Total time: 75.06 seconds
```

### Customization

- **LLM Provider**: Modify `llm_config` in `test1.py`:
  - Groq: `provider="groq"`, `model="llama-3.3-70b-versatile"`, `max_tokens=500`
  - Gemini: `provider="gemini"`, `model="models/gemini-1.5-flash"`, `max_tokens=1024`
  - OpenAI: `provider="openai"`, `model="gpt-3.5-turbo"`, `max_tokens=150`
  - DeepSeek: `provider="deepseek"`, `model="deepseek-chat"`, `max_tokens=1024`
- **Database**: Update `DATABASE_URL` in `.env`.
- **Queries**: Change the `process_natural_language_query` calls in `test1.py` to test other questions.

### Notes

- **Startup Time**: Initial schema reflection takes ~60 seconds due to pre-caching, but queries run in ~2-5 seconds thereafter.
- **Logging**: Check `sql_tool.log` for detailed execution logs (e.g., LLM response times, SQL generation).

## Development

### Dependencies

Defined in `pyproject.toml`:

```toml
[project]
name = "sql-agent-tool"
version = "0.1.0"
dependencies = [
    "sqlalchemy>=2.0",
    "psycopg2-binary>=2.9",
    "pydantic>=2.0",
    "python-dotenv>=1.0",
    "groq>=0.4",
    "google-generativeai>=0.5",
    "openai>=1.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "pytest-mock>=3.0",
]
```

### Adding New Tests

- Place test files in the `tests/` directory.
- Use the `postgresql_config` and `sql_tool_postgresql` fixtures for database setup.
- Avoid modifying production tables like `users`; use temporary tables instead.

## Known Issues

- **Groq API Integration**: Requires a valid key in `.env` for natural language query generation.
- **Permissions**: Ensure the PostgreSQL user has privileges to create and drop temporary tables in the target database.

## Contributing

1. Fork the repository.
2. Create a feature branch (`git checkout -b feature/your-feature`).
3. Commit your changes (`git commit -m "Add your feature"`).
4. Push to the branch (`git push origin feature/your-feature`).
5. Open a pull request.

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.

## Acknowledgments

- Developed during an internship at Wappnet Systems.
- Built with guidance from Grok (xAI) for testing and debugging.
