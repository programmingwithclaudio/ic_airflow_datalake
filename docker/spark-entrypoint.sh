#!/bin/bash
set -e

# Constants
SPARK_MASTER_URL=${SPARK_MASTER_URL:-spark://spark-master:7077}
SPARK_WORKER_CORES=${SPARK_WORKER_CORES:-1}
SPARK_WORKER_MEMORY=${SPARK_WORKER_MEMORY:-1g}
SPARK_DRIVER_MEMORY=${SPARK_DRIVER_MEMORY:-1g}
SPARK_EXECUTOR_MEMORY=${SPARK_EXECUTOR_MEMORY:-1g}
SPARK_MASTER_HOST=${SPARK_MASTER_HOST:-spark-master}
SPARK_MASTER_PORT=${SPARK_MASTER_PORT:-7077}
SPARK_MASTER_WEBUI_PORT=${SPARK_MASTER_WEBUI_PORT:-8080}
SPARK_MODE=${SPARK_MODE:-master}

# Configure Spark for S3/MinIO
export SPARK_HOME=/opt/spark
export HADOOP_CONF_DIR=/opt/spark/conf
export HADOOP_HOME=/opt/spark

# Create hadoop configuration
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
</configuration>
EOF

echo "Configured core-site.xml for MinIO/S3 access"

# Start based on mode
case "$SPARK_MODE" in
    "master")
        echo "Starting Spark master"
        exec /opt/spark/sbin/start-master.sh --host $SPARK_MASTER_HOST --port $SPARK_MASTER_PORT --webui-port $SPARK_MASTER_WEBUI_PORT
        ;;
    "worker")
        echo "Starting Spark worker, connecting to: $SPARK_MASTER_URL"
        
        # Wait for master to be available
        MASTER_READY=false
        RETRIES=30
        while [ $RETRIES -gt 0 ] && [ "$MASTER_READY" = false ]; do
            if nc -z ${SPARK_MASTER_HOST} ${SPARK_MASTER_PORT}; then
                MASTER_READY=true
                echo "Spark master is ready"
            else
                echo "Waiting for Spark master... ($RETRIES retries left)"
                sleep 5
                RETRIES=$((RETRIES - 1))
            fi
        done

        if [ "$MASTER_READY" = true ]; then
            # In Spark 3.4.2, it's start-worker.sh not start-slave.sh
            exec /opt/spark/sbin/start-worker.sh \
                $SPARK_MASTER_URL \
                --cores $SPARK_WORKER_CORES \
                --memory $SPARK_WORKER_MEMORY
        else
            echo "Error: Spark master not available after retries"
            exit 1
        fi
        ;;
    *)
        echo "Unknown Spark mode: $SPARK_MODE. Supported modes: master, worker"
        exit 1
        ;;
esac