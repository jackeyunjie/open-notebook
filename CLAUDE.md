# Open Notebook - Root CLAUDE.md

This file provides architectural guidance for contributors working on Open Notebook at the project level.

## Project Overview

**Open Notebook** is an open-source, privacy-focused alternative to Google's Notebook LM. It's an AI-powered research assistant enabling users to upload multi-modal content (PDFs, audio, video, web pages), generate intelligent notes, search semantically, chat with AI models, and produce professional podcasts—all with complete control over data and choice of AI providers.

**Key Values**: Privacy-first, multi-provider AI support, fully self-hosted option, open-source transparency.

---

## Three-Tier Architecture

```
┌─────────────────────────────────────────────────────────┐
│              Frontend (React/Next.js)                    │
│              frontend/ @ port 3000                       │
├─────────────────────────────────────────────────────────┤
│ - Notebooks, sources, notes, chat, podcasts, search UI  │
│ - Zustand state management, TanStack Query (React Query)│
│ - Shadcn/ui component library with Tailwind CSS         │
└────────────────────────┬────────────────────────────────┘
                         │ HTTP REST
┌────────────────────────▼────────────────────────────────┐
│              API (FastAPI)                              │
│              api/ @ port 5055                           │
├─────────────────────────────────────────────────────────┤
│ - REST endpoints for notebooks, sources, notes, chat    │
│ - LangGraph workflow orchestration                      │
│ - Job queue for async operations (podcasts)             │
│ - Multi-provider AI provisioning via Esperanto          │
│ - Living Knowledge System integration (port 8888)       │
└────────────────────────┬────────────────────────────────┘
                         │ SurrealQL
┌────────────────────────▼────────────────────────────────┐
│         Database (SurrealDB)                            │
│         Graph database @ port 8000                      │
├─────────────────────────────────────────────────────────┤
│ - Records: Notebook, Source, Note, ChatSession, Credential│
│ - Relationships: source-to-notebook, note-to-source     │
│ - Vector embeddings for semantic search                 │
└─────────────────────────────────────────────────────────┘
```

---

## Living Knowledge System (New)

An organic, self-growing knowledge management system based on human body organization principles.

### Architecture: Five-Layer Cognitive Model

```
┌─────────────────────────────────────────────────────────┐
│  P4 DataAgent (Immune System)                           │
│  - Data lifecycle management (hot/warm/cold/frozen)     │
│  - Quality monitoring and auto-repair                   │
│  - Storage cost optimization (83% savings)              │
├─────────────────────────────────────────────────────────┤
│  P3 Evolution Layer                                     │
│  - Self-improvement through feedback loops              │
│  - Strategy optimization over time                      │
├─────────────────────────────────────────────────────────┤
│  P2 Relationship Layer                                  │
│  - Knowledge graph construction                         │
│  - Cross-reference and association                      │
├─────────────────────────────────────────────────────────┤
│  P1 Judgment Layer                                      │
│  - Value assessment and prioritization                  │
│  - Multi-dimensional evaluation                         │
├─────────────────────────────────────────────────────────┤
│  P0 Perception Layer                                    │
│  - Pain Scanner: Detect friction points                 │
│  - Emotion Watcher: Monitor sentiment                   │
│  - Trend Hunter: Identify patterns                      │
│  - Scene Discover: Context awareness                    │
└─────────────────────────────────────────────────────────┘
```

### Biological Analogies

| Software Component | Biological Analogy | Function |
|-------------------|-------------------|----------|
| Skill | Cell | Basic functional unit with lifecycle |
| Agent | Tissue | Group of collaborating skills |
| System | Organ | Complex functional unit |
| Flow | Meridian | Data/control/temporal connections |
| Trigger | Acupoint | External access points |
| DataAgent | Immune System | Health monitoring and maintenance |

### Technical Stack

- **Database**: PostgreSQL 15+ with TimescaleDB 2.11+
- **API**: FastAPI on port 8888
- **Architecture**: Independent service (loosely coupled)
- **Data Model**: Cell → Tissue → Organ → Meridian → Acupoint

### Quick Start

```bash
# Start Living Knowledge System
./scripts/start_living.sh dev

# Access API
open http://localhost:8888/docs
```

### Key Files

- `open_notebook/skills/living/skill_cell.py` - Cell lifecycle management
- `open_notebook/skills/living/agent_tissue.py` - Agent coordination
- `open_notebook/skills/living/meridian_flow.py` - Message flow system
- `open_notebook/skills/living/acupoint_trigger.py` - External triggers
- `open_notebook/skills/living/p4_data_agent.py` - Data lifecycle management
- `open_notebook/skills/living/launcher.py` - Service launcher
- `open_notebook/skills/living/api_server.py` - REST API server
- `open_notebook/skills/living/database/` - PostgreSQL abstraction layer

---

## Useful sources

User documentation is at @docs/

## Tech Stack

### Frontend (`frontend/`)
- **Framework**: Next.js 16 (React 19)
- **Language**: TypeScript
- **State Management**: Zustand
- **Data Fetching**: TanStack Query (React Query)
- **Styling**: Tailwind CSS + Shadcn/ui
- **Build Tool**: Webpack (via Next.js)
- **i18n compatible**: All front-end changes must also consider the translation keys

### API Backend (`api/` + `open_notebook/`)
- **Framework**: FastAPI 0.104+
- **Language**: Python 3.11+
- **Workflows**: LangGraph state machines
- **Database**: SurrealDB async driver
- **AI Providers**: Esperanto library (8+ providers: OpenAI, Anthropic, Google, Groq, Ollama, Mistral, DeepSeek, xAI)
- **Job Queue**: Surreal-Commands for async jobs (podcasts)
- **Logging**: Loguru
- **Validation**: Pydantic v2
- **Testing**: Pytest

### Database
- **SurrealDB**: Graph database with built-in embedding storage and vector search
- **Schema Migrations**: Automatic on API startup via AsyncMigrationManager

### Additional Services
- **Content Processing**: content-core library (file/URL extraction)
- **Prompts**: AI-Prompter with Jinja2 templating
- **Podcast Generation**: podcast-creator library
- **Embeddings**: Multi-provider via Esperanto

---

## Architecture Highlights

### 1. Async-First Design
- All database queries, graph invocations, and API calls are async (await)
- SurrealDB async driver with connection pooling
- FastAPI handles concurrent requests efficiently

### 2. LangGraph Workflows
- **source.py**: Content ingestion (extract → embed → save)
- **chat.py**: Conversational agent with message history
- **ask.py**: Search + synthesis (retrieve relevant sources → LLM)
- **transformation.py**: Custom transformations on sources
- All use `provision_langchain_model()` for smart model selection

### 3. Multi-Provider AI
- **Esperanto library**: Unified interface to 8+ AI providers
- **Credential system**: Individual encrypted credential records per provider; models link to credentials for direct config
- **ModelManager**: Factory pattern with fallback logic; uses credential config when available, env vars as fallback
- **Smart selection**: Detects large contexts, prefers long-context models
- **Override support**: Per-request model configuration

### 4. Database Schema
- **Automatic migrations**: AsyncMigrationManager runs on API startup
- **SurrealDB graph model**: Records with relationships and embeddings
- **Vector search**: Built-in semantic search across all content
- **Transactions**: Repo functions handle ACID operations

### 5. Authentication
- **Current**: Simple password middleware (insecure, dev-only)
- **Production**: Replace with OAuth/JWT (see CONFIGURATION.md)

---

## Important Quirks & Gotchas

### API Startup
- **Migrations run automatically** on startup; check logs for errors
- **Must start API before UI**: UI depends on API for all data
- **SurrealDB must be running**: API fails without database connection

### Frontend-Backend Communication
- **Base API URL**: Configured in `.env.local` (default: http://localhost:5055)
- **CORS enabled**: Configured in `api/main.py` (allow all origins in dev)
- **Rate limiting**: Not built-in; add at proxy layer for production

### LangGraph Workflows
- **Blocking operations**: Chat/podcast workflows may take minutes; no timeout
- **State persistence**: Uses SQLite checkpoint storage in `/data/sqlite-db/`
- **Model fallback**: If primary model fails, falls back to cheaper/smaller model

### Podcast Generation
- **Async job queue**: `podcast_service.py` submits jobs but doesn't wait
- **Track status**: Use `/commands/{command_id}` endpoint to poll status
- **TTS failures**: Fall back to silent audio if speech synthesis fails

### Content Processing
- **File extraction**: Uses content-core library; supports 50+ file types
- **URL handling**: Extracts text + metadata from web pages
- **Large files**: Content processing is sync; may block API briefly

---

## Component References

See dedicated CLAUDE.md files for detailed guidance:

- **[frontend/CLAUDE.md](frontend/CLAUDE.md)**: React/Next.js architecture, state management, API integration
- **[api/CLAUDE.md](api/CLAUDE.md)**: FastAPI structure, service pattern, endpoint development
- **[open_notebook/CLAUDE.md](open_notebook/CLAUDE.md)**: Backend core, domain models, LangGraph workflows, AI provisioning
- **[open_notebook/domain/CLAUDE.md](open_notebook/domain/CLAUDE.md)**: Data models, repository pattern, search functions
- **[open_notebook/ai/CLAUDE.md](open_notebook/ai/CLAUDE.md)**: ModelManager, AI provider integration, Esperanto usage
- **[open_notebook/graphs/CLAUDE.md](open_notebook/graphs/CLAUDE.md)**: LangGraph workflow design, state machines
- **[open_notebook/database/CLAUDE.md](open_notebook/database/CLAUDE.md)**: SurrealDB operations, migrations, async patterns
- **[open_notebook/skills/living/](open_notebook/skills/living/)**: Living Knowledge System - organic, self-growing knowledge management

---

## Documentation Map

- **[README.md](README.md)**: Project overview, features, quick start
- **[docs/index.md](docs/index.md)**: Complete user & deployment documentation
- **[CONFIGURATION.md](CONFIGURATION.md)**: Environment variables, model configuration
- **[CONTRIBUTING.md](CONTRIBUTING.md)**: Contribution guidelines
- **[MAINTAINER_GUIDE.md](MAINTAINER_GUIDE.md)**: Release & maintenance procedures

---

## Testing Strategy

- **Unit tests**: `tests/test_domain.py`, `test_models_api.py`
- **Graph tests**: `tests/test_graphs.py` (workflow integration)
- **Utils tests**: `tests/test_utils.py`, `tests/test_chunking.py`, `tests/test_embedding.py`
- **Run all**: `uv run pytest tests/`
- **Coverage**: Check with `pytest --cov`

---

## Common Tasks

### Add a New API Endpoint
1. Create router in `api/routers/feature.py`
2. Create service in `api/feature_service.py`
3. Define schemas in `api/models.py`
4. Register router in `api/main.py`
5. Test via http://localhost:5055/docs

### Add a New LangGraph Workflow
1. Create `open_notebook/graphs/workflow_name.py`
2. Define StateDict and node functions
3. Build graph with `.add_node()` / `.add_edge()`
4. Invoke in service: `graph.ainvoke({"input": ...}, config={"..."})`
5. Test with sample data in `tests/`

### Add Database Migration
1. Create `migrations/XXX_description.surql`
2. Write SurrealQL schema changes
3. Create `migrations/XXX_description_down.surql` (optional rollback)
4. API auto-detects on startup; migration runs if newer than recorded version

### Deploy to Production
1. Review [CONFIGURATION.md](CONFIGURATION.md) for security settings
2. Use `make docker-release` for multi-platform image
3. Push to Docker Hub / GitHub Container Registry
4. Deploy `docker compose --profile multi up`
5. Verify migrations via API logs

---

## Support & Community

- **Documentation**: https://open-notebook.ai
- **Discord**: https://discord.gg/37XJPXfz2w
- **Issues**: https://github.com/lfnovo/open-notebook/issues
- **License**: MIT (see LICENSE)

---

**Last Updated**: February 2026 | **Project Version**: 1.3.0+
