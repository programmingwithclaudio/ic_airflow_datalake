from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator
import psycopg2
from minio import Minio
import random
import csv
import os

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2025, 3, 13),
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

dag = DAG(
    'data_pipeline_etl',
    default_args=default_args,
    description='Pipeline ETL: Generar datos, ETL con Spark y carga a Postgres',
    schedule_interval=timedelta(hours=1),
)

# Tarea 1: Generar datos aleatorios y subirlos a MinIO
def generar_y_subir_datos():
    # Generamos un archivo CSV con datos aleatorios
    local_dir = "/tmp/input_data"
    os.makedirs(local_dir, exist_ok=True)
    file_path = f"{local_dir}/data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    with open(file_path, "w", newline="") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["timestamp", "value"])
        for _ in range(100):
            writer.writerow([datetime.now().isoformat(), random.uniform(0, 100)])
    
    # Conectamos a MinIO y subimos el archivo
    client = Minio(
        "minio:9000",
        access_key="minioadmin",
        secret_key="minioadmin",
        secure=False
    )
    bucket_name = "test"
    if not client.bucket_exists(bucket_name):
        client.make_bucket(bucket_name)
    
    client.fput_object(bucket_name, os.path.basename(file_path), file_path)
    print(f"Archivo {file_path} subido a MinIO en el bucket '{bucket_name}'.")

generar_datos_task = PythonOperator(
    task_id='generar_y_subir_datos',
    python_callable=generar_y_subir_datos,
    dag=dag,
)

# Tarea 2: Ejecutar el job de Spark Streaming (ETL)
spark_job = BashOperator(
    task_id='spark_streaming_job',
    bash_command='spark-submit --master spark://spark-master:7077 /opt/airflow/spark/spark_job.py',
    dag=dag,
)

# Tarea 3: Cargar los datos transformados en Postgres
def cargar_postgres():
    try:
        # Se asume que Spark escribe el resultado en CSV en /opt/airflow/data/output/result.csv
        output_file = "/opt/airflow/data/output/result.csv"
        conn = psycopg2.connect(
            dbname="airflow",
            user="airflow",
            password="airflow",
            host="postgres_airflow",
            port="5432"
        )
        cur = conn.cursor()
        # Se debe tener creada la tabla 'my_new_table' en Postgres
        with open(output_file, "r") as f:
            next(f)  # Saltar encabezado
            for line in f:
                timestamp, avg_value = line.strip().split(',')
                cur.execute("INSERT INTO my_new_table (timestamp, avg_value) VALUES (%s, %s)",
                            (timestamp, avg_value))
        conn.commit()
        cur.close()
        conn.close()
        print("Datos cargados correctamente en Postgres.")
    except Exception as e:
        print(f"Error al cargar datos en Postgres: {e}")

cargar_postgres_task = PythonOperator(
    task_id='cargar_postgres',
    python_callable=cargar_postgres,
    dag=dag,
)

# Secuencia de ejecución del DAG
generar_datos_task >> spark_job >> cargar_postgres_task
