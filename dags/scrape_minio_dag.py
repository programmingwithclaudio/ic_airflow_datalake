from datetime import datetime, timedelta
import os
import tempfile
import re
import zipfile
from selenium import webdriver
from bs4 import BeautifulSoup
import requests
import psycopg2
from psycopg2.extras import RealDictCursor
import boto3
from dotenv import load_dotenv

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.dummy import DummyOperator
from airflow.utils.task_group import TaskGroup
from airflow.models import Variable

load_dotenv()

# Configuración por defecto del DAG
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 3,
    'retry_delay': timedelta(minutes=5),
}

# Clase para representar archivos de Aduanet
class Aduanet:
    def __init__(self, id, name, url, fecha):
        self.id = id
        self.name = name
        self.url = url
        self.fecha = fecha

# Cliente de base de datos PostgreSQL
class ZipsRepository:
    def __init__(self):
        self.connection = psycopg2.connect(os.getenv("DATABASE_URL"))
        self.cursor = self.connection.cursor(cursor_factory=RealDictCursor)
        self.create_table_if_not_exists()

    def create_table_if_not_exists(self):
        create_table_query = """
        CREATE TABLE IF NOT EXISTS public.aduanet (
            id SERIAL PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            url TEXT NOT NULL,
            download_date TIMESTAMP NOT NULL,
            status VARCHAR(50) DEFAULT 'staged',
            staging_path TEXT,
            minio_path TEXT
        );
        """
        self.cursor.execute(create_table_query)
        self.connection.commit()

    def save_zip_file(self, name, url, staging_path=None):
        if not self.zip_file_exists(name):
            query = """
            INSERT INTO public.aduanet(name, url, download_date, staging_path)
            VALUES (%s, %s, %s, %s)
            """
            self.cursor.execute(query, (name, url, datetime.now(), staging_path))
            self.connection.commit()
            return True
        return False

    def update_zip_status(self, name, status, minio_path=None):
        query = """
        UPDATE public.aduanet
        SET status = %s, minio_path = %s
        WHERE name = %s
        """
        self.cursor.execute(query, (status, minio_path, name))
        self.connection.commit()

    def get_staged_files(self, prefix=None):
        if prefix:
            query = "SELECT * FROM public.aduanet WHERE status = 'staged' AND name LIKE %s"
            self.cursor.execute(query, (f"{prefix}%",))
        else:
            query = "SELECT * FROM public.aduanet WHERE status = 'staged'"
            self.cursor.execute(query)
        return self.cursor.fetchall()

    def zip_file_exists(self, name):
        query = "SELECT 1 FROM public.aduanet WHERE name = %s LIMIT 1"
        self.cursor.execute(query, (name,))
        return self.cursor.fetchone() is not None

    def close(self):
        if self.connection:
            self.cursor.close()
            self.connection.close()

# Cliente de MinIO (S3)
def create_s3_client():
    s3_endpoint = os.getenv("MINIO_ENDPOINT", "http://minio:9000")
    s3_client = boto3.client(
        's3',
        endpoint_url=s3_endpoint,
        aws_access_key_id=os.getenv("MINIO_ACCESS_KEY", "minioadmin"),
        aws_secret_access_key=os.getenv("MINIO_SECRET_KEY", "minioadmin"),
        region_name='us-east-1'
    )
    return s3_client

# Funciones para tareas de Airflow
def scrape_aduanet_website(**kwargs):
    ti = kwargs['ti']
    
    # Configurar Chrome para headless
    options = webdriver.ChromeOptions()
    options.binary_location = "/usr/bin/chromium"
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    
    aduanas_search_result_url = "http://www.aduanet.gob.pe/aduanas/informae/presentacion_bases_web.htm"
    
    # Iniciar selenium y obtener contenido de la página
    driver = webdriver.Chrome(options=options)
    driver.get(aduanas_search_result_url)
    
    # Esperar a que la página cargue
    import time
    time.sleep(10)
    
    content = driver.page_source
    driver.quit()
    
    # Parsear HTML
    html = BeautifulSoup(content, "html.parser")
    
    # Extraer archivos ZIP
    BASE_URL = "http://www.aduanet.gob.pe"
    zips = []
    zip_elements = html.find_all("a")
    
    for index, item in enumerate(zip_elements):
        try:
            zip_name = item.text.strip()
            zip_url = item["href"]
            
            # Corregir URL
            if zip_url.startswith("\\"):
                clean_path = zip_url.replace("\\", "/")
                if clean_path.startswith("/"):
                    clean_path = clean_path[1:]
                zip_url = f"{BASE_URL}/{clean_path}"
            elif not zip_url.startswith("http"):
                zip_url = f"{BASE_URL}/{zip_url}"
                
            if zip_name and zip_url:
                zips.append(
                    {
                        "id": index + 1,
                        "name": zip_name,
                        "url": zip_url,
                    }
                )
        except (AttributeError, KeyError):
            continue
    
    # Pasar resultado a la siguiente tarea
    ti.xcom_push(key='aduanet_zips', value=zips)
    return len(zips)

def download_to_staging(**kwargs):
    ti = kwargs['ti']
    zips = ti.xcom_pull(task_ids='scrape_aduanet_website', key='aduanet_zips')
    
    if not zips:
        print("No se encontraron archivos ZIP en Aduanet.")
        return 0
    
    # Filtrar por IDs (opcional)
    start_id = int(Variable.get("aduanet_start_id", default_var=1))
    end_id = int(Variable.get("aduanet_end_id", default_var=1000))
    selected_zips = [zip for zip in zips if start_id <= zip["id"] <= end_id]
    
    # Crear directorio de staging
    staging_dir = os.path.join(tempfile.gettempdir(), "aduanet_staging")
    if not os.path.exists(staging_dir):
        os.makedirs(staging_dir)
    
    # Inicializar repositorio
    repository = ZipsRepository()
    
    downloaded_count = 0
    
    # Procesar archivos seleccionados
    for aduanas_zip in selected_zips:
        staging_path = os.path.join(staging_dir, aduanas_zip["name"])
        
        if repository.save_zip_file(aduanas_zip["name"], aduanas_zip["url"], staging_path):
            try:
                print(f"Descargando: {aduanas_zip['url']}")
                response = requests.get(aduanas_zip["url"], timeout=30)
                response.raise_for_status()
                
                with open(staging_path, "wb") as f:
                    f.write(response.content)
                
                downloaded_count += 1
                print(f"Archivo {staging_path} descargado con éxito.")
            except Exception as e:
                print(f"Error al descargar {aduanas_zip['url']}: {e}")
                repository.update_zip_status(aduanas_zip["name"], "error")
        else:
            print(f"El archivo {aduanas_zip['name']} ya existe en la base de datos.")
    
    repository.close()
    return downloaded_count

def filter_and_upload_to_minio(**kwargs):
    prefix_filter = Variable.get("aduanet_prefix_filter", default_var="")
    bucket_name = Variable.get("minio_bucket_name", default_var="aduanet-data")
    
    # Inicializar MinIO
    s3_client = create_s3_client()
    
    # Crear bucket si no existe
    try:
        s3_client.create_bucket(Bucket=bucket_name)
        print(f"Bucket '{bucket_name}' creado con éxito")
    except s3_client.exceptions.BucketAlreadyOwnedByYou:
        print(f"Bucket '{bucket_name}' ya existe")
    
    # Obtener archivos en staging
    repository = ZipsRepository()
    staged_files = repository.get_staged_files(prefix_filter)
    
    uploaded_count = 0
    
    for file in staged_files:
        try:
            staging_path = file["staging_path"]
            file_name = file["name"]
            
            if os.path.exists(staging_path):
                # Ruta en MinIO
                minio_path = f"aduanet/{file_name}"
                
                # Subir a MinIO
                with open(staging_path, "rb") as f:
                    s3_client.upload_fileobj(f, bucket_name, minio_path)
                
                # Actualizar estado en la BD
                repository.update_zip_status(file_name, "uploaded", minio_path)
                uploaded_count += 1
                print(f"Archivo {file_name} cargado a MinIO: {minio_path}")
            else:
                print(f"Archivo no encontrado en staging: {staging_path}")
                repository.update_zip_status(file_name, "missing")
        except Exception as e:
            print(f"Error al procesar {file['name']}: {e}")
            repository.update_zip_status(file["name"], "error")
    
    repository.close()
    return uploaded_count

# Crear DAG
with DAG(
    'aduanet_etl_pipeline',
    default_args=default_args,
    description='ETL para datos de Aduanet con staging y carga a MinIO',
    schedule_interval=timedelta(days=1),
    start_date=datetime(2023, 1, 1),
    catchup=False,
) as dag:
    
    start = DummyOperator(task_id='start')
    
    # Tarea de scraping
    scrape_task = PythonOperator(
        task_id='scrape_aduanet_website',
        python_callable=scrape_aduanet_website,
        provide_context=True,
    )
    
    # Tarea de descarga a staging
    download_task = PythonOperator(
        task_id='download_to_staging',
        python_callable=download_to_staging,
        provide_context=True,
    )
    
    # Tarea de filtrado y carga a MinIO
    upload_task = PythonOperator(
        task_id='filter_and_upload_to_minio',
        python_callable=filter_and_upload_to_minio,
        provide_context=True,
    )
    
    end = DummyOperator(task_id='end')
    
    # Definir dependencias
    start >> scrape_task >> download_task >> upload_task >> end
