FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1
WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libglib2.0-0 libgl1 libgomp1 && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

RUN mkdir -p /app/data && chmod 777 /app/data

# Memory optimization defaults for Render Free
ENV MODEL_NAME=buffalo_s \
    ONNX_PROVIDER=CPUExecutionProvider \
    MEMORY_OPTIMIZATION=true

EXPOSE 8000
# Run uvicorn with a single worker to avoid memory duplication
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
