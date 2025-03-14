FROM apache/airflow:2.7.3

USER root
RUN apt-get update && apt-get install -y --no-install-recommends \
    vim curl nano wget git procps openjdk-11-jdk \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Crear directorios necesarios y ajustar permisos
RUN mkdir -p /opt/airflow/data/input /opt/airflow/data/output /opt/airflow/data/checkpoint && \
    chown -R 50000:50000 /opt/airflow/data && \
    chmod -R 777 /opt/airflow/data

# Copiar el requirements.txt y instalar dependencias (incluyendo las de Kafka)
USER airflow
COPY requirements.txt /requirements.txt
RUN pip install --no-cache-dir -r /requirements.txt && \
    pip install apache-airflow-providers-apache-spark==4.1.5 && \
    pip install apache-airflow-providers-openlineage==1.8.0 && \
    pip install apache-airflow-providers-apache-kafka && \
    pip install kafka-python

# Sobrescribir el airflow.cfg por defecto con la configuración personalizada
COPY airflow.cfg $AIRFLOW_HOME/airflow.cfg

# Copiar el script de inicio y asignar permisos de ejecución
COPY start-airflow.sh $AIRFLOW_HOME/start-airflow.sh
RUN chmod +x $AIRFLOW_HOME/start-airflow.sh

# Crear la carpeta dags (si no existe) y exponer el puerto 8080
RUN mkdir -p $AIRFLOW_HOME/dags
EXPOSE 8080

# Usar el script de inicio como entrypoint
CMD [ "/opt/airflow/start-airflow.sh" ]