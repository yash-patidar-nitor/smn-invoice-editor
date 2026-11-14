FROM python:3.12-slim

WORKDIR /app

# Install system dependencies required for build & headless browser
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency specifications
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browser and its Linux OS dependencies on the server
RUN playwright install --with-deps chromium

# Copy application source code
COPY . .

# Expose web application port
EXPOSE 5000

ENV PORT=5000
ENV PYTHONUNBUFFERED=1

CMD ["python", "server.py"]
