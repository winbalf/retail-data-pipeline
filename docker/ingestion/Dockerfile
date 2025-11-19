FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY ingestion/ ./ingestion/
COPY shared/ ./shared/

# Set Python path
ENV PYTHONPATH=/app

# Default command (can be overridden)
CMD ["python", "-m", "ingestion.main"]

