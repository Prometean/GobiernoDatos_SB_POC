# docker/ingest.Dockerfile

FROM python:3.10-slim

WORKDIR /app

COPY ingest/ ./ingest/

RUN pip install --no-cache-dir pandas requests

CMD ["python", "ingest/alpha_ingest.py"]
