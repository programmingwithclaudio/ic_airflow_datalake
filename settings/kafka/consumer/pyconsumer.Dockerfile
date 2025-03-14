FROM python:3.9-slim

WORKDIR /app

COPY settings/consumer/requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY settings/consumer/consumer.py consumer.py

CMD ["python", "consumer.py"]

