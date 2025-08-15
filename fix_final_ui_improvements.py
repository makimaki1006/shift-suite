#!/usr/bin/env python3
"""
Final UI improvements with simplified approach
"""

def apply_final_ui_improvements():
    """Apply final UI improvements with proper color scheme"""
    
    dash_app_path = "C:\\ShiftAnalysis\\dash_app.py"
    
    print("Reading dash_app.py...")
    with open(dash_app_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 1. Add clientside callback for tab switching
    clientside_callback = '''
    # Enhanced tab switching with clientside callback
    app.clientside_callback(
        """
        function(active_tab) {
            // Ensure content is visible when tab switches
            setTimeout(function() {
                var tabContent = document.getElementById('tab-content');
                if (tabContent) {
                    tabContent.style.opacity = '1';
                    tabContent.style.visibility = 'visible';
                    tabContent.style.backgroundColor = '#ffffff';
                    tabContent.style.color = '#1a202c';
                    
                    // Make all child elements visible
                    var allElements = tabContent.querySelectorAll('*');
                    allElements.forEach(function(element) {
                        if (element.style) {
                            element.style.opacity = '1';
                            element.style.visibility = 'visible';
                        }
                    });
                }
            }, 50);
            return active_tab;
        }
        """,
        Output('main-tabs', 'value'),
        Input('main-tabs', 'value'),
        prevent_initial_call=False
    )
    '''
    
    # 2. Comprehensive style improvements
    style_improvements = [
        # Fix color contrast issues
        ("'color': '#ff9800'", "'color': '#d97706', 'fontWeight': '600'"),
        ("'color': 'red'", "'color': '#dc2626', 'fontWeight': '600'"),
        ("'color': '#666'", "'color': '#4b5563'"),
        ("'backgroundColor': '#f8f9fa'", "'backgroundColor': '#ffffff'"),
        
        # Improve card styling
        ("'padding': '20px'", "'padding': '24px'"),
        ("'borderRadius': '8px'", "'borderRadius': '12px'"),
        ("'boxShadow': '0 2px 4px rgba(0,0,0,0.1)'", "'boxShadow': '0 4px 8px rgba(0,0,0,0.12)'"),
        
        # Text improvements
        ("'fontSize': '16px'", "'fontSize': '16px', 'lineHeight': '1.6'"),
        ("'color': '#2c3e50'", "'color': '#1f2937'"),
        ("'color': '#34495e'", "'color': '#374151'"),
    ]
    
    # Apply style improvements
    for old_style, new_style in style_improvements:
        content = content.replace(old_style, new_style)
    
    # 3. Add the clientside callback before any existing callbacks
    lines = content.split('\\n')
    callback_inserted = False
    
    for i, line in enumerate(lines):
        if '@app.callback' in line and not callback_inserted:
            lines.insert(i, clientside_callback)
            callback_inserted = True
            break
    
    if not callback_inserted:
        # Insert near the end if no callbacks found
        lines.insert(-10, clientside_callback)
    
    content = '\\n'.join(lines)
    
    # 4. Fix specific layout issues in tab content containers
    layout_fixes = [
        # Ensure main tab content has proper styling
        (
            "html.Div(id='tab-content')",
            """html.Div(
                id='tab-content',
                style={
                    'backgroundColor': '#ffffff',
                    'color': '#1f2937',
                    'padding': '24px',
                    'minHeight': '600px',
                    'fontSize': '16px',
                    'lineHeight': '1.6',
                    'opacity': '1',
                    'visibility': 'visible'
                }
            )"""
        ),
        
        # Fix proportional abolition content styling
        (
            "'backgroundColor': '#e8f4fd'",
            "'backgroundColor': '#f0f9ff', 'color': '#1f2937'"
        ),
        
        # Enhance data tables
        (
            "dash_table.DataTable(",
            """dash_table.DataTable(
                style_table={'backgroundColor': '#ffffff'},"""
        )
    ]
    
    for old_layout, new_layout in layout_fixes:
        content = content.replace(old_layout, new_layout)
    
    # Write the improved content
    with open(dash_app_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("Applied final UI improvements:")
    print("- Added clientside callback for immediate tab visibility")
    print("- Improved color contrast across all elements")
    print("- Enhanced layout spacing and typography")
    print("- Fixed remaining visibility issues")
    print("- Improved overall user experience")
    return True

if __name__ == "__main__":
    apply_final_ui_improvements()