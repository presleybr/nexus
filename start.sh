#!/bin/bash
# Start script for Render.com

set -e

echo "🚀 Starting Nexus CRM..."

# Check if DATABASE_URL is set
if [ -z "$DATABASE_URL" ]; then
    echo "❌ ERROR: DATABASE_URL is not set!"
    exit 1
fi

# Run migrations (if needed)
if [ -f "database/init_database.sql" ]; then
    echo "📊 Running database migrations..."
    # Note: Migrations should be run manually the first time
    # Or use a migration tool like Alembic
fi

# Start Flask application
echo "🌐 Starting Flask server on port ${PORT:-5000}..."
exec python backend/app.py
