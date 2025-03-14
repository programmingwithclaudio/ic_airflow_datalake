#!/bin/bash

# Crear la estructura de directorios
mkdir -p dags plugins spark/jobs data/input data/output data/checkpoint requirements

# Crear un archivo requirements.txt básico
cat > requirements/requirements.txt << 'EOF'
# Core components
apache-airflow-providers-apache-spark==4.1.5
apache-airflow-providers-openlineage==1.8.0
apache-airflow-providers-apache-kafka==1.1.0
apache-airflow-providers-amazon==7.3.0
kafka-python==2.0.2

# Data processing
pandas==1.5.3
numpy==1.24.2
pyarrow==12.0.0

# MinIO/S3 interaction
boto3==1.26.151
s3fs==2023.5.0

# Database clients
psycopg2-binary==2.9.6
pymongo==4.3.3
redis==4.5.5

# Utilities
python-dotenv==1.0.0
pyyaml==6.0
requests==2.31.0
EOF

# Crear un DAG de ejemplo
mkdir -p dags
cat > dags/example_minio_dag.py << 'EOF'
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
import boto3
from io import StringIO
import pandas as pd

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

def _create_s3_client():
    s3_endpoint = 'http://minio:9000'
    s3_client = boto3.client(
        's3',
        endpoint_url=s3_endpoint,
        aws_access_key_id='minioadmin',
        aws_secret_access_key='minioadmin',
        region_name='us-east-1'
    )
    return s3_client

def create_bucket():
    s3_client = _create_s3_client()
    
    # Crear bucket si no existe
    try:
        s3_client.create_bucket(Bucket='data-bucket')
        print("Bucket 'data-bucket' creado con éxito")
    except s3_client.exceptions.BucketAlreadyOwnedByYou:
        print("Bucket 'data-bucket' ya existe")

def upload_test_data():
    s3_client = _create_s3_client()
    
    # Crear algunos datos de ejemplo
    data = {
        'id': range(1, 11),
        'name': [f'Item {i}' for i in range(1, 11)],
        'value': [i * 10 for i in range(1, 11)]
    }
    df = pd.DataFrame(data)
    
    # Convertir a CSV
    csv_buffer = StringIO()
    df.to_csv(csv_buffer, index=False)
    
    # Subir a MinIO
    s3_client.put_object(
        Bucket='data-bucket',
        Key='example/data.csv',
        Body=csv_buffer.getvalue()
    )
    print("Datos subidos con éxito a 'data-bucket/example/data.csv'")

with DAG(
    'minio_example',
    default_args=default_args,
    description='Test MinIO connection',
    schedule_interval=timedelta(days=1),
    start_date=datetime(2023, 1, 1),
    catchup=False,
) as dag:
    
    create_bucket_task = PythonOperator(
        task_id='create_bucket',
        python_callable=create_bucket,
    )
    
    upload_data_task = PythonOperator(
        task_id='upload_test_data',
        python_callable=upload_test_data,
    )
    
    create_bucket_task >> upload_data_task
EOF

echo "Estructura del proyecto creada satisfactoriamente."