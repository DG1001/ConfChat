# PresentAI - Production Dockerfile
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (for better caching)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create instance directory for SQLite database
RUN mkdir -p instance

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash appuser && \
    chown -R appuser:appuser /app
USER appuser

# Environment variables with defaults
ENV FLASK_ENV=production
ENV PORT=5000
ENV HOST=0.0.0.0

# Expose port (can be overridden)
EXPOSE $PORT

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:$PORT/ || exit 1

# Start command using gunicorn
CMD python -m gunicorn \
    --workers 1 \
    --threads 4 \
    --bind $HOST:$PORT \
    --timeout 60 \
    --keep-alive 2 \
    --log-level info \
    --access-logfile - \
    --error-logfile - \
    app:app