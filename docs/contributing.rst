Contributing
============

We welcome contributions to SQL Agent Tool! This guide will help you get started.

Development Setup
-----------------

1. Fork the repository on GitHub
2. Clone your fork locally:

.. code-block:: bash

   git clone https://github.com/YOUR-USERNAME/sql-tool.git
   cd sql-tool

3. Create a virtual environment:

.. code-block:: bash

   python -m venv .venv
   source .venv/bin/activate

4. Install development dependencies:

.. code-block:: bash

   pip install .[dev]

Running Tests
-------------

The project uses pytest for testing:

.. code-block:: bash

   pytest tests/

Test files are located in the `tests/` directory:

* `test_core.py` - Core functionality tests
* `test_gemini_llm.py` - Gemini LLM integration tests  
* `test_postgresql.py` - PostgreSQL database tests
* `test_sql_agent.py` - SQL agent integration tests

Testing Guidelines
------------------

* Place test files in the `tests/` directory
* Use the `postgresql_config` and `sql_tool_postgresql` fixtures for database setup
* Avoid modifying production tables; use temporary tables instead
* Ensure tests clean up after themselves

Code Style
-----------

* Follow PEP 8 Python style guidelines
* Use meaningful variable and function names
* Add docstrings to all public functions and classes
* Keep functions focused and single-purpose

Pull Request Process
--------------------

1. Create a feature branch:

.. code-block:: bash

   git checkout -b feature/your-feature

2. Make your changes and add tests
3. Ensure all tests pass:

.. code-block:: bash

   pytest

4. Commit your changes:

.. code-block:: bash

   git commit -m "Add your feature"

5. Push to your fork:

.. code-block:: bash

   git push origin feature/your-feature

6. Open a pull request on GitHub

License
-------

This project is licensed under a dual license model:

* **Apache License 2.0** – For open source usage
* **Commercial License** – For proprietary/commercial use, contact harshdadiya@gmail.com

By contributing, you agree that your contributions will be licensed under the same terms.
