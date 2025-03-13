# Imagen base de Airflow
FROM apache/airflow:2.3.4

# Establecemos usuario root para instalar dependencias
USER root

# Actualizamos y agregamos paquetes útiles
RUN apt-get update && apt-get install -y --no-install-recommends \
    vim curl nano wget git \
    && apt-get autoremove -yqq --purge \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Volvemos a usuario airflow
USER airflow

# Instalamos librerías necesarias
COPY requirements.txt /requirements.txt
RUN pip install --no-cache-dir -r /requirements.txt
