# Week 3 CSV Analytics Container - Secure Multi-stage Build
# Combines Week 1 + Week 2 functionality with MCP server and HTTP API

# ============================================================================
# Build Stage - Install dependencies and prepare application
# ============================================================================
FROM python:3.13-alpine AS builder

# Install build dependencies and uv in single layer
RUN apk add --no-cache \
        gcc \
        musl-dev \
        libffi-dev \
        openssl-dev \
        python3-dev \
        build-base && \
    pip install --no-cache-dir uv

# Set working directory
WORKDIR /build

# Copy project files for dependency resolution
COPY pyproject.toml ./
COPY src/ ./src/

# Install project and dependencies using uv
RUN uv venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN uv pip install --no-cache-dir -e .

# ============================================================================
# Runtime Stage - Minimal production image
# ============================================================================
FROM python:3.13-alpine AS runtime

# Install minimal runtime dependencies
RUN apk add --no-cache \
    libstdc++ \
    libgcc \
    libgomp \
    && rm -rf /var/cache/apk/*

# Create non-root user and setup environment in single layer
RUN addgroup -g 1001 -S appgroup && \
    adduser -u 1001 -S appuser -G appgroup && \
    mkdir -p /app/charts /app/logs && \
    chown -R appuser:appgroup /app

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Set working directory
WORKDIR /app

# Copy application code and data with proper ownership
COPY --chown=appuser:appgroup src/ ./src/
COPY --chown=appuser:appgroup data/ ./data/

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')" || exit 1

# Set environment variables
ENV PYTHONPATH=/app/src
ENV HOST=0.0.0.0
ENV PORT=8000
ENV DEBUG=false

# Run the FastAPI application
CMD ["python", "src/main.py"]
