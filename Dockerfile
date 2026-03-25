# Use a stable, slim version of Python
FROM python:3.11-slim

# Set environment variables to optimize Python for Docker
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set the working directory inside the container
WORKDIR /app

# Install system dependencies (needed for Pandas, ReportLab, etc.)
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements.txt separately for caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy all project files into the container
COPY . .

# Railway provides the PORT environment variable
# Port 7860 is used as a fallback if PORT is not set
ENV PORT 8080
EXPOSE 8080

# Shell-form CMD to support environment variable substitution ($PORT)
CMD uvicorn backend.main:app --host 0.0.0.0 --port $PORT
