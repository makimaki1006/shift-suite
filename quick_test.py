#\!/usr/bin/env python3
import sys
try:
    import dash_app
    print("Import OK")
    if hasattr(dash_app, "create_shortage_tab"):
        print("Function exists")
        try:
            result = dash_app.create_shortage_tab()
            print(f"Call OK: {type(result)}")
        except Exception as e:
            print(f"Error: {type(e).__name__}: {e}")
            if "df_shortage_role_filtered" in str(e):
                print("ERROR: df_shortage_role_filtered issue\!")
except Exception as e:
    print(f"Import error: {e}")
