# Developer Guide

> Complete guide for setting up, developing, and contributing to Vantage

---

## Table of Contents

1. [Development Setup](#development-setup)
2. [Environment Configuration](#environment-configuration)
3. [Development Workflows](#development-workflows)
4. [Project Structure](#project-structure)
5. [Adding New Features](#adding-new-features)
6. [Testing](#testing)
7. [Troubleshooting](#troubleshooting)

---

## Development Setup

### Prerequisites

| Requirement | Version | Purpose |
|-------------|---------|---------|
| Python | 3.8+ | Backend runtime |
| Node.js | 16+ | Frontend tooling |
| Conda | Latest | Environment management |
| Docker | 20+ | Infrastructure services |
| Ollama | Latest | Local LLM inference |

### Step-by-Step Setup

#### 1. Clone the Repository

```bash
git clone https://github.com/HalfBloodPrince07/Vantage.git
cd Vantage
```

#### 2. Create and Activate Conda Environment

```bash
# Create environment
conda create -n opensearch python=3.10 -y

# Activate environment (REQUIRED for all backend operations)
conda activate opensearch
```

> **Important**: Always use the `opensearch` conda environment for all Python operations.

#### 3. Install Python Dependencies

```bash
pip install -r requirements.txt
```

#### 4. Install Frontend Dependencies

```bash
cd frontend
npm install
cd ..
```

#### 5. Start Infrastructure Services

```bash
# Start OpenSearch and Redis containers
docker-compose up -d

# Verify services are running
docker ps

# Expected output:
# - locallens_opensearch (port 9200)
# - locallens_redis (port 6379)
# - locallens_dashboards (port 5601)
```

#### 6. Start Ollama and Pull Model

```bash
# Start Ollama server
ollama serve

# In another terminal, pull the required model
ollama pull qwen3-vl:8b
```

#### 7. Run the Application

**Backend:**

```bash
# From project root
python -m backend.api
```

**Frontend:**

```bash
cd frontend
npm run dev
```

---

## Environment Configuration

### config.yaml Reference

The main configuration file is `config.yaml` in the project root.

#### Ollama Settings

```yaml
ollama:
  base_url: "http://localhost:11434"
  timeout: 500
  unified_model:
    name: "qwen3-vl:8b"    # Change model here
    temperature: 0.3
    max_tokens: 15000
```

#### OpenSearch Settings

```yaml
opensearch:
  host: "localhost"
  port: 9200
  index_name: "locallens_index"
  use_ssl: true
  verify_certs: false
  auth:
    username: "admin"
    password: "LocalLens@1234"  # Change for production
```

#### Search Configuration

```yaml
search:
  hybrid:
    enabled: true
    vector_weight: 0.7    # Increase for more semantic matching
    bm25_weight: 0.3      # Increase for more keyword matching
  recall_top_k: 50        # Initial retrieval count
  rerank_top_k: 5         # Final result count
  min_score: 0.3          # Minimum relevance threshold
```

#### Memory Settings

```yaml
memory:
  session:
    backend: "redis"              # Options: "redis" or "memory"
    redis_url: "redis://localhost:6379"
    window_size: 10               # Conversation turns to keep
    ttl_seconds: 3600             # Session timeout
```

---

## Development Workflows

### Running the Development Server

```bash
# Backend (auto-reload enabled via uvicorn)
python -m backend.api

# Frontend (hot-reload enabled via Vite)
cd frontend
npm run dev
```

### Linting

**Frontend:**

```bash
cd frontend
npm run lint
```

**Backend:**

```bash
# TODO: No linting configured. Recommended: add flake8 or ruff
# pip install flake8
# flake8 backend/
```

### Building for Production

**Frontend:**

```bash
cd frontend
npm run build      # Creates dist/ folder
npm run preview    # Preview production build
```

**Backend:**
The backend runs the same way in production; use a process manager like `gunicorn`:

```bash
pip install gunicorn
gunicorn -w 4 -k uvicorn.workers.UvicornWorker backend.api:app --bind 0.0.0.0:8000
```

### Logs

Logs are written to the `logs/` directory:

- `logs/backend.log` - Backend application logs
- `logs/frontend.log` - Frontend dev server logs

---

## Project Structure

```
Vantage/
├── backend/                      # Python backend (FastAPI)
│   ├── __init__.py               # Package exports
│   ├── api.py                    # FastAPI app with all endpoints
│   ├── auth.py                   # Authentication utilities
│   ├── auth_endpoints.py         # Auth-related API endpoints
│   ├── feedback.py               # User feedback handling
│   ├── ingestion.py              # Document processing pipeline
│   ├── opensearch_client.py      # OpenSearch wrapper
│   ├── reranker.py               # Cross-encoder reranking
│   ├── watcher.py                # File system watcher
│   ├── watcher_endpoints.py      # Watcher API endpoints
│   ├── mcp_tools.py              # MCP tool registry
│   ├── a2a_agent.py              # Agent-to-Agent base classes
│   ├── streaming_steps.py        # SSE step emission
│   │
│   ├── agents/                   # Specialized AI agents
│   │   ├── query_classifier.py   # Athena - Intent detection
│   │   ├── analysis_agent.py     # Analysis tasks
│   │   ├── clarification_agent.py # Socrates - Disambiguation
│   │   ├── summarization_agent.py # Thoth - Summarization
│   │   ├── explanation_agent.py   # Hermes - Result explanation
│   │   ├── critic_agent.py        # Diogenes - Quality control
│   │   ├── confidence_scorer.py   # Themis - Scoring
│   │   ├── graph_rag_agent.py     # Apollo - Graph expansion
│   │   ├── reasoning_planner.py   # Odysseus - Multi-hop
│   │   ├── adaptive_retriever.py  # Proteus - Strategy selection
│   │   └── retrieval_controller.py # Retrieval orchestration
│   │
│   ├── graph/                    # Knowledge graph
│   │   ├── knowledge_graph.py    # Graph CRUD operations
│   │   ├── entity_resolver.py    # Entity disambiguation
│   │   └── relationship_extractor.py # Relation extraction
│   │
│   ├── memory/                   # Memory systems
│   │   ├── memory_manager.py     # Memory coordination
│   │   ├── session_memory.py     # Short-term (Redis)
│   │   ├── episodic_memory.py    # Query-response pairs
│   │   ├── procedural_memory.py  # Learned patterns
│   │   ├── user_profile.py       # User preferences
│   │   ├── memory_reflector.py   # Memory consolidation
│   │   ├── memory_tool.py        # LangChain tool wrapper
│   │   ├── conversation_manager.py # Chat history
│   │   └── agentic_memory/       # A-mem implementation
│   │
│   ├── orchestration/            # Workflow management
│   │   └── orchestrator.py       # Zeus - LangGraph workflows
│   │
│   ├── ranking/                  # Ranking utilities
│   │
│   ├── utils/                    # Shared utilities
│   │   ├── llm_utils.py          # Ollama API wrappers
│   │   ├── model_manager.py      # Model lifecycle
│   │   └── session_logger.py     # LLM call logging
│   │
│   ├── tests/                    # Backend tests
│   └── uploads/                  # Uploaded files storage
│
├── frontend/                     # React frontend (Vite)
│   ├── package.json              # Dependencies and scripts
│   ├── vite.config.js            # Vite configuration
│   ├── index.html                # HTML entry point
│   │
│   └── src/
│       ├── main.jsx              # React entry point
│       ├── App.jsx               # Root component
│       ├── index.css             # Global styles
│       │
│       ├── components/           # React components
│       │   ├── ChatInterface.jsx # Main chat UI
│       │   ├── ChatSidebar.jsx   # Conversation list
│       │   ├── OnboardingWizard.jsx # Setup wizard
│       │   ├── SettingsPanel.jsx # User settings
│       │   ├── DocumentSelector.jsx # Document picker
│       │   ├── EntityGraphModal.jsx # Knowledge graph viz
│       │   ├── MemoryExplorer.jsx # Memory browser
│       │   ├── AgentThinking.jsx # Agent status display
│       │   └── ... (44 total components)
│       │
│       ├── hooks/                # Custom React hooks
│       │   └── useDarkMode.jsx   # Theme management
│       │
│       └── styles/               # CSS modules
│           ├── dark-mode.css
│           └── ai-dashboard.css
│
├── config.yaml                   # Application configuration
├── docker-compose.yml            # Infrastructure services
├── requirements.txt              # Python dependencies
├── run.bat                       # Windows startup script
├── run.sh                        # Linux/Mac startup script
└── *.db                          # SQLite databases (generated)
```

---

## Adding New Features

### Pattern: Adding a New Agent

1. **Create the agent file** in `backend/agents/`:

```python
# backend/agents/my_agent.py

from typing import Dict, Any, Optional
from loguru import logger

class MyAgent:
    AGENT_NAME = "Hephaestus"  # Greek mythology name
    AGENT_TITLE = "The Craftsman"
    AGENT_DESCRIPTION = "God of forge - I craft custom solutions"
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.model = config.get("ollama", {}).get("unified_model", {}).get("name", "qwen3-vl:8b")
        logger.info(f"[{self.AGENT_NAME}] Initialized")
    
    async def process(self, query: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Main processing method.
        
        Args:
            query: User query
            context: Optional context from previous agents
            
        Returns:
            Dict with 'result', 'confidence', and any other outputs
        """
        # Your agent logic here
        pass
```

1. **Register in orchestrator** (`backend/orchestration/orchestrator.py`):

```python
from backend.agents.my_agent import MyAgent

class EnhancedOrchestrator:
    def __init__(self, ...):
        # ...existing code...
        self.my_agent = MyAgent(config)
```

1. **Add to workflow** (if using LangGraph):

```python
def _build_langgraph_workflow(self):
    workflow = StateGraph(WorkflowState)
    workflow.add_node("my_agent", self._my_agent_node)
    # Add edges...
```

### Pattern: Adding a New API Endpoint

1. **Add endpoint in `backend/api.py`**:

```python
from pydantic import BaseModel

class MyRequest(BaseModel):
    param1: str
    param2: int = 10

@app.post("/my-endpoint")
async def my_endpoint(request: MyRequest):
    """
    Description of what this endpoint does.
    """
    # Your logic here
    return {"status": "success", "result": result}
```

1. **Add frontend call** in relevant component:

```javascript
const callMyEndpoint = async (param1, param2) => {
    const response = await fetch('http://localhost:8000/my-endpoint', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ param1, param2 })
    });
    return response.json();
};
```

### Pattern: Adding a New Memory Type

1. **Create memory class** in `backend/memory/`:

```python
# backend/memory/my_memory.py

from typing import Dict, Any, List
from loguru import logger

class MyMemory:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
    
    async def store(self, key: str, value: Any) -> None:
        """Store a memory entry."""
        pass
    
    async def retrieve(self, key: str) -> Any:
        """Retrieve a memory entry."""
        pass
    
    async def search(self, query: str) -> List[Dict]:
        """Search memories."""
        pass
```

1. **Register in MemoryManager** (`backend/memory/memory_manager.py`):

```python
from backend.memory.my_memory import MyMemory

class MemoryManager:
    def __init__(self, config):
        # ...existing code...
        self.my_memory = MyMemory(config)
```

---

## Testing

### Running Backend Tests

```bash
# From project root
python -m pytest backend/tests/ -v
```

### Test Files

| File | Purpose |
|------|---------|
| `backend/tests/verify_agents.py` | Verify agent initialization |
| `backend/tests/verify_fixes.py` | Verify bug fixes |
| `backend/tests/reproduce_memory_error.py` | Memory error reproduction |

### Manual Testing

**Search endpoint:**

```bash
curl -X POST http://localhost:8000/search \
  -H "Content-Type: application/json" \
  -d '{"query": "test query", "top_k": 5}'
```

**Health check:**

```bash
curl http://localhost:8000/health
```

**Index stats:**

```bash
curl http://localhost:8000/stats
```

---

## Troubleshooting

### Common Issues

#### 1. OpenSearch Connection Failed

**Symptom:** `ConnectionError: Unable to connect to OpenSearch`

**Solution:**

```bash
# Check if OpenSearch is running
docker ps | grep opensearch

# If not running, start it
docker-compose up -d opensearch

# Wait for startup (can take 60+ seconds)
curl -k https://localhost:9200 -u admin:LocalLens@1234
```

#### 2. Ollama Model Not Found

**Symptom:** `ollama.ResponseError: model 'qwen3-vl:8b' not found`

**Solution:**

```bash
# Pull the model
ollama pull qwen3-vl:8b

# Verify it's available
ollama list
```

#### 3. Redis Connection Error

**Symptom:** `redis.exceptions.ConnectionError`

**Solution:**

```bash
# Check if Redis is running
docker ps | grep redis

# If not, backend falls back to in-memory session storage
# To start Redis:
docker-compose up -d redis
```

#### 4. Frontend Proxy Error

**Symptom:** `ECONNREFUSED` when calling API from frontend

**Solution:**

- Ensure backend is running on port 8000
- Check `vite.config.js` proxy configuration
- Verify CORS is enabled in `backend/api.py`

#### 5. CUDA Out of Memory

**Symptom:** `CUDA out of memory` during embedding or LLM calls

**Solution:**

```python
# In config.yaml, reduce batch sizes:
models:
  cross_encoder:
    batch_size: 16  # Reduce from 32

# Or disable GPU:
performance:
  enable_gpu: false
```

### Debug Mode

Enable verbose logging in `config.yaml`:

```yaml
observability:
  logging:
    level: "DEBUG"
    agent_logging: true
    memory_logging: true
```

### Viewing Logs

```bash
# Backend logs
tail -f logs/backend.log

# Or run backend with visible output
python -m backend.api 2>&1 | tee logs/debug.log
```

---

## Code Style Guidelines

### Python

- Use type hints for function signatures
- Use `loguru` for logging (not standard `logging`)
- Follow agent naming convention (Greek mythology)
- Use async/await for I/O operations

### JavaScript/React

- Use functional components with hooks
- Keep components focused and small
- Use CSS modules (`.css` files per component)
- Handle loading and error states

### Commit Messages

```
feat: Add new summarization agent (Thoth)
fix: Resolve memory leak in session manager
docs: Update API documentation
refactor: Extract common LLM utilities
test: Add integration tests for search
```

---

## API Reference

See the auto-generated FastAPI docs at:

- **Swagger UI**: <http://localhost:8000/docs>
- **ReDoc**: <http://localhost:8000/redoc>
