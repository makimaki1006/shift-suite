#!/usr/bin/env python3
"""
Add None checks for data_get calls in dash_app.py
"""

def add_critical_none_checks():
    """Add None checks for critical data_get calls"""
    
    dash_app_path = "C:\\ShiftAnalysis\\dash_app.py"
    
    print("Reading dash_app.py...")
    with open(dash_app_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Define critical data_get patterns that need None checks
    critical_patterns = [
        # Pattern: variable = data_get('key')
        # Add: if variable is None: variable = pd.DataFrame()
        {
            'pattern': r"(\s+)(\w+)\s*=\s*data_get\('([^']+)'\)",
            'replacement': lambda m: f"{m.group(1)}{m.group(2)} = data_get('{m.group(3)}')\n{m.group(1)}if {m.group(2)} is None:\n{m.group(1)}    {m.group(2)} = pd.DataFrame()"
        }
    ]
    
    import re
    
    # Find all standalone data_get assignments
    pattern = r"(\s+)(\w+)\s*=\s*data_get\('([^']+)'\)(?!\s*\n\s*if\s+\w+\s+is\s+None)"
    
    matches = list(re.finditer(pattern, content))
    print(f"Found {len(matches)} data_get assignments needing None checks")
    
    # Process matches in reverse order to preserve positions
    for match in reversed(matches):
        indent = match.group(1)
        var_name = match.group(2)
        key = match.group(3)
        
        original = match.group(0)
        replacement = f"{indent}{var_name} = data_get('{key}')\n{indent}if {var_name} is None:\n{indent}    {var_name} = pd.DataFrame()"
        
        content = content[:match.start()] + replacement + content[match.end():]
    
    # Write the updated content
    with open(dash_app_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"Added None checks for {len(matches)} data_get calls")
    return True

if __name__ == "__main__":
    add_critical_none_checks()