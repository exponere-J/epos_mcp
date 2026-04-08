FROM python:3.11-slim

WORKDIR /app

RUN pip install --no-cache-dir fastapi uvicorn pyyaml

COPY engine/ ./engine/
COPY error_detector.py .

EXPOSE 8106

CMD ["python", "error_detector.py"]

