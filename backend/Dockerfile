# =============================================================================
# Backend Development Dockerfile - Optimized for fast rebuilds
# =============================================================================
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies (including dev tools)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    make \
    libpq-dev \
    nmap \
    curl \
    dnsutils \
    iputils-ping \
    net-tools \
    vim \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies first (better caching)
COPY requirements/ ./requirements/
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements/base.txt \
    && pip install --no-cache-dir watchfiles  # For better file watching

# Create directories for data
RUN mkdir -p data/logs data/uploads data/reports

# Create non-root user
RUN useradd --create-home --shell /bin/bash --uid 1000 app \
    && chown -R app:app /app

# Note: Application code is mounted as volume in dev mode
# Switch to non-root user
USER app

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Development startup with hot reload
CMD ["uvicorn", "app.main:app", \
    "--host", "0.0.0.0", \
    "--port", "8000", \
    "--reload", \
    "--reload-include", "*.py", \
    "--reload-include", "*.yaml", \
    "--reload-include", "*.yml", \
    "--log-level", "debug"]