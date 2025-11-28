#!/bin/bash
# Build script for Render.com

set -e  # Exit on error

echo "🚀 Starting Nexus CRM Build..."

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Install Playwright
echo "🌐 Installing Playwright Chromium..."
playwright install chromium
playwright install-deps chromium

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p automation/canopus/downloads/Danner
mkdir -p automation/canopus/excel_files
mkdir -p boletos
mkdir -p logs

echo "✅ Build completed successfully!"
