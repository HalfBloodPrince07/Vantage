# Project Architecture Overview

This document provides a **textual architecture diagram** of the entire Vantage system, showing the major layers and their interactions.

```
+----------------------+      +----------------------+      +----------------------+
|   User Interface    |      |   API Layer (FastAPI)|      |   Infrastructure     |
|  (React/Vite)      |<---->|  (backend/api.py)    |<---->|  Docker Compose       |
+----------------------+      +----------------------+      +----------------------+
          |                               |                               |
          |                               |                               |
          v                               v                               v
+----------------------+      +----------------------+      +----------------------+ 
|   Frontend Components|      |   Orchestration     |      |   Services          |
|   (Chat, Landing)   |      |   (Zeus)            |      |   - OpenSearch       |
+----------------------+      +----------------------+      |   - Redis            |
          |                               |               |   - Ollama (LLM)    |
          |                               |               +----------------------+
          v                               v
+----------------------+      +----------------------+      +----------------------+ 
|   SSE Streaming      |      |   Agent Layer        |      |   Data Layer         |
|   (thinking steps)  |<---->|   (Agents)           |<---->|   (OpenSearch, SQLite,|
+----------------------+      +----------------------+      |    Redis)            |
          |                               |               +----------------------+
          |                               |
          v                               v
+----------------------+      +----------------------+      +----------------------+ 
|   Session Context    |      |   Memory System      |      |   Knowledge Graph    |
|   (Redis)            |<---->|   (5‑tier)           |<---->|   (Entity/Relation) |
+----------------------+      +----------------------+      +----------------------+ 
```

**Key Interactions**

- The UI sends HTTP requests (or SSE) to the FastAPI server.
- FastAPI forwards the request to **Zeus**, the central orchestrator.
- Zeus routes the request to the appropriate **agent(s)** based on intent and attached documents.
- Agents interact with the **Data Layer** (OpenSearch for vector/keyword search, SQLite for persistence) and the **Knowledge Graph**.
- All intermediate steps are streamed back to the UI via **Server‑Sent Events**.
- The **Memory System** provides session context, user preferences, and episodic memory.
- Underlying services (OpenSearch, Redis, Ollama) run in Docker containers.
