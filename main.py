#!/usr/bin/env python3
"""
FFmpeg Batch Video Processor
Main application entry point
"""

import uvicorn
import logging
import sys
import os
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('/data/logs/processor.log')
    ]
)

logger = logging.getLogger(__name__)


def ensure_directories():
    """Ensure required directories exist."""
    directories = [
        "/data/input",
        "/data/output",
        "/data/logs"
    ]

    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        logger.info(f"Directory ready: {directory}")


def main():
    """Main application entry point."""
    logger.info("=" * 60)
    logger.info("FFmpeg Batch Video Processor")
    logger.info("=" * 60)

    # Ensure directories
    ensure_directories()

    # Get configuration from environment
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", "8000"))
    workers = int(os.getenv("MAX_WORKERS", "4"))

    logger.info(f"Starting API server on {host}:{port}")
    logger.info(f"Max workers: {workers}")

    # Start the API server
    uvicorn.run(
        "api:app",
        host=host,
        port=port,
        log_level="info",
        access_log=True
    )


if __name__ == "__main__":
    main()
