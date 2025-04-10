import click
from .commands.init import init
from .commands.query import query
from .commands.shell import shell
from .commands.update import update
from sql_agent_tool.models import DatabaseConfig, LLMConfig

@click.group()
@click.option('--host', default='localhost', help='Database host')
@click.option('--port', default=5433, help='Database port')
@click.option('--dbname', default='P1', help='Database name')
@click.option('--user', default='postgres', help='Database user')
@click.option('--password', prompt=True, hide_input=True, help='Database password')
@click.option('--provider', default='groq', help='LLM provider (e.g., openai, gemini, deepseek, groq)')
@click.option('--api-key', prompt=True, hide_input=True, help='LLM API key')
@click.option('--model', default='llama-3.3-70b-versatile', help='LLM model')
@click.option('--max-rows', default=1000, help='Maximum rows to return')
@click.option('--read-only', is_flag=True, default=True, help='Enable read-only mode')
@click.pass_context
def cli(ctx, host, port, dbname, user, password, provider, api_key, model, max_rows, read_only):
    """SQL Agent CLI Tool - Manage databases with LLM-powered queries."""
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
        api_key=api_key,
        model=model,
        temperature=0.7,
        max_tokens=1500
    )
    ctx.obj['max_rows'] = max_rows
    ctx.obj['read_only'] = read_only

# Register commands
cli.add_command(init)
cli.add_command(query)
cli.add_command(shell)
cli.add_command(update)