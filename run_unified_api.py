"""Unified API Server Launcher.

Starts the combined Open Notebook + Living Knowledge System API
on a single port (default: 5055).

Usage:
    python run_unified_api.py
    python run_unified_api.py --port 8080
    python run_unified_api.py --host 0.0.0.0 --port 5055 --reload
"""

import argparse
import os
import sys

import uvicorn
from loguru import logger


def main():
    """Run the unified API server."""
    parser = argparse.ArgumentParser(
        description="Open Notebook + LKS Unified API Server"
    )
    parser.add_argument(
        "--host",
        default=os.getenv("API_HOST", "0.0.0.0"),
        help="Host to bind to (default: 0.0.0.0)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=int(os.getenv("API_PORT", "5055")),
        help="Port to bind to (default: 5055)"
    )
    parser.add_argument(
        "--reload",
        action="store_true",
        help="Enable auto-reload for development"
    )
    parser.add_argument(
        "--log-level",
        default="info",
        choices=["debug", "info", "warning", "error", "critical"],
        help="Logging level (default: info)"
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=1,
        help="Number of worker processes (default: 1)"
    )
    
    args = parser.parse_args()
    
    # Configure logging
    logger.info(f"Starting Unified API Server on {args.host}:{args.port}")
    logger.info(f"API Documentation: http://{args.host}:{args.port}/docs")
    logger.info(f"Health Check: http://{args.host}:{args.port}/health")
    
    # Run server
    uvicorn.run(
        "api.unified_main:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        log_level=args.log_level,
        workers=args.workers if not args.reload else 1,
        access_log=True,
    )


if __name__ == "__main__":
    main()
