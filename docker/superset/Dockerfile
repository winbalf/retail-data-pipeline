FROM apache/superset:latest

# Install required packages for PostgreSQL support and CORS
# Superset uses a virtual environment at /app/.venv
USER root
# Install PostgreSQL client tools for database connection checks
RUN apt-get update && \
  apt-get install -y --no-install-recommends postgresql-client && \
  apt-get clean && \
  rm -rf /var/lib/apt/lists/*
# Install Python packages
RUN /usr/local/bin/pip install --target=/app/.venv/lib/python3.10/site-packages --no-cache-dir \
  psycopg2-binary>=2.9.9 \
  flask-cors>=4.0.0
USER superset

