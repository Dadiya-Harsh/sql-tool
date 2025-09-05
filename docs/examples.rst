Examples
========

Basic Query Example
-------------------

.. code-block:: python

   import time
   from sql_agent_tool.models import DatabaseConfig, LLMConfig
   from sql_agent_tool import SQLAgentTool

   # Database configuration
   config = DatabaseConfig(
       drivername="postgresql",
       username="postgres",
       password="root",
       host="localhost",
       port=5432,
       database="test_database"
   )

   # LLM configuration  
   llm_config = LLMConfig(
       provider="gemini",
       api_key="your-api-key",
       model="models/gemini-1.5-flash",
       max_tokens=500
   )

   agent_tool = SQLAgentTool(config, llm_config)

   try:
       # Query 1: Aggregate data
       result = agent_tool.process_natural_language_query(
           "what is the overall sentiment score of Vivek"
       )
       
       if result.success:
           print(f"Found {result.row_count} results:")
           for row in result.data:
               print(row)

       # Query 2: Search query
       result2 = agent_tool.process_natural_language_query(
           "Are there any employee name Vivek?"
       )
       
       if result2.success:
           print(f"Found {result2.row_count} results:")
           for row in result2.data:
               print(row)
               
   except Exception as e:
       print(f"Error: {e}")
   finally:
       agent_tool.close()

Different LLM Providers
-----------------------

OpenAI Example:

.. code-block:: python

   llm_config = LLMConfig(
       provider="openai", 
       api_key=os.getenv("OPENAI_API_KEY"),
       model="gpt-3.5-turbo",
       max_tokens=500
   )

DeepSeek Example:

.. code-block:: python

   llm_config = LLMConfig(
       provider="deepseek",
       api_key=os.getenv("DEEPSEEK_API_KEY"), 
       model="deepseek-chat",
       max_tokens=1024
   )

CLI Configuration Examples
--------------------------

Basic config.yaml:

.. code-block:: yaml

   database:
     host: localhost
     port: 5433
     dbname: P1
     user: postgres
     require_ssl: false

   llm:
     provider: groq
     model: llama-3.3-70b-versatile

Production config.yaml:

.. code-block:: yaml

   database:
     host: prod-db.example.com
     port: 5432
     dbname: production
     user: readonly_user
     require_ssl: true

   llm:
     provider: gemini
     model: models/gemini-1.5-pro
