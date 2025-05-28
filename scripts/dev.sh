#!/bin/bash
# Switch to development environment and start the server

echo "🔄 Switching to development environment..."
python3 scripts/switch_env.py switch development

if [ $? -eq 0 ]; then
    echo "🚀 Starting development server..."
    # Activate virtual environment and run the server
    source venv/bin/activate && python main.py
else
    echo "❌ Failed to switch to development environment"
    exit 1
fi
