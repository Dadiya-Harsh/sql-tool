# cli/commands/shell.py
import click
import sys
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
def shell(db, driver, api_key, llm_provider, llm_model):
    """Interactive query shell"""
    config = load_config()
    
    # Database setup
    try:
        db_config = {
            "drivername": driver or config["drivername"],
            "username": config["username"],
            "password": config["password"],
            "host": config["host"],
            "port": config["port"],
            "database": config["database"],
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
    
    click.echo(colored(f"""
    SQL Agent Interactive Shell
    ---------------------------
    Connected to: {db_config['drivername']}://{db_config['host']}:{db_config['port']}/{db_config['database']}
    LLM Provider: {llm_config['provider']} ({llm_config['model']})
    Type 'exit' or 'quit' to close
    """, "green"))
    
    try:
        while True:
            query_text = input(colored("sql-agent> ", "blue")).strip()
            
            if query_text.lower() in ("exit", "quit"):
                break
                
            if not query_text:
                continue
                
            try:
                result = tool.process_natural_language_query(query_text)
                
                if result.success:
                    click.echo(colored("\nGenerated SQL:", "cyan"))
                    click.echo(result.query)
                    
                    if result.data:
                        click.echo("\nResults:")
                        click.echo(tabulate(result.data, headers=result.columns, tablefmt="pretty"))
                        click.echo(colored(f"\nRows returned: {result.row_count}", "green"))
                    else:
                        click.echo(colored("No data returned.", "yellow"))
                else:
                    click.echo(colored(f"Error: {result.error}", "red"))
                    
            except Exception as e:
                click.echo(colored(f"Unexpected error: {str(e)}", "red"))
                
    except KeyboardInterrupt:
        click.echo(colored("\nExiting...", "yellow"))
    finally:
        tool.close()