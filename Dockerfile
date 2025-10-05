# docker/Dockerfile

FROM python:3.12-slim

# Install build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    libmagic1 \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Install Python dependencies
COPY requirements-minimal.txt .
RUN pip install --upgrade pip
RUN pip install -r requirements-minimal.txt

# Copy application files
COPY app /app
COPY src /src

# Set PYTHONPATH
ENV PYTHONPATH=/app

# Expose port (default 8000)
EXPOSE 8000

# Set default environment variables (these should be overridden via Docker Compose or runtime)
ENV PORT=8000 \
    HOST=0.0.0.0 \
    LOG_LEVEL=10

# Mountable directories
VOLUME ["/app/data", "/app/frontend"]

# Start application
CMD ["bash", "start_docker.sh"]
