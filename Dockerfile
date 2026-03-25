# Use a stable, slim version of Python
FROM python:3.11-slim

# Set environment variables to optimize Python for Docker
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set the working directory inside the container
WORKDIR /app

# Install system dependencies
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

# Railway defaults to port 8080 which is our standard here
EXPOSE 8080

# Hardcoded port 8080 to avoid any dynamic port substitution errors ($PORT string issues)
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8080"]
