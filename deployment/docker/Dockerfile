FROM python:3.11-slim

WORKDIR /app

# Install system dependencies including gcc for psutil
RUN apt-get update && apt-get install -y \
    curl \
    postgresql-client \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

ARG CACHE_BUST=1

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Make startup script executable
RUN chmod +x startup.sh

# Expose port
EXPOSE 8000

# Run the startup script
CMD ["./startup.sh"]
