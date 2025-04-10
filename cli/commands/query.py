import click
from sql_agent_tool import SQLAgentTool
from sql_agent_tool.models import DatabaseConfig, LLMConfig, QueryResult

@click.command()
@click.argument('query', nargs=-1, type=str)
@click.pass_context
def query(ctx, query):
    """Execute a natural language query (e.g., 'find users named John')."""
    db_config = ctx.obj['db_config']
    llm_config = ctx.obj['llm_config']
    max_rows = ctx.obj['max_rows']
    read_only = ctx.obj['read_only']

    natural_query = ' '.join(query) if query else click.prompt('Enter natural language query')
    try:
        tool = SQLAgentTool(
            config=db_config,
            llmconfigs=llm_config,
            max_rows=max_rows,
            read_only=read_only
        )
        result = tool.process_natural_language_query(natural_query)
        if result.success:
            click.echo(f"Rows returned: {result.row_count}")
            for row in result.data:
                click.echo(row)
        else:
            click.echo(f"Error: {result.error}", err=True)
    except Exception as e:
        click.echo(f"Error processing query: {str(e)}", err=True)
    finally:
        if 'tool' in locals():
            tool.close()