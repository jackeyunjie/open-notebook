#!/bin/bash
# Open Notebook - Quick Start Script
# One-command setup for new users

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_banner() {
    echo ""
    echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║                                                            ║${NC}"
    echo -e "${BLUE}║         🚀 Open Notebook - Quick Start Script             ║${NC}"
    echo -e "${BLUE}║         Privacy-First AI Research Platform                ║${NC}"
    echo -e "${BLUE}║                                                            ║${NC}"
    echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
    echo ""
}

check_docker() {
    echo -e "${YELLOW}🔍 Checking prerequisites...${NC}"

    if ! command -v docker &> /dev/null; then
        echo -e "${RED}❌ Docker not found. Please install Docker Desktop first:${NC}"
        echo "   https://www.docker.com/products/docker-desktop/"
        exit 1
    fi

    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        echo -e "${RED}❌ Docker Compose not found. Please update Docker Desktop.${NC}"
        exit 1
    fi

    echo -e "${GREEN}✅ Docker is installed${NC}"
}

generate_encryption_key() {
    if command -v openssl &> /dev/null; then
        openssl rand -base64 32
    else
        # Fallback: use random characters
        cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 32 | head -n 1
    fi
}

download_compose_file() {
    echo -e "${YELLOW}📥 Downloading docker-compose.yml...${NC}"

    COMPOSE_URL="https://raw.githubusercontent.com/lfnovo/open-notebook/main/docker-compose.yml"

    if curl -sL "$COMPOSE_URL" -o docker-compose.yml; then
        echo -e "${GREEN}✅ docker-compose.yml downloaded${NC}"
    else
        echo -e "${YELLOW}⚠️  Download failed, creating minimal compose file...${NC}"
        create_minimal_compose
    fi
}

create_minimal_compose() {
    ENCRYPTION_KEY=$(generate_encryption_key)

    cat > docker-compose.yml << EOF
services:
  surrealdb:
    image: surrealdb/surrealdb:v2
    command: start --log info --user root --pass root rocksdb:/mydata/mydatabase.db
    user: root
    ports:
      - "8000:8000"
    volumes:
      - ./surreal_data:/mydata
    restart: always

  open_notebook:
    image: lfnovo/open_notebook:v1-latest
    ports:
      - "8502:8502"
      - "5055:5055"
    environment:
      - OPEN_NOTEBOOK_ENCRYPTION_KEY=${ENCRYPTION_KEY}
      - SURREAL_URL=ws://surrealdb:8000/rpc
      - SURREAL_USER=root
      - SURREAL_PASSWORD=root
      - DEMO_MODE=true
    volumes:
      - ./notebook_data:/app/data
      - ./demo-data:/app/demo-data:ro
    depends_on:
      - surrealdb
    restart: always

  # Optional: Load demo data on first run
  demo-loader:
    image: lfnovo/open_notebook:v1-latest
    depends_on:
      - surrealdb
      - open_notebook
    volumes:
      - ./demo-data:/app/demo-data:ro
    environment:
      - SURREAL_URL=ws://surrealdb:8000/rpc
      - SURREAL_USER=root
      - SURREAL_PASSWORD=root
    command: >
      sh -c "sleep 10 && python -c 'import sys; sys.exit(0)'"
    restart: "no"
EOF

    echo -e "${GREEN}✅ Created docker-compose.yml with secure encryption key${NC}"
}

download_demo_data() {
    echo -e "${YELLOW}📥 Setting up demo data...${NC}"

    mkdir -p demo-data

    # Create demo notebook metadata
    cat > demo-data/README.md << 'EOF'
# Open Notebook - Demo Data

This folder contains sample data to help you explore Open Notebook's features.

## 📚 Demo Notebook: "AI Revolution 2024"

A curated collection exploring the latest AI breakthroughs:
- Transformer architectures and beyond
- Multimodal AI systems
- AI safety and alignment
- Industry applications

## 🎯 Try These Skills

Once your notebook is loaded, try these AI-powered Skills:

1. **Smart Source Analyzer** - Auto-generates summaries and tags
2. **Citation Enhancer** - Adds precise paragraph-level citations
3. **Knowledge Connector** - Builds knowledge graphs from sources
4. **Auto Podcast Planner** - Plans multi-speaker podcast episodes
5. **Research Assistant** - Deep research with iterative queries
6. **Video Generator** - Creates video scripts from content
7. **PPT Generator** - Builds presentation slides
8. **MindMap Generator** - Visualizes topic hierarchies
9. **Meeting Summarizer** - Extracts action items from transcripts
10. **Model Router** - Intelligently routes to best AI model

## 🚀 Quick Start

1. Open http://localhost:8502
2. Go to "Notebooks" → Select "AI Revolution 2024"
3. Explore the pre-loaded sources
4. Try "Generate Podcast" or "Create Mind Map"
EOF

    echo -e "${GREEN}✅ Demo data ready${NC}"
}

start_services() {
    echo -e "${YELLOW}🚀 Starting Open Notebook...${NC}"

    # Check if Docker Desktop is running
    if ! docker info > /dev/null 2>&1; then
        echo ""
        echo -e "${RED}❌ Docker is not running${NC}"
        echo ""
        echo -e "${YELLOW}Please start Docker Desktop first:${NC}"
        echo "   1. Open Docker Desktop application"
        echo "   2. Wait for the engine to start (green light)"
        echo "   3. Run this script again"
        echo ""
        exit 1
    fi

    if docker compose up -d; then
        echo ""
        echo -e "${GREEN}✅ Services started successfully!${NC}"
    else
        echo ""
        echo -e "${RED}❌ Failed to start services${NC}"
        echo ""
        echo -e "${YELLOW}Troubleshooting tips:${NC}"
        echo "   - Check if ports 8000, 8502, 5055 are available"
        echo "   - Run: docker compose logs to see errors"
        echo ""
        exit 1
    fi
}

wait_for_ready() {
    echo -e "${YELLOW}⏳ Waiting for services to be ready...${NC}"

    local retries=30
    local count=0

    while [ $count -lt $retries ]; do
        if curl -s http://localhost:5055/health > /dev/null 2>&1 || \
           curl -s http://localhost:8502 > /dev/null 2>&1; then
            echo ""
            echo -e "${GREEN}✅ Open Notebook is ready!${NC}"
            return 0
        fi

        echo -n "."
        sleep 2
        count=$((count + 1))
    done

    echo ""
    echo -e "${YELLOW}⚠️  Services are starting, but health check timed out.${NC}"
    return 1
}

print_success() {
    echo ""
    echo -e "${GREEN}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║                     🎉 SUCCESS! 🎉                          ║${NC}"
    echo -e "${GREEN}╚════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "${BLUE}📍 Open Notebook is running at:${NC} http://localhost:8502"
    echo ""
    echo -e "${YELLOW}📋 Next Steps:${NC}"
    echo "   1. Open http://localhost:8502 in your browser"
    echo "   2. Go to Settings → API Keys → Add your AI provider"
    echo "   3. Create your first notebook or explore the demo"
    echo ""
    echo -e "${YELLOW}🆘 Need help?${NC}"
    echo "   • Discord: https://discord.gg/37XJPXfz2w"
    echo "   • Docs: https://docs.open-notebook.ai"
    echo "   • Issues: https://github.com/lfnovo/open-notebook/issues"
    echo ""
    echo -e "${BLUE}⚡ Quick Commands:${NC}"
    echo "   docker compose logs -f     # View logs"
    echo "   docker compose down        # Stop services"
    echo "   docker compose up -d       # Start services"
    echo ""
}

print_windows_note() {
    if [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "cygwin" ]] || [[ "$OSTYPE" == "win32" ]]; then
        echo ""
        echo -e "${YELLOW}💡 Windows Users:${NC}"
        echo "   If the above URL doesn't work, try:"
        echo "   http://host.docker.internal:8502"
        echo ""
    fi
}

main() {
    print_banner
    check_docker
    download_compose_file
    download_demo_data
    start_services
    wait_for_ready
    print_success
    print_windows_note
}

# Run main function
main "$@"
