#!/bin/bash
set -e

# Variables de entorno con valores por defecto
SPARK_MASTER_URL=${SPARK_MASTER_URL:-spark://spark-master:7077}
SPARK_WORKER_CORES=${SPARK_WORKER_CORES:-1}
SPARK_WORKER_MEMORY=${SPARK_WORKER_MEMORY:-1g}
SPARK_DRIVER_MEMORY=${SPARK_DRIVER_MEMORY:-1g}
SPARK_EXECUTOR_MEMORY=${SPARK_EXECUTOR_MEMORY:-1g}
SPARK_WORKER_WEBUI_PORT=${SPARK_WORKER_WEBUI_PORT:-8081}
SPARK_MODE=${SPARK_MODE:-worker}

# Configurar Spark para S3/MinIO
export SPARK_HOME=/opt/spark
export HADOOP_CONF_DIR=/opt/spark/conf
export HADOOP_HOME=/opt/spark

# Crear el directorio de configuración si no existe
mkdir -p $HADOOP_CONF_DIR

# Crear la configuración de Hadoop (core-site.xml)
cat > $HADOOP_CONF_DIR/core-site.xml <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<?xml-stylesheet type="text/xsl" href="configuration.xsl"?>
<configuration>
    <property>
        <name>fs.s3a.endpoint</name>
        <value>http://minio:9000</value>
    </property>
    <property>
        <name>fs.s3a.access.key</name>
        <value>minioadmin</value>
    </property>
    <property>
        <name>fs.s3a.secret.key</name>
        <value>minioadmin</value>
    </property>
    <property>
        <name>fs.s3a.path.style.access</name>
        <value>true</value>
    </property>
    <property>
        <name>fs.s3a.impl</name>
        <value>org.apache.hadoop.fs.s3a.S3AFileSystem</value>
    </property>
    <property>
        <name>fs.s3a.connection.ssl.enabled</name>
        <value>false</value>
    </property>
</configuration>
EOF

echo "Configured core-site.xml for MinIO/S3 access"

# Arrancar según el modo especificado
if [ "$SPARK_MODE" = "worker" ]; then
    echo "Starting Spark worker..."
    # Verificar que el master esté disponible antes de iniciar el worker
    until nc -z spark-master 7077; do
        echo "Waiting for Spark Master to be available..."
        sleep 2
    done
    
    /opt/spark/sbin/start-worker.sh $SPARK_MASTER_URL \
        --webui-port $SPARK_WORKER_WEBUI_PORT \
        --cores $SPARK_WORKER_CORES \
        --memory $SPARK_WORKER_MEMORY
    
    # Mantener el contenedor en ejecución
    tail -f /opt/spark/logs/spark--org.apache.spark.deploy.worker.Worker-*.out
fi