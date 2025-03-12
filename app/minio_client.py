#!/usr/bin/env python3
import os
import time
from minio import Minio
from minio.error import S3Error
from datetime import datetime

def main():
    """
    Cliente MinIO para operaciones básicas de almacenamiento de objetos
    """
    # Cargar credenciales desde variables de entorno
    minio_server = os.getenv("MINIO_SERVER").replace("http://", "")
    if ":" not in minio_server:
        minio_server = f"{minio_server}:9000"
    
    access_key = os.getenv("MINIO_ACCESS_KEY")
    secret_key = os.getenv("MINIO_SECRET_KEY")
    bucket_name = os.getenv("MINIO_BUCKET_NAME")
    
    print(f"🔌 Conectando a MinIO en {minio_server}...")
    
    # Crear cliente MinIO
    client = Minio(
        minio_server,
        access_key=access_key,
        secret_key=secret_key,
        secure=False  # Cambiar a True si se utiliza HTTPS
    )
    
    # Asegurarse de que el bucket existe
    try:
        if not client.bucket_exists(bucket_name):
            client.make_bucket(bucket_name)
            print(f"✅ Bucket '{bucket_name}' creado.")
        else:
            print(f"📂 Bucket '{bucket_name}' ya existe.")
    except S3Error as err:
        print(f"❌ Error al verificar/crear bucket: {err}")
        return
    
    # Listar todos los buckets
    try:
        print("\n📋 Lista de Buckets:")
        for bucket in client.list_buckets():
            print(f" - {bucket.name} (creado: {bucket.creation_date})")
    except S3Error as err:
        print(f"❌ Error al listar buckets: {err}")
    
    # Crear un archivo de ejemplo
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    file_path = f"/tmp/example-{timestamp}.txt"
    with open(file_path, "w") as f:
        f.write(f"¡Hola, MinIO! - Archivo creado el {datetime.now().isoformat()}")
    
    # Subir el archivo
    try:
        object_name = f"example-{timestamp}.txt"
        client.fput_object(
            bucket_name, 
            object_name, 
            file_path,
            metadata={"Created-By": "Python-Client", "Timestamp": timestamp}
        )
        print(f"\n📤 Archivo '{object_name}' subido con éxito.")
    except S3Error as err:
        print(f"❌ Error al subir archivo: {err}")
    
    # Listar objetos en el bucket
    try:
        print(f"\n📂 Archivos en el bucket '{bucket_name}':")
        objects = list(client.list_objects(bucket_name, recursive=True))
        
        if not objects:
            print(" - No hay archivos en el bucket")
        else:
            for obj in objects:
                size_kb = obj.size / 1024
                print(f" - {obj.object_name} ({size_kb:.2f} KB, modificado: {obj.last_modified})")
        
        # Obtener y mostrar URL de acceso público para el último archivo subido
        if objects:
            url = client.presigned_get_object(bucket_name, object_name)
            print(f"\n🔗 URL para acceder al archivo '{object_name}':")
            print(f" - {url}")
    except S3Error as err:
        print(f"❌ Error al listar archivos: {err}")

if __name__ == "__main__":
    # Esperar un poco para asegurar que MinIO esté completamente inicializado
    time.sleep(2)
    main()