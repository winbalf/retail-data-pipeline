#!/bin/bash
# Script to view Airflow task logs for debugging

echo "To view task logs in Airflow UI:"
echo ""
echo "1. Go to http://localhost:8080"
echo "2. Click on the DAG 'retail_data_pipeline'"
echo "3. Click on the failed task (red square)"
echo "4. Click 'View Log' button"
echo ""
echo "Or view recent scheduler logs:"
docker-compose logs --tail=100 airflow-scheduler | grep -A 5 -B 5 "ingest_retailers_to_s3"

