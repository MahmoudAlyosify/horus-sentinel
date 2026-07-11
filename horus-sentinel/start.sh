#!/bin/bash

echo "=============================================="
echo "       Starting HORUS Sentinel"
echo "=============================================="
echo ""

# Check if Docker is running
if ! docker info >/dev/null 2>&1; then
    echo "[ERROR] Docker is not running or not installed."
    echo "Please start Docker and run this script again."
    exit 1
fi

# Check for .env file
if [ ! -f ".env" ]; then
    echo "[INFO] .env file not found. Creating default .env from .env.example..."
    cp .env.example .env
    echo "[INFO] .env file created successfully."
fi

echo "[INFO] Building and starting containers..."
docker compose -f deploy/docker-compose.yml up -d --build

echo ""
echo "=============================================="
echo "       HORUS Sentinel is Running!"
echo "=============================================="
echo "- Backend API Docs : http://localhost:8000/docs"
echo "- Neo4j Graph DB   : http://localhost:7474"
echo "- MinIO (S3)       : http://localhost:9001"
echo ""
echo "To see the logs, run: docker compose -f deploy/docker-compose.yml logs -f"
echo "=============================================="
