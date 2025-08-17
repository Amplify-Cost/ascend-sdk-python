FROM python:3.11-slim

WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port (Railway will provide PORT env variable)
EXPOSE 8000

# Use Python directly instead of shell script to avoid PORT variable issues
CMD python -c "import os; import uvicorn; uvicorn.run('main:app', host='0.0.0.0', port=int(os.environ.get('PORT', 8000)))"
