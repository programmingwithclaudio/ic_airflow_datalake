

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

```bash
docker-compose down -v
docker-compose up --build -d
docker rm $(docker ps -aq)
docker volume rm $(docker volume ls -q)
docker system prune
docker system prune --volumes
docker-compose down --volumes --remove-orphans
docker volume prune -f
docker image prune -a -f
docker system prune -a --volumes -f
```


