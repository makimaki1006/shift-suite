#!/usr/bin/env python3
"""
Final syntax cleanup for dash_app.py
"""

def clean_syntax_errors():
    """Clean up all remaining syntax errors in dash_app.py"""
    
    dash_app_path = "C:\\ShiftAnalysis\\dash_app.py"
    
    print("Cleaning syntax errors...")
    
    with open(dash_app_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Fix common syntax issues
    fixes = [
        # Fix TEXT_STYLES indentation and duplicate keys
        ("        'header_text': {", "    'header_text': {"),
        ("            'color': '#1a202c',", "        'color': '#1a202c',"),
        ("            'fontSize': '22px',", "        'fontSize': '22px',"),
        ("            'fontWeight': 'bold',", "        'fontWeight': 'bold',"),
        ("            'marginBottom': '16px',", "        'marginBottom': '16px',"),
        ("            'opacity': '1'", "        'opacity': '1'"),
        ("        },", "    },"),
        ("        'emphasis_text': {", "    'emphasis_text': {"),
        ("            'color': '#2563eb',", "        'color': '#2563eb',"),
        ("            'fontWeight': '600',", "        'fontWeight': '600',"),
        ("        'warning_text': {", "    'warning_text': {"),
        ("            'color': '#dc2626',", "        'color': '#dc2626',"),
        ("            'fontSize': '16px',", "        'fontSize': '16px',"),
        ("            'backgroundColor': '#fef2f2',", "        'backgroundColor': '#fef2f2',"),
        ("            'padding': '8px 12px',", "        'padding': '8px 12px',"),
        ("            'borderRadius': '6px'", "        'borderRadius': '6px'"),
        
        # Fix duplicate keys and formatting
        ("'fontSize': '16px', 'lineHeight': '1.6'", "'fontSize': '16px', 'lineHeight': '1.6'"),
        ("    }\n        'padding':", "}\n\n# Additional styles\nADDITIONAL_STYLES = {\n    'padding':"),
        
        # Clean up any remaining syntax issues
        ("\\n\\n\\n", "\\n\\n"),
        ("    }    }", "    }\n}"),
    ]
    
    for old, new in fixes:
        content = content.replace(old, new)
    
    # Ensure proper dictionary closures
    lines = content.split('\\n')
    cleaned_lines = []
    in_dict = False
    brace_count = 0
    
    for i, line in enumerate(lines):
        # Track dictionary nesting
        brace_count += line.count('{') - line.count('}')
        
        # Clean up orphaned lines
        if line.strip().startswith("'padding'") and i > 0 and not lines[i-1].strip().endswith('{'):
            # This is an orphaned style line, skip it
            continue
            
        cleaned_lines.append(line)
    
    content = '\\n'.join(cleaned_lines)
    
    # Write cleaned content
    with open(dash_app_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("Syntax cleanup completed")
    
    # Test syntax
    try:
        compile(content, dash_app_path, 'exec')
        print("Syntax validation: PASSED")
        return True
    except SyntaxError as e:
        print(f"Syntax validation: FAILED at line {e.lineno}: {e.msg}")
        return False

if __name__ == "__main__":
    clean_syntax_errors()