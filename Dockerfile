# ======================================================
# AI NEWS DIGEST — Railway / Docker Deployment
# ======================================================
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Create data directory for SQLite persistence
RUN mkdir -p /app/data

# Default environment variables (overridden by Railway env vars)
ENV HOST=0.0.0.0
ENV PORT=8000
ENV APP_MODE=live
ENV ENVIRONMENT=production
ENV DEBUG=False

EXPOSE 8000

CMD ["sh", "-c", "uvicorn backend.app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
