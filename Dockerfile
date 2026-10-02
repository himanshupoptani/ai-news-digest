# ======================================================
# AI NEWS DIGEST — Railway / Docker Deployment
# ======================================================
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Create data directory for SQLite persistence
RUN mkdir -p /app/data

# Environment defaults (Railway overrides PORT automatically)
ENV HOST=0.0.0.0
ENV APP_MODE=live
ENV ENVIRONMENT=production
ENV DEBUG=False

# Use Python directly to read PORT — avoids shell CRLF issues on Windows
CMD ["python", "-c", "import os, uvicorn; uvicorn.run('backend.app.main:app', host='0.0.0.0', port=int(os.environ.get('PORT', 8000)), workers=1)"]
