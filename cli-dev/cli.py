#!/usr/bin/env python3
import argparse
import json
import os
import sys
import requests
from tabulate import tabulate
from sql_agent_tool import SQLAgentTool, DatabaseConfig
from sql_agent_tool.models import LLMConfig
import logging

# Set up basic logging
logging.basicConfig(filename='cli.log', level=logging.INFO)
logger = logging.getLogger("sql-agent-cli")

def fetch_latest_version():
    """Download and install the latest sql-agent-tool from GitHub."""
    repo_url = "https://api.github.com/repos/Dadiya-Harsh/sql-tool/releases/latest"
    try:
        response = requests.get(repo_url)
        response.raise_for_status()
        release = response.json()
        version = release["tag_name"]
        logger.info(f"Latest version: {version}")
        
        for asset in release["assets"]:
            if asset["name"].endswith(".tar.gz"):
                tarball_url = asset["browser_download_url"]
                break
        else:
            logger.error("No tarball found in latest release")
            return False
        
        logger.info(f"Downloading {tarball_url}")
        os.system(f"pip install {tarball_url} --force-reinstall")
        return True
    except Exception as e:
        logger.error(f"Failed to fetch latest version: {str(e)}")
        return False

def load_config(config_file: str = ".sqlagentrc") -> dict:
    """Load DB and LLM config from a JSON file if it exists."""
    if os.path.exists(config_file):
        with open(config_file, "r") as f:
            return json.load(f)
    return {}

def get_api_key(provider: str, cli_key: str) -> str:
    """Determine the LLM API key from CLI arg, env var, or config."""
    if cli_key:
        return cli_key
    
    # Map provider to common env vars
    env_vars = {
        "openai": "OPENAI_API_KEY",
        "groq": "GROQ_API_KEY",
        "gemini": "GEMINI_API_KEY",
        "microsoft": "AZURE_OPENAI_API_KEY",
        "deepseek": "DEEPSEEK_API_KEY",
        "llama": "LLAMA_API_KEY"  # Adjust based on actual provider
    }
    env_key = os.getenv(env_vars.get(provider, ""), "")
    if env_key:
        return env_key
    
    logger.warning(f"No API key provided for {provider}. Check --api-key, env var, or .sqlagentrc")
    return ""

def run_query(args):
    """Run a natural language query using SQLAgentTool."""
    # Load config from file
    config = load_config()
    
    # DB config from args or config file
    db_config = DatabaseConfig(
        drivername=args.driver or config.get("drivername", "postgresql"),
        username=config.get("username", "postgres"),
        password=config.get("password", "password"),
        host=config.get("host", "localhost"),
        port=config.get("port", 5433),
        database=config.get("database", "P1"),
        query={}  # Add query params if needed
    )
    print(f"Connecting to database: {db_config.drivername}://{db_config.username}@{db_config.host}:{db_config.port}/{db_config.database}")
    print(f"Using driver: {db_config.drivername}")
    print(f"Using database: {db_config.database}")
    print(f"Using host: {db_config.host}")
    print(f"Using port: {db_config.port}")
    print(f"Using username: {db_config.username}")
    print(f"Using password: {db_config.password}")
    print(f"Using query: {db_config.query}")
    # LLM config
    provider = args.llm_provider or config.get("llm_provider", "openai")
    api_key = get_api_key(provider, args.api_key)
    if not api_key:
        logger.error("LLM API key is required. Use --api-key or set an environment variable.")
        sys.exit(1)
    
    llm_config = LLMConfig(
        provider=provider,
        api_key=api_key,
        model=args.llm_model or config.get("llm_model", "gpt-3.5-turbo"),
        temperature=config.get("temperature", 0.7),
        max_tokens=config.get("max_tokens", 1500)
    )
    
    # Initialize the tool
    try:
        tool = SQLAgentTool(db_config, llm_config)
    except Exception as e:
        logger.error(f"Failed to initialize SQLAgentTool: {str(e)}")
        sys.exit(1)
    
    if args.schema:
        # Show schema
        schema_info = tool.get_schema_info(include_sample_data=False)
        print(json.dumps(schema_info, indent=2))
    else:
        # Process query
        result = tool.process_natural_language_query(args.query)
        if args.sql_only:
            print(f"Generated SQL:\n{result.query}")
        else:
            if result.success:
                if result.data:
                    print(f"Generated SQL:\n{result.data}")
                    # print(tabulate(result.data, headers=result.columns, tablefmt="pretty"))
                    print(f"\nRows returned: {result.row_count}")
                else:
                    print("No data returned.")
            else:
                print(f"Error: {result.error}")
    
    tool.close()

def main():
    parser = argparse.ArgumentParser(description="SQL Agent CLI: Query databases with natural language.")
    parser.add_argument("--db", required=True, help="Database connection string (e.g., sqlite:///mydb.db)")
    parser.add_argument("--driver", help="Database driver (e.g., sqlite, postgresql)")
    parser.add_argument("query", nargs="?", help="Natural language query (e.g., 'How many users?')")
    parser.add_argument("--sql-only", action="store_true", help="Show generated SQL only")
    parser.add_argument("--schema", action="store_true", help="Display database schema")
    parser.add_argument("--update", action="store_true", help="Update to latest GitHub version")
    parser.add_argument("--api-key", help="LLM API key (overrides env var or config)")
    parser.add_argument("--llm-provider", help="LLM provider (e.g., openai, groq)")
    parser.add_argument("--llm-model", help="LLM model (e.g., gpt-3.5-turbo)")
    
    args = parser.parse_args()
    
    if args.update:
        if fetch_latest_version():
            print("Updated successfully. Rerun your command.")
        else:
            print("Update failed.")
        sys.exit(0)
    
    if not args.query and not args.schema:
        parser.error("Either a query or --schema is required unless using --update")
    
    run_query(args)

if __name__ == "__main__":
    main()