FROM python:3.11-slim

WORKDIR /app

# Install dependencies
RUN pip install --no-cache-dir \
    fastapi==0.104.1 \
    uvicorn==0.24.0 \
    psycopg2-binary==2.9.9 \
    pydantic==2.5.0

# Copy server code
COPY server.py .

# Expose port
EXPOSE 8100

# Health check
HEALTHCHECK --interval=10s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8100/health')"

# Start server
CMD ["python", "server.py"]

