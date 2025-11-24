#!/bin/bash
# Script to update Grafana datasource configuration with environment variables
# This is useful since Grafana provisioning doesn't support env var substitution directly

set -e

# Load environment variables from .env file if it exists
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Set defaults if not in environment
POSTGRES_DB=${POSTGRES_DB:-retail_analytics}
# Use Grafana-specific user credentials (read-only access)
GRAFANA_DB_USER=${GRAFANA_DB_USER:-grafana_user}
GRAFANA_DB_PASSWORD=${GRAFANA_DB_PASSWORD:-grafana_password_123}

# Create datasource config directory if it doesn't exist
mkdir -p grafana/provisioning/datasources

# Generate datasource configuration
cat > grafana/provisioning/datasources/postgres.yml <<EOF
apiVersion: 1

datasources:
  - name: Retail Analytics PostgreSQL
    type: postgres
    access: proxy
    url: postgres:5432
    database: ${POSTGRES_DB}
    user: ${GRAFANA_DB_USER}
    secureJsonData:
      password: ${GRAFANA_DB_PASSWORD}
    jsonData:
      sslmode: disable
      maxOpenConns: 100
      maxIdleConns: 100
      connMaxLifetime: 14400
      postgresVersion: 1400
      timescaledb: false
    isDefault: true
    editable: true
EOF

echo "✅ Grafana datasource configuration updated!"
echo "   Database: ${POSTGRES_DB}"
echo "   User: ${GRAFANA_DB_USER}"
echo ""
echo "⚠️  Note: Restart Grafana container for changes to take effect:"
echo "   docker-compose restart grafana"

