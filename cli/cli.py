import click
import yaml
import os
import yaml
import os
from .commands.init import init
from .commands.query import query
from .commands.shell import shell
from .commands.update import update
from sql_agent_tool.models import DatabaseConfig, LLMConfig

def load_config(config_path):
    """Load configuration from a YAML file with fallback defaults."""
    default_db_config = {
        "drivername": "postgresql",
        "host": "localhost",
        "port": 5432,
        "dbname": "postgres",
        "user": "postgres",
        "require_ssl": False
    }
    default_llm_config = {
        "provider": "groq",
        "model": "llama-3.3-70b-versatile",
        "temperature": 0.7,
        "max_tokens": 1500
    }

    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f) or {}
        db_config = config.get("database", {})
        llm_config = config.get("llm", {})
        return {
            "drivername": db_config.get("drivername", default_db_config["drivername"]),
            "host": db_config.get("host", default_db_config["host"]),
            "port": db_config.get("port", default_db_config["port"]),
            "dbname": db_config.get("dbname", default_db_config["dbname"]),
            "user": db_config.get("user", default_db_config["user"]),
            "require_ssl": db_config.get("require_ssl", default_db_config["require_ssl"]),
            "provider": llm_config.get("provider", default_llm_config["provider"]),
            "model": llm_config.get("model", default_llm_config["model"]),
            "temperature": llm_config.get("temperature", default_llm_config["temperature"]),
            "max_tokens": llm_config.get("max_tokens", default_llm_config["max_tokens"])
        }
    return {
        "host": default_db_config["host"],
        "port": default_db_config["port"],
        "dbname": default_db_config["dbname"],
        "user": default_db_config["user"],
        "require_ssl": default_db_config["require_ssl"],
        "provider": default_llm_config["provider"],
        "model": default_llm_config["model"],
        "temperature": default_llm_config["temperature"],
        "max_tokens": default_llm_config["max_tokens"]
    }

@click.group()
@click.option('--config', type=click.Path(exists=True), help='Path to configuration YAML file')
@click.option('--host', default=lambda: load_config('config.yaml').get('host'), help='Database host')
@click.option('--port', default=lambda: load_config('config.yaml').get('port'), help='Database port')
@click.option('--dbname', default=lambda: load_config('config.yaml').get('dbname'), help='Database name')
@click.option('--user', default=lambda: load_config('config.yaml').get('user'), help='Database user')
@click.option('--password', prompt=True, hide_input=True, help='Database password')
@click.option('--provider', default=lambda: load_config('config.yaml').get('provider'), help='LLM provider (e.g., openai, gemini, deepseek, groq)')
@click.option('--api-key', prompt=True, hide_input=True, help='LLM API key')
@click.option('--model', default=lambda: load_config('config.yaml').get('model'), help='LLM model')
@click.option('--max-rows', default=lambda: load_config('config.yaml').get('max_rows', 1000), help='Maximum rows to return')
@click.option('--read-only', is_flag=True, default=True, help='Enable read-only mode')
@click.pass_context
def cli(ctx, config, host, port, dbname, user, password, provider, api_key, model, max_rows, read_only):
    """SQL Agent CLI Tool - Manage databases with LLM-powered queries."""
    # If --config is provided, reload config to override defaults
    if config:
        config_data = load_config(config)
        host = config_data.get('host', host)
        port = config_data.get('port', port)
        dbname = config_data.get('dbname', dbname)
        user = config_data.get('user', user)
        provider = config_data.get('provider', provider)
        model = config_data.get('model', model)
        max_rows = config_data.get('max_rows', max_rows)

    ctx.ensure_object(dict)
    ctx.obj['db_config'] = DatabaseConfig(
        drivername='postgresql',
        username=user,
        password=password,
        host=host,
        port=port,
        database=dbname,
        require_ssl=False
    )
    ctx.obj['llm_config'] = LLMConfig(
        provider=provider,
        api_key=api_key if api_key else None,
        model=model,
        temperature=0.7,  # Keep as default unless in config
        max_tokens=1500   # Keep as default unless in config
    )
    ctx.obj['max_rows'] = max_rows
    ctx.obj['read_only'] = read_only

# Register commands
cli.add_command(init)
cli.add_command(query)
cli.add_command(shell)
cli.add_command(update)