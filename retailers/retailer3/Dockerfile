FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip install --no-cache-dir flask psycopg2-binary

# Copy application code
COPY api/ ./api/
COPY database/ ./database/

# Expose port
EXPOSE 5003

# Run the API
CMD ["python", "api/app.py"]

