# sql_agent_tool/config.py

import json
from pathlib import Path
from .exceptions import ConfigurationError

REQUIRED_FIELDS = {
    "database": ["drivername", "username", "host", "database"],
    "llm": ["provider", "api_key"]
}

def load_config(config_file=".sqlagentrc"):
    config_path = Path(config_file)
    
    if not config_path.exists():
        raise ConfigurationError("Configuration file not found")
    
    with config_path.open() as f:
        config = json.load(f)
    
    # Validate required sections
    for section, fields in REQUIRED_FIELDS.items():
        if section not in config:
            raise ConfigurationError(f"Missing section: {section}")
        
        for field in fields:
            if field not in config[section]:
                raise ConfigurationError(
                    f"Missing required field '{field}' in {section} section"
                )
    
    return config