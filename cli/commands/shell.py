import click
from sql_agent_tool import SQLAgentTool
from sql_agent_tool.models import DatabaseConfig, LLMConfig, QueryResult

@click.command()
@click.pass_context
def shell(ctx):
    """Start an interactive SQL shell."""
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
        click.echo(f"Connected to {db_config.database} on {db_config.host}:{db_config.port}. Type 'exit' to quit.")
        while True:
            natural_query = click.prompt("SQL> ", default="exit")
            if natural_query.lower() == "exit":
                break
            result = tool.process_natural_language_query(natural_query)
            if result.success:
                click.echo(f"Rows returned: {result.row_count}")
                for row in result.data:
                    click.echo(row)
            else:
                click.echo(f"Error: {result.error}", err=True)
    except Exception as e:
        click.echo(f"Error in shell: {str(e)}", err=True)
    finally:
        if 'tool' in locals():
            tool.close()