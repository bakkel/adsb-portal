FROM python:3.12-slim

WORKDIR /app

COPY server.py .
COPY static/ static/

ENV PYTHONUNBUFFERED=1 \
    DB_PATH=/data/fr24portal.db

EXPOSE 8081

CMD ["python3", "server.py"]
