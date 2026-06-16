# Use official lightweight Python image
FROM python:3.9-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Set work directory
WORKDIR /app

# Install system utilities if needed (sqlite3 is already in slim python)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . /app/

# Expose local port for Flask
EXPOSE 5000

# Run API Server via CLI Orchestrator
CMD ["python", "main.py", "--serve"]
