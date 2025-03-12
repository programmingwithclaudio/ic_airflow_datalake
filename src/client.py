from minio import Minio
from minio.error import S3Error
from datetime import datetime

# Conectar con MinIO
client = Minio(
    "127.0.0.1:9000",
    access_key="Nt1BR5NXbgVh4AqOA7BX",
    secret_key="weKIbuVXkywzHNjEmz04C8KarTjJr7jUTebczC4j",
    secure=False
)

# Nombre del bucket
bucket_name = "my-test-bucket-iv"

# Creamos un nuevo bucket si no existe
found = client.bucket_exists(bucket_name)
if not found:
    client.make_bucket(bucket_name)
    print(f"✅ Bucket '{bucket_name}' creado.")
else:
    print(f"⚠️ Bucket '{bucket_name}' ya existe.")

# Listamos todos los buckets
print("\nBuckets:")
buckets = client.list_buckets()
for bucket in buckets:
    print(f"- {bucket.name} (Creado el {bucket.creation_date})")

# Archivo a subir
file_path = "src/example.txt"  # Ajusta la ruta si es necesario
object_name = "example.txt"  # Nombre del archivo en MinIO

# Generar timestamp
timestamp = datetime.now().isoformat()

try:
    # Subir archivo
    client.fput_object(
        bucket_name, 
        object_name, 
        file_path,
        metadata={"Created-By": "Python-Client", "Timestamp": timestamp}
    )
    print(f"\n📤 Archivo '{object_name}' subido con éxito.")
except S3Error as err:
    print(f"❌ Error al subir archivo: {err}")

# Listamos los objetos del bucket
print(f"\nObjetos en '{bucket_name}':")
objects = client.list_objects(bucket_name)
for obj in objects:
    print(f"- {obj.object_name} (Tamaño: {obj.size} bytes)")
