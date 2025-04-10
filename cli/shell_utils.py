# cli/shell_utils.py
import re
from sql_agent_tool.exceptions import InvalidQueryError

def validate_query(query_text: str) -> None:
    """Basic query validation"""
    if len(query_text) < 3:
        raise InvalidQueryError("Query too short")
        
    if re.match(r'^\s*drop\s+table', query_text, re.IGNORECASE):
        raise InvalidQueryError("DROP TABLE queries not allowed in shell")