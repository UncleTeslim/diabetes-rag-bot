FROM python:3.11-slim

WORKDIR /app

COPY . /app

RUN pip install --no-cache-dir -r requirements.txt

# Render injects $PORT at runtime (default 10000); expose it so Render detects it immediately
EXPOSE 10000

# gthread workers handle concurrent SSE streams without monkey-patching
# Shell form so $PORT (injected by Render) is expanded at runtime
CMD gunicorn --worker-class gthread --threads 4 --timeout 120 --bind 0.0.0.0:$PORT app:app
