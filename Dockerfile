FROM apache/airflow:2.7.3

USER root
RUN apt-get update && apt-get install -y chromium chromium-driver
USER airflow