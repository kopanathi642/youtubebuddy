import json
from pathlib import Path
CATALOG=json.loads(Path(__file__).with_name('catalog.json').read_text())
TOOLS={t['id']:t for t in CATALOG['tools']}

def require_tool(tool_id):
    if tool_id not in TOOLS:raise ValueError('Unknown tool ID.')
    return TOOLS[tool_id]
