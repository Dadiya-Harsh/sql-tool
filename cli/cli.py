# cli/cli.py
import click
from .commands.query import query
from .commands.shell import shell
from .commands.update import update

@click.group()
def cli():
    """SQL Agent CLI: Natural language database queries"""
    pass

cli.add_command(query)
cli.add_command(shell)
cli.add_command(update)