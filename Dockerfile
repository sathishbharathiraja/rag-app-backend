FROM python:3.11-slim

WORKDIR /app

# Install build dependencies for asyncpg and pgvector
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Command to run the application is defined in docker-compose.yml
