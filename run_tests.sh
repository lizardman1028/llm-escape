#!/bin/bash
set -e

# Determine the directory where this script resides
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$SCRIPT_DIR"  # llm-escape/

# Set PYTHONPATH to project root
export PYTHONPATH="$PROJECT_ROOT"

echo "Running: tests/test_world_integration.py"
python "$PROJECT_ROOT/tests/test_world_integration.py"

echo ""
echo "Running: tests/test_scenarios.py"
python "$PROJECT_ROOT/tests/test_scenarios.py"

