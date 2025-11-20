FROM python:3.11-slim

WORKDIR /app

# Install dependencies
RUN pip install --no-cache-dir requests

# Copy agent code
COPY compliance_agent.py .

# Run agent
CMD ["python", "-u", "compliance_agent.py"]
