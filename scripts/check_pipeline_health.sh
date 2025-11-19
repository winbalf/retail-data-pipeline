#!/bin/bash
# Pipeline Health Check Script
# Runs a series of checks to verify the pipeline is working correctly

set -e

echo "=========================================="
echo "🔍 Retail Data Pipeline Health Check"
echo "=========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Track overall status
ALL_CHECKS_PASSED=true

# Function to print status
print_status() {
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✅ $2${NC}"
    else
        echo -e "${RED}❌ $2${NC}"
        ALL_CHECKS_PASSED=false
    fi
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

# 1. Check Docker services
echo "1️⃣  Checking Docker services..."
echo "-----------------------------------"
if docker-compose ps | grep -q "Up"; then
    print_status 0 "Docker services are running"
    docker-compose ps | grep -E "NAME|retail" | head -10
else
    print_status 1 "Docker services are not running"
    echo "   Run: docker-compose up -d"
fi
echo ""

# 2. Check PostgreSQL
echo "2️⃣  Checking PostgreSQL..."
echo "-----------------------------------"
if docker-compose exec -T postgres pg_isready -U retail_user -d retail_analytics >/dev/null 2>&1; then
    print_status 0 "PostgreSQL is accessible"
    
    # Check if tables exist
    TABLE_COUNT=$(docker-compose exec -T postgres psql -U retail_user -d retail_analytics -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';" 2>/dev/null | tr -d ' ')
    if [ -n "$TABLE_COUNT" ] && [ "$TABLE_COUNT" -gt 0 ]; then
        print_status 0 "Database schema exists ($TABLE_COUNT tables)"
        
        # Check for data
        FACT_COUNT=$(docker-compose exec -T postgres psql -U retail_user -d retail_analytics -t -c "SELECT COUNT(*) FROM fact_sales;" 2>/dev/null | tr -d ' ')
        if [ -n "$FACT_COUNT" ]; then
            if [ "$FACT_COUNT" -gt 0 ]; then
                print_status 0 "Data exists in fact_sales ($FACT_COUNT records)"
            else
                print_warning "fact_sales table is empty (pipeline may not have run yet)"
            fi
        fi
    else
        print_warning "Database schema not found (tables don't exist)"
    fi
else
    print_status 1 "PostgreSQL is not accessible"
fi
echo ""

# 3. Check Airflow
echo "3️⃣  Checking Airflow..."
echo "-----------------------------------"
if curl -s -f http://localhost:8080/health >/dev/null 2>&1; then
    print_status 0 "Airflow webserver is accessible"
    echo "   UI: http://localhost:8080"
else
    print_status 1 "Airflow webserver is not accessible"
    echo "   Check: docker-compose logs airflow-webserver"
fi

# Check scheduler
if docker-compose exec -T airflow-scheduler airflow jobs check --job-type SchedulerJob >/dev/null 2>&1; then
    print_status 0 "Airflow scheduler is running"
else
    print_warning "Airflow scheduler may not be running"
    echo "   Check: docker-compose logs airflow-scheduler"
fi
echo ""

# 4. Check Retailer APIs
echo "4️⃣  Checking Retailer APIs..."
echo "-----------------------------------"
for i in 1 2 3; do
    if curl -s -f http://localhost:500$i/health >/dev/null 2>&1; then
        print_status 0 "Retailer $i API is accessible"
    else
        print_status 1 "Retailer $i API is not accessible"
    fi
done
echo ""

# 5. Check S3 Connection
echo "5️⃣  Checking S3 Connection..."
echo "-----------------------------------"
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
    
    if [ -n "$S3_BUCKET_RAW" ]; then
        echo "   Bucket: $S3_BUCKET_RAW"
        
        # Try to test S3 connection
        if docker-compose run --rm ingestion python scripts/test_s3.py >/tmp/s3_test.log 2>&1; then
            print_status 0 "S3 connection successful"
            # Count files if any
            FILE_COUNT=$(grep -c "📄" /tmp/s3_test.log 2>/dev/null || echo "0")
            if [ "$FILE_COUNT" -gt 0 ]; then
                echo "   Files found in S3 (check output above)"
            else
                print_warning "S3 bucket is empty (run ingestion first)"
            fi
        else
            print_status 1 "S3 connection failed"
            echo "   Check: cat /tmp/s3_test.log"
        fi
    else
        print_warning "S3_BUCKET_RAW not set in .env"
    fi
else
    print_warning ".env file not found"
fi
echo ""

# 6. Check Environment Variables
echo "6️⃣  Checking Environment Variables..."
echo "-----------------------------------"
REQUIRED_VARS=("AWS_ACCESS_KEY_ID" "AWS_SECRET_ACCESS_KEY" "S3_BUCKET_RAW" "POSTGRES_USER" "POSTGRES_PASSWORD")
MISSING_VARS=()

if [ -f .env ]; then
    for var in "${REQUIRED_VARS[@]}"; do
        if grep -q "^${var}=" .env && ! grep -q "^${var}=$" .env && ! grep -q "^${var}=your" .env; then
            print_status 0 "$var is set"
        else
            print_status 1 "$var is missing or not configured"
            MISSING_VARS+=("$var")
        fi
    done
else
    print_status 1 ".env file not found"
    echo "   Run: make setup"
fi
echo ""

# 7. Check Recent Pipeline Activity
echo "7️⃣  Checking Recent Pipeline Activity..."
echo "-----------------------------------"
if docker-compose exec -T postgres psql -U retail_user -d retail_analytics -t -c "SELECT COUNT(*) FROM fact_sales;" >/dev/null 2>&1; then
    LAST_RECORD=$(docker-compose exec -T postgres psql -U retail_user -d retail_analytics -t -c "SELECT MAX(created_at) FROM fact_sales;" 2>/dev/null | tr -d ' ')
    if [ -n "$LAST_RECORD" ] && [ "$LAST_RECORD" != "" ]; then
        echo "   Last record inserted: $LAST_RECORD"
        print_status 0 "Pipeline has processed data"
    else
        print_warning "No records found (pipeline may not have run)"
    fi
else
    print_warning "Could not check pipeline activity"
fi
echo ""

# Summary
echo "=========================================="
echo "📋 Summary"
echo "=========================================="
if [ "$ALL_CHECKS_PASSED" = true ] && [ ${#MISSING_VARS[@]} -eq 0 ]; then
    echo -e "${GREEN}✅ All checks passed! Pipeline appears to be healthy.${NC}"
    echo ""
    echo "Next steps:"
    echo "  1. Open Airflow UI: http://localhost:8080"
    echo "  2. Enable the 'retail_data_pipeline' DAG"
    echo "  3. Trigger a manual run or wait for scheduled run (2 AM daily)"
    exit 0
else
    echo -e "${YELLOW}⚠️  Some checks failed. Please review the issues above.${NC}"
    echo ""
    echo "Common fixes:"
    echo "  - Start services: docker-compose up -d"
    echo "  - Check logs: docker-compose logs [service_name]"
    echo "  - Configure .env: Edit .env file with your credentials"
    echo "  - See docs/TROUBLESHOOTING.md for detailed help"
    exit 1
fi

