#!/bin/bash
# Switch to testing environment and run tests

echo "🔄 Switching to testing environment..."
python3 scripts/switch_env.py switch testing

if [ $? -eq 0 ]; then
    echo "🧪 Running tests..."
    python3 -m pytest tests/ -v
else
    echo "❌ Failed to switch to testing environment"
    exit 1
fi
