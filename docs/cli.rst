Command Line Interface
======================

The SQL Agent Tool provides a command-line interface for interactive database querying.

Available Commands
------------------

.. code-block:: bash

   sql-agent-tool --help              # Show help
   sql-agent-tool --version           # Show version
   sql-agent-tool shell               # Start interactive shell
   sql-agent-tool init                # Initialize database

Interactive Shell
-----------------

The shell mode provides an interactive environment for natural language querying:

.. code-block:: bash

   $ sql-agent-tool shell
   Password: ****
   Api key: ****
   Connected to database. Type 'exit' to quit.
   
   SQL> what users are registered today?
   Generated SQL:
   SELECT * FROM users WHERE DATE(created_at) = CURRENT_DATE
   
   Results:
   {'id': 1, 'name': 'John Doe', 'email': 'john@example.com'}

Configuration
-------------

The CLI uses a `config.yaml` file for configuration. If not found, it will prompt for connection details.

Example config.yaml:

.. code-block:: yaml

   database:
     host: localhost
     port: 5432
     dbname: production_db
     user: app_user
     require_ssl: true

   llm:
     provider: gemini
     model: models/gemini-1.5-flash

Manual Page
-----------

.. program:: sql-agent-tool

.. option:: -h, --help

   Show help message and exit.

.. option:: --version

   Show program version and exit.

.. option:: --config CONFIG

   Path to configuration file (default: config.yaml).

.. option:: shell

   Start interactive SQL shell.

.. option:: init

   Initialize database connection.
