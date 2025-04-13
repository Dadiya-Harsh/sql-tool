import click
from sql_agent_tool.core import SQLAgentTool
from sql_agent_tool.models import DatabaseConfig, LLMConfig

@click.command()
@click.pass_context
def init(ctx):
    """Initialize the database schema and reflect it."""
    db_config = ctx.obj['db_config']
    llm_config = ctx.obj['llm_config']
    max_rows = ctx.obj['max_rows']
    read_only = ctx.obj['read_only']

    try:
        tool = SQLAgentTool(
            config=db_config,
            llmconfigs=llm_config,
            max_rows=max_rows,
            read_only=read_only
        )
        tool.get_schema_info(include_sample_data=False)
        click.echo("Database schema initialized and reflected successfully.")
    except Exception as e:
        click.echo(f"Error initializing database: {str(e)}", err=True)
    finally:
        if 'tool' in locals():
            tool.close()