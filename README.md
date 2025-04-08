# SQL Agent Tool

![Python](https://img.shields.io/badge/python-3.10+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Tests](https://img.shields.io/badge/tests-pytest-brightgreen.svg)

The **SQL Agent Tool** is a Python-based utility designed to interact with PostgreSQL databases, allowing users to execute SQL queries safely and efficiently. It integrates with the Groq API for potential natural language query generation (if implemented) and includes a robust test suite to ensure reliability. This project was developed as part of an internship at Wappnet, focusing on database interaction and testing against an existing PostgreSQL database (`P2`).

## Features

- **Database Connection**: Connects to PostgreSQL databases using SQLAlchemy.
- **Query Execution**: Safely executes read-only SQL queries with parameter binding.
- **Schema Reflection**: Retrieves and reflects database schema information.
- **Error Handling**: Custom exceptions for schema reflection, query validation, and execution errors.
- **Testing**: Comprehensive test suite using `pytest` with temporary table management to preserve production data.

## Project Structure

```
sql-tool/
├── sql_agent_tool/
│   ├── __init__.py
│   ├── core.py          # Main SQLAgentTool implementation
│   ├── exceptions.py    # Custom exceptions
│   └── models.py        # Database configuration models (e.g., DatabaseConfig)
├── tests/
│   └── test_postgresql.py  # Test suite for PostgreSQL integration
├── pyproject.toml       # Project configuration and dependencies
└── README.md            # This file
```

## Prerequisites

- **Python**: 3.10 or higher
- **PostgreSQL**: A running PostgreSQL server (e.g., on `localhost:5433`) with a database (e.g., `P2`)
- **Dependencies**: Listed in `pyproject.toml`

## Installation

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

   Alternatively, install development dependencies for testing:

   ```bash
   pip install .[dev]
   ```

4. **Configure Environment Variables** (optional):
   Create a `.env` file or set these in your shell:
   ```bash
   PG_USER=postgres
   PG_PASSWORD=password
   PG_HOST=localhost
   PG_PORT=5433
   PG_DATABASE=P2
   GROQ_API_KEY=your_groq_api_key_here
   ```
   Load them in your script with `python-dotenv` if needed.

## Usage

### Running the Tool

The `SQLAgentTool` class can be instantiated and used to interact with your PostgreSQL database. Example:

```python
from sql_agent_tool import SQLAgentTool, DatabaseConfig

config = DatabaseConfig(
    drivername="postgresql",
    username="postgres",
    password="password",
    host="localhost",
    port=5433,
    database="P2"
)

tool = SQLAgentTool(config, groq_api_key="your_groq_api_key_here")
result = tool.execute_query("SELECT * FROM users WHERE id = :id", {"id": 1})
print(result.data)

tool.close()
```

### Running Tests

The test suite ensures the tool works correctly with PostgreSQL. To run tests:

```bash
pytest tests/test_postgresql.py -v
```

The tests:

- Verify tool initialization.
- Test schema reflection with temporary tables.
- Validate query execution and error handling.

**Note**: Tests use temporary tables (`test_users_schema`, `test_query_table`) to avoid modifying production data in `P2`.

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

- **Groq API Integration**: Currently uses a placeholder key (`test_key`). Replace with a valid key for full functionality if natural language query generation is implemented.
- **Permissions**: Ensure the PostgreSQL user has privileges to create and drop temporary tables in the `P2` database.

## Contributing

1. Fork the repository.
2. Create a feature branch (`git checkout -b feature/your-feature`).
3. Commit your changes (`git commit -m "Add your feature"`).
4. Push to the branch (`git push origin feature/your-feature`).
5. Open a pull request.

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.

## Acknowledgments

- Developed during an internship at Wappnet.
- Built with guidance from Grok (xAI) for testing and debugging.

---

Feel free to customize this further—add specific sections like "Configuration Details" if your tool has more features, or include a "Roadmap" if you have future plans. Let me know if you’d like me to refine it or add anything specific!
