#!/bin/bash
# Startup script for Railway deployment

# Use Railway's PORT environment variable, default to 8000
PORT=${PORT:-8000}

echo "Starting server on port $PORT..."
echo "DEBUG: DATABASE_URL is set: ${DATABASE_URL:0:30}..."
echo "DEBUG: APP_ENV=$APP_ENV"
echo "DEBUG: STRIPE_SECRET_KEY starts with: ${STRIPE_SECRET_KEY:0:10}..."
echo "DEBUG: STRIPE_PUBLISHABLE_KEY starts with: ${STRIPE_PUBLISHABLE_KEY:0:10}..."

# Run database initialization if needed
if [ "$RUN_INIT" = "true" ]; then
    echo "Running database initialization..."
    python init_db.py
    python migrate_add_moderation.py
fi

# Start the application
exec uvicorn app.main:app --host 0.0.0.0 --port $PORT
