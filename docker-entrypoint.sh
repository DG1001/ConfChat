#!/bin/bash
set -e

echo "Starting PresentAI..."

# Ensure instance directory exists
mkdir -p instance

# Initialize database if it doesn't exist
if [ ! -f "instance/presentations.db" ]; then
    echo "Initializing database..."
    python -c "
from app import app, db
with app.app_context():
    db.create_all()
    print('Database tables created successfully')
"
fi

echo "Starting Gunicorn..."
exec python -m gunicorn \
    --workers 1 \
    --threads 4 \
    --bind ${HOST}:${PORT} \
    --timeout 60 \
    --keep-alive 2 \
    --log-level info \
    --access-logfile - \
    --error-logfile - \
    app:app