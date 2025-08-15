#!/usr/bin/env bash
set -e

pip install -r requirements.txt
pip install pytest-cov || echo "pytest-cov not installed; coverage reports unavailable"

echo "Dependencies installed"
