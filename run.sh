#!/usr/bin/env bash

# Exit immediately if a command fails
set -e

# Go to the directory where the script lives
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"

# Cleanup function to kill background processes on exit
cleanup() {
    echo "Shutting down..."
    kill $CSS_PID 2>/dev/null
    exit 0
}
trap cleanup SIGINT SIGTERM

# Start Tailwind CSS watcher in background
npm run watch:css &
CSS_PID=$!

# Run Django development server
python ./notibac/manage.py runserver
