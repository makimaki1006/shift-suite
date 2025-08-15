#!/usr/bin/env python3
# Simple import test without problematic modules

import sys
import os
import traceback
import pandas as pd
from pathlib import Path

# Add the current directory to Python path
sys.path.insert(0, os.getcwd())

print("Testing basic imports...")

try:
    from shift_suite.tasks.io_excel import ingest_excel
    print("✓ io_excel import successful")
except Exception as e:
    print(f"✗ io_excel import failed: {e}")
    traceback.print_exc()

try:
    from shift_suite.tasks.heatmap import build_heatmap
    print("✓ heatmap import successful")
except Exception as e:
    print(f"✗ heatmap import failed: {e}")

try:
    from shift_suite.tasks.shortage import shortage_and_brief
    print("✓ shortage import successful")
except Exception as e:
    print(f"✗ shortage import failed: {e}")

try:
    from shift_suite.tasks.build_stats import build_stats
    print("✓ build_stats import successful")
except Exception as e:
    print(f"✗ build_stats import failed: {e}")

print("Basic import test completed")