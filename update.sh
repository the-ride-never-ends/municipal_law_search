#!/bin/bash

# Quick deployment script for updates
# Use this for quick updates without full SSL setup

set -e

echo "Updating American Law Search application..."

# Get the directory where the script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Pull latest changes (if using git)
if [ -d ".git" ]; then
    echo "Pulling latest changes..."
    git pull
fi

# Rebuild and restart containers
echo "Rebuilding and restarting containers..."
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml up --build -d

echo "Application updated successfully!"
echo "View logs with: docker-compose -f docker-compose.prod.yml logs -f"