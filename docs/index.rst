SQL Agent Tool Documentation
============================

A lightweight, LLM-integrated SQL utility for intelligent, secure PostgreSQL querying.

The SQL Agent Tool is a Python-based utility designed to interact with PostgreSQL databases, 
allowing users to execute SQL queries safely and efficiently. It integrates with multiple 
LLM providers (Groq, Google Gemini, OpenAI, DeepSeek) to convert natural language queries 
into SQL.

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   installation
   quickstart
   api
   cli
   examples
   contributing

Features
--------

* **Database Connection**: Connects to PostgreSQL databases using SQLAlchemy
* **Query Execution**: Safely executes read-only SQL queries with parameter binding
* **Schema Reflection**: Retrieves and reflects database schema information
* **Natural Language Processing**: Converts natural language queries to SQL using LLMs
* **Error Handling**: Custom exceptions for schema reflection, query validation, and execution errors
* **Testing**: Comprehensive test suite using pytest

Supported LLM Providers
-----------------------

* Groq
* Google Gemini
* OpenAI
* DeepSeek

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
