#!/usr/bin/env python3
"""
Fix tab content visibility issues - ensure all tab content is properly styled and visible
"""

def fix_tab_content_visibility():
    """Add proper styling to all tab content containers"""
    
    dash_app_path = "C:\\ShiftAnalysis\\dash_app.py"
    
    print("Reading dash_app.py...")
    with open(dash_app_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 1. Find and fix all dcc.Tab children styling
    import re
    
    # Pattern to find tab children without proper styling
    tab_pattern = r"dcc\.Tab\(label='([^']+)',\s*value='([^']+)',\s*children=\[\s*html\.Div\(([^}]+)\)\s*\]\)"
    
    def enhance_tab_content(match):
        label = match.group(1)
        value = match.group(2)
        content_part = match.group(3)
        
        # Check if styling is already applied
        if 'padding' in content_part and 'backgroundColor' in content_part:
            return match.group(0)  # Already styled
            
        # Add enhanced styling
        enhanced_content = f"""dcc.Tab(label='{label}', value='{value}', children=[
                        html.Div({content_part}, style={{
                            'backgroundColor': '#ffffff',
                            'color': '#1a202c',
                            'padding': '24px',
                            'minHeight': '400px',
                            'fontSize': '16px',
                            'lineHeight': '1.6'
                        }})
                    ])"""
        
        return enhanced_content
    
    # Apply the enhancement
    enhanced_content = re.sub(tab_pattern, enhance_tab_content, content, flags=re.MULTILINE | re.DOTALL)
    
    # 2. Add specific styling to main tab content area
    main_tab_content_old = "html.Div(id='tab-content')"
    main_tab_content_new = """html.Div(
        id='tab-content',
        style={
            'backgroundColor': '#ffffff',
            'color': '#1a202c',
            'padding': '20px',
            'minHeight': '500px',
            'fontSize': '16px',
            'lineHeight': '1.6'
        }
    )"""
    
    enhanced_content = enhanced_content.replace(main_tab_content_old, main_tab_content_new)
    
    # 3. Fix any remaining visibility issues in specific tabs
    visibility_fixes = [
        # Fix proportional abolition tab content
        (
            "html.Div(id='proportional-abolition-content')",
            """html.Div(
                id='proportional-abolition-content',
                style={
                    'backgroundColor': '#ffffff',
                    'color': '#1a202c',
                    'padding': '20px',
                    'fontSize': '16px',
                    'lineHeight': '1.6'
                }
            )"""
        ),
        # Fix other key content areas
        (
            "style={'color': '#666'",
            "style={'color': '#374151'"
        ),
        (
            "style={'color': 'red'}",
            "style={'color': '#dc2626', 'fontWeight': '600'}"
        ),
        (
            "style={'color': '#ff9800'}",
            "style={'color': '#f59e0b', 'fontWeight': '600'}"
        )
    ]
    
    for old_style, new_style in visibility_fixes:
        enhanced_content = enhanced_content.replace(old_style, new_style)
    
    # 4. Add CSS for tab switching improvements
    css_enhancement = '''
    
    # CSS for enhanced tab visibility and switching
    app.index_string = """
    <!DOCTYPE html>
    <html>
        <head>
            {%metas%}
            <title>{%title%}</title>
            {%favicon%}
            {%css%}
            <style>
                /* Enhanced Tab Visibility Styles */
                .dash-tab {
                    font-size: 14px !important;
                    font-weight: 600 !important;
                    color: #4a5568 !important;
                    background-color: #f7fafc !important;
                    border: 2px solid #e2e8f0 !important;
                    padding: 12px 20px !important;
                    transition: all 0.2s ease !important;
                }
                
                .dash-tab:hover {
                    background-color: #edf2f7 !important;
                    color: #2d3748 !important;
                }
                
                .dash-tab--selected {
                    background-color: #ffffff !important;
                    color: #1a202c !important;
                    font-weight: bold !important;
                    border-bottom: none !important;
                    border-top: 3px solid #2563eb !important;
                }
                
                /* Ensure tab content is always visible */
                .tab-content {
                    background-color: #ffffff !important;
                    color: #1a202c !important;
                    padding: 24px !important;
                    min-height: 400px !important;
                    font-size: 16px !important;
                    line-height: 1.6 !important;
                    opacity: 1 !important;
                    visibility: visible !important;
                }
                
                /* Fix text visibility issues */
                .dash-tab-content > div {
                    opacity: 1 !important;
                    visibility: visible !important;
                    color: #1a202c !important;
                }
                
                /* Improve contrast for better readability */
                h1, h2, h3, h4, h5, h6 {
                    color: #1a202c !important;
                    opacity: 1 !important;
                }
                
                p, div, span {
                    color: #374151 !important;
                    opacity: 1 !important;
                }
                
                .alert-info {
                    background-color: #e0f2fe !important;
                    color: #0277bd !important;
                    border: 1px solid #81d4fa !important;
                }
                
                .alert-warning {
                    background-color: #fff3e0 !important;
                    color: #f57c00 !important;
                    border: 1px solid #ffcc02 !important;
                }
                
                .alert-error {
                    background-color: #ffebee !important;
                    color: #d32f2f !important;
                    border: 1px solid #ef5350 !important;
                }
            </style>
        </head>
        <body>
            {%app_entry%}
            <footer>
                {%config%}
                {%scripts%}
                {%renderer%}
            </footer>
        </body>
    </html>
    """'''
    
    # Find where to insert the CSS
    lines = enhanced_content.split('\\n')
    app_creation_line = -1
    for i, line in enumerate(lines):
        if 'app = dash.Dash(' in line:
            app_creation_line = i
            break
    
    if app_creation_line >= 0:
        # Insert CSS enhancement after app creation
        lines.insert(app_creation_line + 10, css_enhancement)
        enhanced_content = '\\n'.join(lines)
    
    # Write the enhanced content
    with open(dash_app_path, 'w', encoding='utf-8') as f:
        f.write(enhanced_content)
    
    print("Fixed tab content visibility issues:")
    print("- Added proper styling to all tab content containers")
    print("- Enhanced tab switching visibility")
    print("- Fixed text color contrast issues")
    print("- Added CSS for better tab behavior")
    print("- Ensured all content is visible on load")
    return True

if __name__ == "__main__":
    fix_tab_content_visibility()