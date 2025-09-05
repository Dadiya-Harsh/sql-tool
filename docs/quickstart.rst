Quick Start Guide
=================

This guide will get you up and running with SQL Agent Tool in minutes.

Basic Usage
-----------

.. code-block:: python

   from sql_agent_tool.models import DatabaseConfig, LLMConfig
   from sql_agent_tool import SQLAgentTool

   # Configure database connection
   config = DatabaseConfig(
       drivername="postgresql",
       username="postgres",
       password="your-password",
       host="localhost",
       port=5432,
       database="your-database"
   )

   # Configure LLM
   llm_config = LLMConfig(
       provider="groq",
       api_key="your-api-key",
       model="llama-3.3-70b-versatile",
       max_tokens=500
   )

   # Create agent
   agent_tool = SQLAgentTool(config, llm_config)

   # Execute natural language query
   result = agent_tool.process_natural_language_query(
       "What are the top 5 users by registration date?"
   )

   if result.success:
       print(f"Found {result.row_count} results:")
       for row in result.data:
           print(row)

   agent_tool.close()

Using the CLI
-------------

Start the interactive shell:

.. code-block:: bash

   sql-agent-tool shell

Or with custom config:

.. code-block:: bash

   sql-agent-tool --config /path/to/config.yaml shell

Configuration File
------------------

Create `config.yaml`:

.. code-block:: yaml

   database:
     host: localhost
     port: 5432
     dbname: your_database
     user: postgres
     require_ssl: false

   llm:
     provider: groq
     model: llama-3.3-70b-versatile
