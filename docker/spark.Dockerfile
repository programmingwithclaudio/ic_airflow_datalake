FROM apache/spark:3.4.2

USER root
RUN apt-get update && apt-get install -y curl netcat-traditional && apt-get clean && rm -rf /var/lib/apt/lists/*

# Descargar los JARs necesarios para la integración S3/MinIO
RUN curl --location https://repo1.maven.org/maven2/org/apache/hadoop/hadoop-aws/3.3.4/hadoop-aws-3.3.4.jar --output /opt/spark/jars/hadoop-aws-3.3.4.jar && \
    curl --location https://repo1.maven.org/maven2/com/amazonaws/aws-java-sdk-bundle/1.12.262/aws-java-sdk-bundle-1.12.262.jar --output /opt/spark/jars/aws-java-sdk-bundle-1.12.262.jar

# Copiar el entrypoint script y asignar la propiedad a 'spark'
COPY --chown=spark:spark docker/spark-entrypoint.sh /opt/entrypoint.sh
# Cambiar permisos (ejecutado como root para asegurarnos de que se puede)
RUN chmod +x /opt/entrypoint.sh

# Cambiar a usuario spark
USER spark

ENTRYPOINT ["/opt/entrypoint.sh"]