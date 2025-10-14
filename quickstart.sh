#!/bin/bash
# Quick start script for FFmpeg Batch Processor

set -e

echo "========================================"
echo "FFmpeg Batch Processor - Quick Start"
echo "========================================"
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "Error: Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "Error: Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Create directories
echo "Creating necessary directories..."
mkdir -p data/input data/output data/logs config

# Copy environment file if it doesn't exist
if [ ! -f .env ]; then
    echo "Creating .env file..."
    cp .env.example .env 2>/dev/null || echo "No .env.example found, skipping..."
fi

# Build and start the containers
echo ""
echo "Building Docker image..."
docker-compose build

echo ""
echo "Starting services..."
docker-compose up -d

echo ""
echo "Waiting for services to be ready..."
sleep 5

# Check if service is running
if docker-compose ps | grep -q "Up"; then
    echo ""
    echo "✓ FFmpeg Batch Processor is running!"
    echo ""
    echo "========================================"
    echo "Next Steps:"
    echo "========================================"
    echo ""
    echo "1. Place your videos in: ./data/input/"
    echo ""
    echo "2. Process videos using CLI:"
    echo "   docker-compose exec video-processor python cli.py profiles"
    echo "   docker-compose exec video-processor python cli.py profile /data/input/video.mp4 web_optimized"
    echo ""
    echo "3. View API documentation:"
    echo "   http://localhost:8000/docs"
    echo ""
    echo "4. Check processing status:"
    echo "   docker-compose exec video-processor python cli.py stats"
    echo ""
    echo "5. View logs:"
    echo "   docker-compose logs -f video-processor"
    echo ""
    echo "6. Stop the service:"
    echo "   docker-compose down"
    echo ""
    echo "========================================"
    echo "For more examples, see EXAMPLES.md"
    echo "========================================"
else
    echo ""
    echo "✗ Failed to start services. Check logs:"
    echo "   docker-compose logs"
    exit 1
fi
