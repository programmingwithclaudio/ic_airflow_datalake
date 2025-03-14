FROM python:3.9-slim

WORKDIR /app

COPY settings/producer/requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY settings/producer/producer.py producer.py

CMD ["python", "producer.py"]
