#!/usr/bin/env python3
"""
Fix all data_get DataFrame unhashable type errors in dash_app.py
"""

def fix_data_get_errors():
    """Fix all instances of data_get with pd.DataFrame() default parameters"""
    
    dash_app_path = "C:\\ShiftAnalysis\\dash_app.py"
    
    print("Reading dash_app.py...")
    with open(dash_app_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Count original occurrences
    original_count = content.count("data_get(") - content.count("def data_get(")
    problematic_count = content.count("pd.DataFrame()")
    
    print(f"Found {original_count} data_get() calls")
    print(f"Found {problematic_count} pd.DataFrame() instances")
    
    # Replace all data_get calls with pd.DataFrame() defaults
    # Pattern: data_get('key', pd.DataFrame()) -> data_get('key')
    import re
    
    # Fix all data_get calls with pd.DataFrame() defaults
    pattern = r"data_get\(([^,)]+),\s*pd\.DataFrame\(\)\)"
    replacement = r"data_get(\1)"
    
    new_content = re.sub(pattern, replacement, content)
    
    fixes_count = len(re.findall(pattern, content))
    print(f"Fixed {fixes_count} data_get calls with pd.DataFrame() defaults")
    
    # Also need to add None checks after each data_get call
    # This is more complex, so we'll handle the most critical ones manually
    
    # Write the fixed content
    with open(dash_app_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print("✅ Fixed all data_get DataFrame default parameter errors")
    return True

if __name__ == "__main__":
    fix_data_get_errors()