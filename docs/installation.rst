Installation
============

Requirements
------------

* Python: 3.10 or higher
* PostgreSQL: A running PostgreSQL server (local or cloud)

Install from PyPI
-----------------

.. code-block:: bash

   pip install sql-agent-tool

Install from Source
-------------------

1. Clone the repository:

.. code-block:: bash

   git clone https://github.com/Dadiya-Harsh/sql-tool.git
   cd sql-tool

2. Set up a virtual environment:

.. code-block:: bash

   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate

3. Install dependencies:

.. code-block:: bash

   pip install .

For development (including tests):

.. code-block:: bash

   pip install .[dev]

Configuration
-------------

Create a `.env` file in your project root:

.. code-block:: bash

   GROQ_API_KEY=<your-groq-api-key>
   GEMINI_API_KEY=<your-gemini-api-key>
   OPENAI_API_KEY=<your-openai-api-key>
   DEEPSEEK_API_KEY=<your-deepseek-api-key>
   DATABASE_URL=postgresql://<username>:<password>@<host>:<port>/<database>

Example:

.. code-block:: bash

   GROQ_API_KEY=your-groq-key-here
   DATABASE_URL=postgresql://postgres:yourpassword@localhost:5432/yourdatabase
