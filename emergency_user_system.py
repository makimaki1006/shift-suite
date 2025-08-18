#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Emergency User System - 確実に動作する最小システム
"""

import subprocess
import sys
import time
import os
from pathlib import Path

def find_free_port(start_port=8090):
    """空いているポートを見つける"""
    import socket
    for port in range(start_port, start_port + 10):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('localhost', port))
                return port
        except OSError:
            continue
    return None

def emergency_dash_system():
    """緊急Dashシステム起動"""
    print("=" * 60)
    print("EMERGENCY DASH SYSTEM")
    print("=" * 60)
    
    # Find free port
    port = find_free_port(8090)
    if not port:
        print("ERROR: No free ports available")
        return False
    
    print(f"Using port: {port}")
    print(f"URL: http://localhost:{port}")
    print("Starting in 3 seconds...")
    time.sleep(3)
    
    try:
        # Direct import and run
        import dash_app
        print("Dash app imported successfully")
        
        print("Starting server...")
        dash_app.app.run_server(
            debug=False,
            host='127.0.0.1',
            port=port,
            use_reloader=False,
            dev_tools_hot_reload=False,
            dev_tools_ui=False
        )
        
    except KeyboardInterrupt:
        print("\nSystem stopped by user")
        return True
    except Exception as e:
        print(f"ERROR: {e}")
        return False

def emergency_streamlit_system():
    """緊急Streamlitシステム起動"""
    print("=" * 60)
    print("EMERGENCY STREAMLIT SYSTEM")
    print("=" * 60)
    
    # Find free port
    port = find_free_port(8591)
    if not port:
        print("ERROR: No free ports available")
        return False
    
    print(f"Using port: {port}")
    print(f"URL: http://localhost:{port}")
    
    # Check if streamlit file exists
    if not Path("streamlit_shift_analysis.py").exists():
        print("ERROR: streamlit_shift_analysis.py not found")
        return False
    
    try:
        print("Starting Streamlit...")
        subprocess.run([
            sys.executable, "-m", "streamlit", "run",
            "streamlit_shift_analysis.py",
            "--server.port", str(port),
            "--server.headless", "true"
        ], check=True)
        
    except KeyboardInterrupt:
        print("\nSystem stopped by user")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Streamlit error: {e}")
        return False
    except Exception as e:
        print(f"ERROR: {e}")
        return False

def main():
    """メイン関数"""
    print("EMERGENCY USER SYSTEM LAUNCHER")
    print("Choose your system:")
    print("1. Dash System (dash_app.py)")
    print("2. Streamlit System")
    print("3. Auto-select best option")
    
    choice = input("Enter choice (1/2/3): ").strip()
    
    if choice == "1":
        return emergency_dash_system()
    elif choice == "2":
        return emergency_streamlit_system()
    elif choice == "3":
        print("Auto-selecting...")
        
        # Try Dash first
        try:
            import dash_app
            print("Dash available - starting Dash system")
            return emergency_dash_system()
        except:
            print("Dash not available - trying Streamlit")
            return emergency_streamlit_system()
    else:
        print("Invalid choice - auto-selecting")
        return main()

if __name__ == "__main__":
    try:
        success = main()
        if success:
            print("\nSUCCESS: User system is running")
        else:
            print("\nFAILED: Could not start user system")
    except KeyboardInterrupt:
        print("\nExiting...")
    except Exception as e:
        print(f"\nUNEXPECTED ERROR: {e}")
        print("Please report this issue")