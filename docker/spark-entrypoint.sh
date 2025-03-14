#!/bin/bash
set -e

# Variables de entorno con valores por defecto
SPARK_MASTER_URL=${SPARK_MASTER_URL:-spark://spark-master:7077}
SPARK_WORKER_CORES=${SPARK_WORKER_CORES:-1}
SPARK_WORKER_MEMORY=${SPARK_WORKER_MEMORY:-1g}
SPARK_DRIVER_MEMORY=${SPARK_DRIVER_MEMORY:-1g}
SPARK_EXECUTOR_MEMORY=${SPARK_EXECUTOR_MEMORY:-1g}
SPARK_MASTER_HOST=${SPARK_MASTER_HOST:-spark-master}
SPARK_MASTER_PORT=${SPARK_MASTER_PORT:-7077}
SPARK_MASTER_WEBUI_PORT=${SPARK_MASTER_WEBUI_PORT:-8080}
SPARK_MODE=${SPARK_MODE:-master}

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
        <value>Nt1BR5NXbgVh4AqOA7BX</value>
    </property>
    <property>
        <name>fs.s3a.secret.key</name>
        <value>weKIbuVXkywzHNjEmz04C8KarTjJr7jUTebczC4j</value>
    </property>
    <property>
        <name>fs.s3a.path.style.access</name>
        <value>true</value>
    </property>
    <property>
        <name>fs.s3a.impl</name>
        <value>org.apache.hadoop.fs.s3a.S3AFileSystem</value>
    </property>
</configuration>
EOF

echo "Configured core-site.xml for MinIO/S3 access"

# Arrancar según el modo especificado
# Reemplaza la verificación de disponibilidad del master con este código
if [ "$SPARK_MODE" = "master" ]; then
    echo "Starting Spark master..."
    # Con estas líneas:
    /opt/spark/sbin/start-master.sh --host $SPARK_MASTER_HOST --port $SPARK_MASTER_PORT --webui-port $SPARK_MASTER_WEBUI_PORT
    # Mantener el contenedor en ejecución
    tail -f /opt/spark/logs/spark--org.apache.spark.deploy.master.Master-1-*.out
    # Mantener el script en ejecución
    tail -f /opt/spark/logs/spark--org.apache.spark.deploy.worker.Worker-*.out
fi

