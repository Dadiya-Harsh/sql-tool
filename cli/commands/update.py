import click
from sql_agent_tool.core import SQLAgentTool
from sql_agent_tool.models import DatabaseConfig, LLMConfig

@click.command()
@click.pass_context
def update(ctx):
    """Update records in the database (disabled in read-only mode)."""
    if ctx.obj['read_only']:
        click.echo("Update command is disabled in read-only mode.", err=True)
    else:
        click.echo("Update command not yet implemented.")