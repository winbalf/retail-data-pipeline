"""
Airflow DAG for retail data pipeline.
Orchestrates daily ingestion from 3 retailers and transformation to star schema.
"""
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator

# Default arguments
default_args = {
    'owner': 'retail_analytics',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
    'start_date': datetime(2024, 1, 1),
}

# DAG definition
dag = DAG(
    'retail_data_pipeline',
    default_args=default_args,
    description='End-to-end retail analytics data pipeline',
    schedule_interval='0 2 * * *',  # Run daily at 2 AM
    catchup=False,
    tags=['retail', 'analytics', 'etl'],
)

def get_execution_date(**context):
    """
    Extract execution date from Airflow context.
    Ensures consistent date handling across all tasks.
    
    Returns:
        tuple: (execution_date datetime, date_str string)
    """
    from datetime import datetime, timedelta
    
    # Priority: data_interval_start (Airflow 2.x) > execution_date > yesterday
    if 'data_interval_start' in context and context['data_interval_start']:
        execution_date = context['data_interval_start']
    elif 'execution_date' in context and context['execution_date']:
        execution_date = context['execution_date']
    else:
        # Fallback to yesterday for manual triggers
        execution_date = datetime.now() - timedelta(days=1)
    
    date_str = execution_date.strftime('%Y-%m-%d')
    return execution_date, date_str

def run_ingestion(**context):
    """Run ingestion service to fetch data from retailers and upload to S3."""
    import sys
    import os
    
    # Add paths - need to add parent directory so ingestion can be imported as a package
    if '/opt/airflow' not in sys.path:
        sys.path.insert(0, '/opt/airflow')
    if '/opt/airflow/shared' not in sys.path:
        sys.path.insert(0, '/opt/airflow/shared')
    
    # Get execution date using shared function
    execution_date, date_str = get_execution_date(**context)
    print(f"📅 Running ingestion for date: {date_str} (execution_date: {execution_date})")
    
    # Import and run ingestion
    from ingestion.main import main as ingestion_main
    
    # Override sys.argv to pass date
    original_argv = sys.argv
    sys.argv = ['ingestion', date_str]
    
    try:
        result = ingestion_main()
        print(f"✅ Ingestion completed with {result} records for date: {date_str}")
        # Return date_str so transformation task can use the exact same date
        return {'date_str': date_str, 'records': result}
    finally:
        sys.argv = original_argv

def run_transformation(**context):
    """Run transformation service to load S3 data into PostgreSQL star schema."""
    import sys
    import os
    
    # Add paths - need to add parent directory so transformation can be imported as a package
    if '/opt/airflow' not in sys.path:
        sys.path.insert(0, '/opt/airflow')
    if '/opt/airflow/shared' not in sys.path:
        sys.path.insert(0, '/opt/airflow/shared')
    
    # Try to get date from previous task (ingestion) via XCom to ensure exact match
    # If not available (e.g., manual trigger of just this task), use context
    ti = context['ti']
    ingestion_result = ti.xcom_pull(task_ids='ingest_retailers_to_s3')
    
    if ingestion_result and 'date_str' in ingestion_result:
        # Use the same date that ingestion used
        date_str = ingestion_result['date_str']
        print(f"📅 Using date from ingestion task: {date_str}")
    else:
        # Fallback: get date from context (for manual triggers or if ingestion failed)
        execution_date, date_str = get_execution_date(**context)
        print(f"📅 Running transformation for date: {date_str} (execution_date: {execution_date})")
    
    # Import and run transformation
    from transformation.main import main as transformation_main
    
    # Override sys.argv to pass date
    original_argv = sys.argv
    sys.argv = ['transformation', date_str]
    
    try:
        transformation_main()
        print(f"✅ Transformation completed for date: {date_str}")
    finally:
        sys.argv = original_argv

def run_data_quality(**context):
    """Run data quality checks on transformed data in PostgreSQL."""
    import sys
    import os
    
    # Add paths - need to add parent directory so data_quality can be imported as a package
    if '/opt/airflow' not in sys.path:
        sys.path.insert(0, '/opt/airflow')
    if '/opt/airflow/shared' not in sys.path:
        sys.path.insert(0, '/opt/airflow/shared')
    
    # Try to get date from previous task (transformation) via XCom to ensure exact match
    # If not available (e.g., manual trigger of just this task), use context
    ti = context['ti']
    transformation_result = ti.xcom_pull(task_ids='transform_s3_to_postgres')
    ingestion_result = ti.xcom_pull(task_ids='ingest_retailers_to_s3')
    
    # Try to get date from transformation or ingestion task
    if transformation_result:
        # Transformation doesn't return date, so try ingestion
        if ingestion_result and 'date_str' in ingestion_result:
            date_str = ingestion_result['date_str']
            print(f"📅 Using date from ingestion task: {date_str}")
        else:
            # Fallback: get date from context
            execution_date, date_str = get_execution_date(**context)
            print(f"📅 Running data quality checks for date: {date_str} (execution_date: {execution_date})")
    elif ingestion_result and 'date_str' in ingestion_result:
        date_str = ingestion_result['date_str']
        print(f"📅 Using date from ingestion task: {date_str}")
    else:
        # Fallback: get date from context (for manual triggers or if previous tasks failed)
        execution_date, date_str = get_execution_date(**context)
        print(f"📅 Running data quality checks for date: {date_str} (execution_date: {execution_date})")
    
    # Import and run data quality checks
    from data_quality.main import main as data_quality_main
    
    # Override sys.argv to pass date
    original_argv = sys.argv
    sys.argv = ['data_quality', date_str]
    
    try:
        results = data_quality_main()
        print(f"✅ Data quality checks completed for date: {date_str}")
        # Return results for potential downstream usage
        return results
    finally:
        sys.argv = original_argv

# Task 1: Ingest data from all retailers to S3
ingest_task = PythonOperator(
    task_id='ingest_retailers_to_s3',
    python_callable=run_ingestion,
    dag=dag,
)

# Task 2: Transform S3 data to PostgreSQL star schema
transform_task = PythonOperator(
    task_id='transform_s3_to_postgres',
    python_callable=run_transformation,
    dag=dag,
)

# Task 3: Data quality check
data_quality_task = PythonOperator(
    task_id='data_quality_check',
    python_callable=run_data_quality,
    dag=dag,
)

# Define task dependencies
ingest_task >> transform_task >> data_quality_task

