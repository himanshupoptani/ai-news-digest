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

# Environment defaults
ENV HOST=0.0.0.0
ENV APP_MODE=live
ENV ENVIRONMENT=production
ENV DEBUG=False

CMD ["python", "app.py"]
