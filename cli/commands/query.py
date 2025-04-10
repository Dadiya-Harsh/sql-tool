# cli/commands/query.py
import click
import json
from sql_agent_tool import SQLAgentTool
from sql_agent_tool.config import load_config
from sql_agent_tool.exceptions import ConfigurationError
from tabulate import tabulate
from termcolor import colored

@click.command()
@click.option("--db", help="Database connection string")
@click.option("--driver", help="Database driver")
@click.option("--api-key", help="LLM API key")
@click.option("--llm-provider", help="LLM provider")
@click.option("--llm-model", help="LLM model")
@click.argument("query_text")
def query(db, driver, api_key, llm_provider, llm_model, query_text):
    """Execute a single natural language query"""
    config = load_config()
    
    # Database setup
    try:
        db_config = {
            "drivername": driver or config.get("drivername"),
            "username": config.get("username"),
            "password": config.get("password"),
            "host": config.get("host"),
            "port": config.get("port"),
            "database": config.get("database"),
        }
    except KeyError as e:
        raise ConfigurationError(f"Missing required config: {e}")

    # LLM setup
    llm_config = {
        "provider": llm_provider or config.get("llm_provider"),
        "api_key": api_key or config.get("llm_api_key"),
        "model": llm_model or config.get("llm_model"),
    }

    tool = SQLAgentTool(db_config, llm_config)
    
    try:
        result = tool.process_natural_language_query(query_text)
        
        if result.success:
            click.echo(colored("Generated SQL:", "cyan"))
            click.echo(result.query)
            
            if result.data:
                click.echo("\nResults:")
                click.echo(tabulate(result.data, headers=result.columns, tablefmt="pretty"))
                click.echo(colored(f"\nRows returned: {result.row_count}", "green"))
            else:
                click.echo(colored("No data returned.", "yellow"))
        else:
            click.echo(colored(f"Error: {result.error}", "red"))
            
    finally:
        tool.close()