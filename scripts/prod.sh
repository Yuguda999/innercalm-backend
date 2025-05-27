#!/bin/bash
# Switch to production environment and start the server

echo "🔄 Switching to production environment..."
python3 scripts/switch_env.py switch production

if [ $? -eq 0 ]; then
    echo "🚀 Starting production server..."
    python3 main.py
else
    echo "❌ Failed to switch to production environment"
    exit 1
fi
