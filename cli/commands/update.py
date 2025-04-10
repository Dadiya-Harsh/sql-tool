# cli/commands/update.py
import click
import requests
import os
import sys
from termcolor import colored

@click.command()
def update():
    """Update to latest version"""
    try:
        response = requests.get(
            "https://api.github.com/repos/Dadiya-Harsh/sql-tool/releases/latest"
        )
        response.raise_for_status()
        release = response.json()
        version = release["tag_name"]
        
        for asset in release["assets"]:
            if asset["name"].endswith(".tar.gz"):
                download_url = asset["browser_download_url"]
                break
        else:
            click.echo(colored("No valid package found", "red"))
            sys.exit(1)
            
        click.echo(colored(f"Updating to version {version}...", "green"))
        os.system(f"pip install {download_url} --force-reinstall")
        click.echo(colored("Update complete. Please restart the CLI.", "green"))
        
    except Exception as e:
        click.echo(colored(f"Update failed: {str(e)}", "red"))
        sys.exit(1)