# Use Python 3.11 slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies (including git for version info)
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY backend/requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY backend/ .

# Copy .git directory to extract commit hash
COPY .git .git

# Create version file with git commit hash
RUN git rev-parse --short HEAD > version.txt && rm -rf .git

# Make start script executable
RUN chmod +x start.sh

# Expose port (Railway uses 8080 by default)
EXPOSE 8080

# Run the application using start script
CMD ["./start.sh"]
