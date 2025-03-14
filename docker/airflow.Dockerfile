FROM apache/airflow:2.7.3

USER root
# Install necessary system packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    vim curl nano wget git procps openjdk-11-jdk \
    && apt-get autoremove -yqq --purge \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Create directories for data and adjust permissions
RUN mkdir -p /opt/airflow/data/input /opt/airflow/data/output /opt/airflow/data/checkpoint && \
    chown -R 50000:50000 /opt/airflow/data && \
    chmod -R 777 /opt/airflow/data

# Install Python dependencies and compatible Airflow providers
USER airflow
COPY docker/requirements.txt /requirements.txt
RUN pip install --no-cache-dir -r /requirements.txt && \
    pip install apache-airflow-providers-apache-spark==4.1.5 && \
    pip install apache-airflow-providers-openlineage==1.8.0