#!/bin/bash
# Wrapper script to run ingestion, handling Docker network issues

set -e

cd "$(dirname "$0")/.."

# Source .env file if it exists
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
fi

# Check if network exists and needs recreation
if docker network inspect retail-data-pipeline_retail_network >/dev/null 2>&1; then
    # Try to start services - if it fails with network error, recreate network
    if ! docker-compose up -d postgres retailer1-api retailer2-api retailer3-api 2>&1 | grep -q "needs to be recreated"; then
        echo "Services started successfully"
    else
        echo "Network issue detected. Recreating network..."
        docker-compose down 2>/dev/null || true
        docker network rm retail-data-pipeline_retail_network 2>/dev/null || true
        docker-compose up -d postgres retailer1-api retailer2-api retailer3-api
    fi
else
    # Network doesn't exist, create it
    echo "Creating network and starting services..."
    docker-compose up -d postgres retailer1-api retailer2-api retailer3-api
fi

# Wait for services to be ready
echo "Waiting for services to be ready..."
sleep 5

# Get date parameter if provided (defaults to yesterday)
DATE_ARG="${1:-}"

# Run ingestion - try docker-compose first, fallback to docker run if network issue
echo "Running ingestion${DATE_ARG:+ for date: $DATE_ARG}..."

# Try docker-compose run first
TMP_OUTPUT=$(mktemp)
set +e  # Don't exit on error
if [ -n "$DATE_ARG" ]; then
    docker-compose run --rm ingestion python -m ingestion.main "$DATE_ARG" > "$TMP_OUTPUT" 2>&1
else
    docker-compose run --rm ingestion python -m ingestion.main > "$TMP_OUTPUT" 2>&1
fi
EXIT_CODE=$?
set -e  # Re-enable exit on error

# Check if it's a network recreation error
if grep -q "needs to be recreated" "$TMP_OUTPUT" 2>/dev/null; then
    # Network recreation error detected - use docker run directly
    cat "$TMP_OUTPUT"
    rm -f "$TMP_OUTPUT"
    echo ""
    echo "⚠️  Network validation issue detected. Using docker run directly..."
    
    # Get the image name (docker-compose uses project_name_service_name format)
    PROJECT_NAME=$(basename "$(pwd)" | tr '[:upper:]' '[:lower:]')
    IMAGE_NAME="${PROJECT_NAME}_ingestion:latest"
    
    # Verify image exists
    if ! docker images --format "{{.Repository}}:{{.Tag}}" | grep -q "^${IMAGE_NAME}$"; then
        echo "Building ingestion image..."
        docker-compose build ingestion || {
            echo "Error: Failed to build ingestion image"
            exit 1
        }
    fi
    
    echo "Running ingestion with docker run..."
    
    # Run with docker directly
    docker run --rm \
        --network retail-data-pipeline_retail_network \
        -e AWS_ACCESS_KEY_ID="${AWS_ACCESS_KEY_ID}" \
        -e AWS_SECRET_ACCESS_KEY="${AWS_SECRET_ACCESS_KEY}" \
        -e AWS_DEFAULT_REGION="${AWS_DEFAULT_REGION:-us-east-1}" \
        -e S3_BUCKET_RAW="${S3_BUCKET_RAW}" \
        -e RETAILER_1_API_URL="${RETAILER_1_API_URL:-http://retailer1-api:5001}" \
        -e RETAILER_1_API_KEY="${RETAILER_1_API_KEY:-retailer1_api_key_123}" \
        -e RETAILER_2_API_URL="${RETAILER_2_API_URL:-http://retailer2-api:5002}" \
        -e RETAILER_2_API_KEY="${RETAILER_2_API_KEY:-retailer2_api_key_123}" \
        -e RETAILER_3_API_URL="${RETAILER_3_API_URL:-http://retailer3-api:5003}" \
        -e RETAILER_3_API_KEY="${RETAILER_3_API_KEY:-retailer3_api_key_123}" \
        -e POSTGRES_HOST=postgres \
        -e POSTGRES_PORT=5432 \
        -e POSTGRES_USER="${POSTGRES_USER:-retail_user}" \
        -e POSTGRES_PASSWORD="${POSTGRES_PASSWORD}" \
        -e POSTGRES_DB="${POSTGRES_DB:-retail_analytics}" \
        -v "$(pwd)/ingestion:/app/ingestion" \
        -v "$(pwd)/shared:/app/shared" \
        -v "$(pwd)/logs:/app/logs" \
        "$IMAGE_NAME" \
        python -m ingestion.main ${DATE_ARG:+$DATE_ARG}
else
    # docker-compose run worked (or failed for other reasons), show output
    cat "$TMP_OUTPUT"
    rm -f "$TMP_OUTPUT"
    exit $EXIT_CODE
fi

