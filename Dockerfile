# ==============================================================================
# Production Dockerfile for Wanderlust AI Trip Planner
# Multi-stage/lightweight build running FastAPI + CrewAI
# ==============================================================================

FROM python:3.12-slim

# Prevent python from buffering stdout and writing .pyc files
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000

WORKDIR /app

# Install minimal build tools required for native C extensions
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency manifests first for optimal Docker layer caching
COPY requirements.txt pyproject.toml ./

# Install python dependencies first for optimal Docker layer caching
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code and static assets
COPY src/ ./src/
COPY output/ ./output/

# Install the project package now that src/ exists
RUN pip install --no-cache-dir -e .

# Ensure output directory exists and is writable
RUN mkdir -p output

# Expose server port
EXPOSE 8000

# Run uvicorn server binding to 0.0.0.0 and dynamic $PORT
CMD ["sh", "-c", "uvicorn trip_planner.server:app --host 0.0.0.0 --port ${PORT:-8000}"]
