from pyspark.sql import SparkSession
from pyspark.sql.functions import window, avg
from pyspark.sql.types import StructType, StructField, TimestampType, DoubleType

def main():
    # Inicializamos la sesión Spark y configuramos las propiedades para S3 (MinIO)
    spark = SparkSession.builder \
        .appName("StreamingJob") \
        .config("spark.hadoop.fs.s3a.endpoint", "http://minio:9000") \
        .config("spark.hadoop.fs.s3a.access.key", "minioadmin") \
        .config("spark.hadoop.fs.s3a.secret.key", "minioadmin") \
        .config("spark.hadoop.fs.s3a.path.style.access", "true") \
        .getOrCreate()
    
    spark.sparkContext.setLogLevel("WARN")
    print("====== Spark Streaming Job Started ======")
    
    # Definir esquema para los datos de entrada
    schema = StructType([
        StructField("timestamp", TimestampType(), True),
        StructField("value", DoubleType(), True)
    ])
    
    try:
        # Lectura en streaming desde MinIO vía s3a
        streaming_df = spark.readStream.format("csv") \
            .schema(schema) \
            .option("header", "true") \
            .load("s3a://test/")
        
        # Procesar datos: agregación con watermark y ventana de 1 minuto
        processed_df = streaming_df.withWatermark("timestamp", "1 minute") \
            .groupBy(window("timestamp", "1 minute")) \
            .agg(avg("value").alias("avg_value"))
            
        # Escribir resultados en CSV usando outputMode "append"
        query = processed_df.writeStream.format("csv") \
            .option("path", "/opt/airflow/data/output") \
            .option("checkpointLocation", "/opt/airflow/data/checkpoint") \
            .outputMode("append") \
            .start()
            
        query.awaitTermination(timeout=60)  # Timeout de 60 segundos para pruebas
        print("====== Spark Streaming Job Completed ======")
        
    except Exception as e:
        print(f"Error in Spark Streaming job: {e}")
        raise e
    finally:
        spark.stop()

if __name__ == "__main__":
    main()
