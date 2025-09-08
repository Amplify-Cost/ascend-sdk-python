# Use Python 3.11 as base - this gives us a Linux environment with Python ready
FROM python:3.11-slim

# Set environment variables that optimize Python for containers
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Install system dependencies that your app might need
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create a working directory inside the container
WORKDIR /app

# Copy requirements first (Docker optimization - if requirements don't change, this step is cached)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy your application code
COPY . .

# Create a non-root user for security (enterprise standard)
RUN groupadd -r appuser && useradd -r -g appuser appuser
RUN chown -R appuser:appuser /app
USER appuser

# Health check - tells AWS if your app is working properly
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Expose the port your FastAPI app runs on
EXPOSE 8000

# Command to start your application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
# Build timestamp: Mon Sep  8 09:52:27 EDT 2025
# Docker cache bust: 1757349207
