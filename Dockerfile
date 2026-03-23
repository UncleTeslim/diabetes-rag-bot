FROM python:3.11-slim

WORKDIR /app

COPY . /app

RUN pip install --no-cache-dir -r requirements.txt

# Railway injects $PORT at runtime (default 10000)
EXPOSE 10000

# Strip Windows CRLF line endings (file was authored on Windows) then make executable
RUN sed -i 's/\r$//' start.sh && chmod +x start.sh

# start.sh: (1) verifies/builds the Pinecone index, (2) launches gunicorn
CMD ["bash", "start.sh"]
