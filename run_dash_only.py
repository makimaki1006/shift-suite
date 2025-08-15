#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dash only launcher - no Streamlit conflict
"""

import sys
import os
from pathlib import Path

# Add current directory to Python path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

print("🚀 Dash起動中...")
print("📍 ブラウザでアクセス: http://localhost:8050")

# Import and run dash app directly
import dash_app

if __name__ == "__main__":
    # Run the dash app
    dash_app.app.run_server(
        debug=False,
        host='127.0.0.1',
        port=8050,
        use_reloader=False  # Important: disable reloader to avoid signal issues
    )