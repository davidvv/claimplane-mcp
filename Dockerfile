FROM python:3.11-slim

# OCI Image Labels
LABEL org.opencontainers.image.source="https://github.com/davidvencovsky/easyAirClaim"
LABEL org.opencontainers.image.description="ClaimPlane - Flight compensation claim management system"
LABEL org.opencontainers.image.version="1.0.0"
LABEL org.opencontainers.image.authors="David Vences"

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    POETRY_NO_INTERACTION=1 \
    POETRY_VENV_IN_PROJECT=1 \
    POETRY_CACHE_DIR=/tmp/poetry_cache

# Set work directory
WORKDIR /app

# Create non-root user FIRST (before copying files)
RUN addgroup --gid 1000 appgroup && \
    adduser --disabled-password --gecos '' --uid 1000 --gid 1000 appuser

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    libmagic1 \
    file \
    # Barcode/QR code reading (Phase 7.5)
    libzbar0 \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project with correct ownership (much faster than chown -R)
COPY --chown=appuser:appgroup . .

# Switch to non-root user
USER appuser

# Health check for container orchestration
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

# Expose port
EXPOSE 8000

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
