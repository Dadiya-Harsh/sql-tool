import re

def extract_sql_from_response(content: str) -> str:
    """Extract clean SQL from LLM response."""
    sql_markers = re.findall(r'```(?:sql)?(.*?)```', content, re.DOTALL)
    if sql_markers:
        return sql_markers[0].strip()
    sql_lines = []
    in_sql = False
    for line in content.split('\n'):
        if re.match(r'^\s*(SELECT|WITH|INSERT|UPDATE|DELETE|CREATE|ALTER)', line, re.IGNORECASE):
            in_sql = True
        if in_sql:
            sql_lines.append(line)
        if line.strip().endswith(';'):
            break
    return '\n'.join(sql_lines).strip() if sql_lines else content.strip()