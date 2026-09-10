# Sound Pesa API Dockerfile
FROM python:3.11-slim as base

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app

# Development stage
FROM base as development

# Install development dependencies
RUN pip install --upgrade pip

# Copy requirements first for better caching
COPY packages/api/requirements.txt /app/requirements.txt
RUN pip install -r requirements.txt

# Copy application code
COPY packages/api /app/api
COPY packages/shared /app/shared

# Create necessary directories
RUN mkdir -p /app/api/staticfiles /app/api/media /app/logs

# Expose port
EXPOSE 8000

# Default command for development
CMD ["python", "api/manage.py", "runserver", "0.0.0.0:8000"]

# Production stage
FROM base as production

# Install production dependencies only
RUN pip install --upgrade pip gunicorn

# Copy requirements and install
COPY packages/api/requirements.txt /app/requirements.txt
RUN pip install -r requirements.txt --no-dev

# Copy application code
COPY packages/api /app/api
COPY packages/shared /app/shared

# Create non-root user
RUN groupadd -r soundpesa && useradd -r -g soundpesa soundpesa

# Create necessary directories and set permissions
RUN mkdir -p /app/api/staticfiles /app/api/media /app/logs && \
    chown -R soundpesa:soundpesa /app

# Switch to non-root user
USER soundpesa

# Collect static files
RUN python api/manage.py collectstatic --noinput

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8000/health/ || exit 1

# Production command
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "4", "--timeout", "120", "api.wsgi:application"]