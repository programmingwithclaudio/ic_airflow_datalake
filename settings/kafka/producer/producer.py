from kafka import KafkaProducer
import json
import time

producer = KafkaProducer(
    bootstrap_servers="kafka:9092",
    value_serializer=lambda v: json.dumps(v).encode("utf-8"),
)

while True:
    data = {"message": "Hola desde Python Producer"}
    producer.send("test-topic", value=data)
    print("Mensaje enviado:", data)
    time.sleep(5)
