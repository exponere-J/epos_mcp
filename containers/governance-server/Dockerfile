FROM python:3.11-slim
WORKDIR /app
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY server.py .
RUN mkdir -p /app/logs /app/context_vault
EXPOSE 8101
HEALTHCHECK --interval=30s --timeout=3s CMD curl -f http://localhost:8101/health || exit 1
CMD ["python", "server.py"]
