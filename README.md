

## 📌 **Flujo de Persistencia de Datos**
1. **MinIO almacena archivos en `./minio_data`**  
   - Se monta como volumen persistente en el contenedor `minio`.
2. **El cliente S3FS monta MinIO como un sistema de archivos** en `./s3fs_data`  
   - Cualquier archivo escrito en `/mnt/s3fs` se almacenará en MinIO.  
3. **Python interactúa con MinIO vía SDK**  
   - Puede leer, escribir y listar archivos en MinIO.  
4. **Todos los datos persisten después de un reinicio**  
   - Gracias a los volúmenes montados, ni los archivos ni la configuración se pierden.

---

## 🚀 **Cómo Ejecutar**
1️⃣ Clonar el repositorio o copiar los archivos a un directorio.  
2️⃣ Crear el archivo `.env` con las credenciales.  
3️⃣ Ejecutar:  
```sh
docker-compose up -d  # Levanta los contenedores en segundo plano
```
4️⃣ Verificar logs de cada servicio con:  
```sh
docker logs -f minio
docker logs -f s3fs
docker logs -f python-client
```
5️⃣ Acceder a la consola web de MinIO:  
   - URL: [http://localhost:9090](http://localhost:9090)  
   - Usuario: `admin`  
   - Contraseña: `adminpassword`  

---
# https://github.com/AhmetFurkanDEMIR/airflow-spark-kafka-example/blob/main/docker/airflow/start-airflow.sh
```bash
docker-compose down -v
docker-compose up --build -d
docker stop $(docker ps -q)

docker rm $(docker ps -aq)
docker volume rm $(docker volume ls -q)
docker network prune
docker system prune
docker system prune --volumes
docker-compose down --volumes --remove-orphans
docker volume prune -f
docker image prune -a -f
docker system prune -a --volumes -f
#check airflow
docker logs airflow_init
docker exec -it airflow_webserver airflow users create --role Admin --username admin --password admin --firstname Admin --lastname Admin --email admin@example.com
docker exec -it airflow_webserver airflow db check


#

docker-compose down --rmi all
docker-compose build --no-cache
docker-compose up


#

docker-compose down
docker-compose build spark-master
docker-compose up -d

#
docker-compose stop spark-master
docker-compose rm -f spark-master
docker-compose up -d spark-master --no-deps --build

#
docker-compose stop spark-worker
docker stop 62e7996b9bab
docker-compose rm -f spark-worker
docker rm 62e7996b9bab
docker-compose up -d spark-worker

#
docker-compose logs -f

#
docker-compose up -d zookeeper kafka postgres redis airflow minio
docker-compose up -d spark-master spark-worker-1 python-producer python-consumer

#
bash project-structure.sh

docker-compose up -d postgres redis minio zookeeper kafka

docker-compose up -d airflow-init airflow-webserver airflow-scheduler

docker-compose up -d spark-master spark-worker

#
visudo
%wheel ALL=(ALL:ALL) ALL
useradd -m -s /bin/bash si
passwd si

```
[http://localhost:9001/login](http://localhost:9001/login)
[http://localhost:8080/](http://localhost:8080/)
---
```bash
sudo pacman -S pybind11
pkg-config --modversion pybind11
# escribir directamente
docker exec -it spark-master /bin/bash
sudo chmod -R 777 dags plugins spark data
mkdir -p spark data/input data/output data/checkpoint
# escribir en local
pip install pyspark
from pyspark.sql import SparkSession

spark = SparkSession.builder \
    .master("spark://localhost:7077") \
    .appName("MiAplicacion") \
    .getOrCreate()
spark-submit --master spark://localhost:7077 docker/main.py

```
```bash
docker exec -it --user root airflow_webserver bash
chmod -R 777 /opt/airflow/data
sudo chmod -R 777 ./data
mkdir -p spark data/input data/output data/checkpoint

chmod -R 777 /opt/airflow/data
sudo chmod -R 777 input output checkpoint
```

```bash
docker exec -it postgres_airflow bash
psql -U airflow -d airflow
\dt

CREATE TABLE my_new_table (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

\d 

docker exec -it spark-master bash
docker-compose build spark-master spark-worker
```
