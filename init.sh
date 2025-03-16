#!/bin/bash

# Variables de configuración
CONTAINER_ID="0383c41e3bcb "  # Reemplaza con el nombre o ID de tu contenedor
PG_USER="airflow"  # Usuario por defecto en PostgreSQL
PG_PASSWORD="airflow"  # Reemplaza con la contraseña de tu usuario postgres
DB_NAME="aduanasdb"  # Nombre de la base de datos a crear

# Comando para crear la base de datos
docker exec -e PGPASSWORD=$PG_PASSWORD -it $CONTAINER_ID \
  psql -U $PG_USER -c "CREATE DATABASE $DB_NAME;"

# Verificar el resultado del comando
if [ $? -eq 0 ]; then
  echo "Base de datos '$DB_NAME' creada exitosamente en el contenedor $CONTAINER_ID."
else
  echo "Error al crear la base de datos '$DB_NAME'."
fi