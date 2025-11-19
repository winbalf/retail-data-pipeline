#!/bin/bash
# Script to fix Docker network recreation issues
# This script removes the network and lets Docker Compose recreate it with correct settings

set -e

cd "$(dirname "$0")/.."

echo "🔧 Fixing Docker network configuration..."

# Stop all containers
echo "Stopping containers..."
docker-compose down 2>/dev/null || true

# Remove the network if it exists
if docker network inspect retail-data-pipeline_retail_network >/dev/null 2>&1; then
    echo "Removing old network..."
    docker network rm retail-data-pipeline_retail_network 2>/dev/null || {
        # If removal fails due to active endpoints, stop containers first
        echo "Network has active endpoints. Stopping containers..."
        docker-compose stop 2>/dev/null || true
        docker-compose rm -f 2>/dev/null || true
        docker network rm retail-data-pipeline_retail_network 2>/dev/null || true
    }
fi

echo "✅ Network cleanup complete!"
echo "The network will be recreated automatically on the next docker-compose command."
echo ""
echo "You can now run your docker-compose commands normally."

