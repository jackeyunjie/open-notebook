#!/bin/bash
# Living Knowledge System Startup Script
# Usage: ./scripts/start_living.sh [dev|prod|stop|logs]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR"

case "${1:-dev}" in
    dev)
        echo "🚀 Starting Living Knowledge System (Development Mode)..."
        echo ""
        echo "Starting PostgreSQL..."
        docker-compose -f docker-compose.living.yml up -d postgres
        echo ""
        echo "⏳ Waiting for PostgreSQL to be ready..."
        sleep 5
        echo ""
        echo "Starting API server (local)..."
        echo "   API will be available at: http://localhost:8888"
        echo "   Docs: http://localhost:8888/docs"
        echo ""
        LIVING_DB_HOST=localhost \
        LIVING_DB_PORT=5433 \
        LIVING_PORT=8888 \
        python -m open_notebook.skills.living.api_server
        ;;

    prod)
        echo "🚀 Starting Living Knowledge System (Production Mode)..."
        docker-compose -f docker-compose.living.yml up -d
        echo ""
        echo "✅ System started!"
        echo "   API: http://localhost:8888"
        echo "   Health: http://localhost:8888/health"
        echo ""
        echo "View logs: ./scripts/start_living.sh logs"
        ;;

    stop)
        echo "🛑 Stopping Living Knowledge System..."
        docker-compose -f docker-compose.living.yml down
        echo "✅ System stopped"
        ;;

    logs)
        echo "📜 Showing logs..."
        docker-compose -f docker-compose.living.yml logs -f
        ;;

    reset)
        echo "⚠️  WARNING: This will delete all data!"
        read -p "Are you sure? (yes/no): " confirm
        if [ "$confirm" = "yes" ]; then
            docker-compose -f docker-compose.living.yml down -v
            echo "✅ Data cleared, system reset"
        else
            echo "Cancelled"
        fi
        ;;

    *)
        echo "Usage: $0 [dev|prod|stop|logs|reset]"
        echo ""
        echo "Commands:"
        echo "  dev    - Start with local API server (for development)"
        echo "  prod   - Start full production stack"
        echo "  stop   - Stop all services"
        echo "  logs   - View logs"
        echo "  reset  - Clear all data (DANGER!)"
        exit 1
        ;;
esac
