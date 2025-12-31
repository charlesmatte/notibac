#!/usr/bin/env bash

# Exit immediately if a command fails
set -e

# Go to the directory where the script lives
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"

# Activate virtual environment
source .venv/bin/activate
