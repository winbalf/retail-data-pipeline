#!/bin/bash
# Generic wrapper script to run docker-compose commands with network issue fallback

set -e

cd "$(dirname "$0")/.."

# Source .env file if it exists
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
fi

# Get the service name and command from arguments
SERVICE="$1"
shift
COMMAND="$@"

if [ -z "$SERVICE" ] || [ -z "$COMMAND" ]; then
    echo "Usage: $0 <service> <command>"
    exit 1
fi

# Ensure required services are running (for ingestion/transformation)
if [ "$SERVICE" = "ingestion" ] || [ "$SERVICE" = "transformation" ]; then
    echo "Starting required services..."
    docker-compose up -d postgres retailer1-api retailer2-api retailer3-api 2>/dev/null || true
    echo "Waiting for services to be ready..."
    sleep 3
fi

# Try docker-compose run first
TMP_OUTPUT=$(mktemp)
set +e  # Don't exit on error
docker-compose run --rm "$SERVICE" $COMMAND > "$TMP_OUTPUT" 2>&1
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
    IMAGE_NAME="${PROJECT_NAME}_${SERVICE}:latest"
    
    # Verify image exists
    if ! docker images --format "{{.Repository}}:{{.Tag}}" | grep -q "^${IMAGE_NAME}$"; then
        echo "Building ${SERVICE} image..."
        docker-compose build "$SERVICE" || {
            echo "Error: Failed to build ${SERVICE} image"
            exit 1
        }
    fi
    
    echo "Running with docker run..."
    
    # Build environment variables based on service
    ENV_ARGS=""
    if [ "$SERVICE" = "ingestion" ] || [ "$SERVICE" = "transformation" ]; then
        ENV_ARGS="-e AWS_ACCESS_KEY_ID=\"${AWS_ACCESS_KEY_ID}\" \
        -e AWS_SECRET_ACCESS_KEY=\"${AWS_SECRET_ACCESS_KEY}\" \
        -e AWS_DEFAULT_REGION=\"${AWS_DEFAULT_REGION:-us-east-1}\" \
        -e S3_BUCKET_RAW=\"${S3_BUCKET_RAW}\" \
        -e S3_BUCKET_PROCESSED=\"${S3_BUCKET_PROCESSED}\" \
        -e RETAILER_1_API_URL=\"${RETAILER_1_API_URL:-http://retailer1-api:5001}\" \
        -e RETAILER_1_API_KEY=\"${RETAILER_1_API_KEY:-retailer1_api_key_123}\" \
        -e RETAILER_2_API_URL=\"${RETAILER_2_API_URL:-http://retailer2-api:5002}\" \
        -e RETAILER_2_API_KEY=\"${RETAILER_2_API_KEY:-retailer2_api_key_123}\" \
        -e RETAILER_3_API_URL=\"${RETAILER_3_API_URL:-http://retailer3-api:5003}\" \
        -e RETAILER_3_API_KEY=\"${RETAILER_3_API_KEY:-retailer3_api_key_123}\" \
        -e POSTGRES_HOST=postgres \
        -e POSTGRES_PORT=5432 \
        -e POSTGRES_USER=\"${POSTGRES_USER:-retail_user}\" \
        -e POSTGRES_PASSWORD=\"${POSTGRES_PASSWORD}\" \
        -e POSTGRES_DB=\"${POSTGRES_DB:-retail_analytics}\""
    fi
    
    # Run with docker directly
    # Build volume mounts
    VOLUME_ARGS="-v \"$(pwd)/${SERVICE}:/app/${SERVICE}\" \
        -v \"$(pwd)/shared:/app/shared\" \
        -v \"$(pwd)/logs:/app/logs\""
    
    # Add scripts directory if command references scripts/
    if echo "$COMMAND" | grep -q "scripts/"; then
        VOLUME_ARGS="$VOLUME_ARGS -v \"$(pwd)/scripts:/app/scripts\""
    fi
    
    eval docker run --rm \
        --network retail-data-pipeline_retail_network \
        $ENV_ARGS \
        $VOLUME_ARGS \
        "$IMAGE_NAME" \
        $COMMAND
else
    # docker-compose run worked (or failed for other reasons), show output
    cat "$TMP_OUTPUT"
    rm -f "$TMP_OUTPUT"
    exit $EXIT_CODE
fi

