# Vantage Quick Start Guide ⚡

Get Vantage running in **5 minutes** with this step-by-step guide.

---

## 📋 Prerequisites Checklist

| Requirement | Version | Check Command |
|-------------|---------|---------------|
| Python | 3.10+ | `python --version` |
| Node.js | 18+ | `node --version` |
| npm | 9+ | `npm --version` |
| Docker | Latest | `docker --version` |
| Ollama | Latest | `ollama --version` |

---

## 🚀 Step 1: Clone & Setup

```bash
# Clone the repository
git clone <repository-url>
cd LocaLense_V2

# Create Python virtual environment (recommended)
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt
```

---

## 🐳 Step 2: Start OpenSearch

**Option A: Docker Compose (Recommended)**
```bash
docker-compose up -d
```

**Option B: Manual Docker**
```bash
docker run -d \
  --name opensearch \
  -p 9200:9200 \
  -p 9600:9600 \
  -e "discovery.type=single-node" \
  -e "DISABLE_SECURITY_PLUGIN=true" \
  opensearchproject/opensearch:2.11.0
```

**Verify OpenSearch is running:**
```bash
curl http://localhost:9200
```

---

## 🤖 Step 3: Setup Ollama & Models

```bash
# Start Ollama service
ollama serve

# Download required models (in a new terminal)
ollama pull nomic-embed-text    # Embeddings (768 dim)
ollama pull qwen2.5:7b          # Main LLM

# Optional: Vision model for images
ollama pull qwen2.5vl:latest
```

**Verify models are available:**
```bash
ollama list
```

You should see:
```
NAME                  SIZE
nomic-embed-text      274 MB
qwen2.5:7b            4.7 GB
```

---

## ⚛️ Step 4: Setup Frontend

```bash
cd frontend
npm install
cd ..
```

---

## ▶️ Step 5: Run Vantage

### Easy Start (Recommended)

**Windows:**
```bash
run.bat
```

**Linux/Mac:**
```bash
chmod +x run.sh
./run.sh
```

### Manual Start

**Terminal 1 - Backend:**
```bash
cd LocaLense_V2
python -m backend.api
```

You should see:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
⚡ Zeus (The Conductor) initialized
   ├── Athena Path: Socrates, Aristotle, Thoth, Hermes, Diogenes
   └── Daedalus Path: Prometheus, Hypatia, Mnemosyne
```

**Terminal 2 - Frontend:**
```bash
cd LocaLense_V2/frontend
npm run dev
```

You should see:
```
VITE v5.x.x ready in xxx ms
➜ Local:   http://localhost:5173/
```

---

## 🎯 Step 6: First Time Configuration

### 1. Open Vantage
Navigate to **http://localhost:5173**

### 2. Create Account
- Click **Sign Up**
- Enter username and password
- Click **Create Account**

### 3. Index Your Documents

**Option A: Index a Folder**
1. Click the folder icon in the sidebar
2. Enter path: `C:\Users\YourName\Documents` (Windows) or `/home/you/documents` (Linux)
3. Click **Index** and wait for completion

**Option B: Upload Files**
1. Click the upload icon
2. Drag & drop or select files
3. Supported: PDF, DOCX, TXT, MD, XLSX, CSV, PNG, JPG

### 4. Start Searching!
Type natural language queries like:
- "Find my invoices from 2024"
- "Compare the budget reports"
- "Summarize the project documentation"

---

## 🏗️ Understanding the Agent System

When you send a query, you'll see the **Greek Pantheon agents** working:

```
⚡ Zeus (The Conductor) → Receiving Query → "Find my invoices..."
🦉 Athena (The Strategist) → Analyzing Intent → document_search
🔍 Search Agent → Searching → Performing hybrid search
📨 Hermes (The Messenger) → Explaining Results → Explained top 3
🔎 Diogenes (The Critic) → Reviewing Quality → Score: 0.85
⚡ Zeus (The Conductor) → Finalizing → Constructing response
```

### Document-Attached Queries

When you attach a document to your conversation:

```
⚡ Zeus (The Conductor) → Routing to Daedalus → Documents attached
🏛️ Daedalus (The Architect) → Activating → Processing 1 document(s)
🔥 Prometheus (The Illuminator) → Extracting → Reading document content
📚 Hypatia (The Scholar) → Analyzing → Semantic analysis
🧠 Mnemosyne (The Keeper) → Extracting → Key insights
```

---

## ✅ Verification Checklist

| Service | URL | Expected |
|---------|-----|----------|
| Frontend | http://localhost:5173 | Vantage UI |
| Backend API | http://localhost:8000 | API docs |
| OpenSearch | http://localhost:9200 | JSON response |
| Ollama | http://localhost:11434 | "Ollama is running" |

---

## 🛠️ Common Issues

### "OpenSearch connection refused"
```bash
# Check if container is running
docker ps | grep opensearch
# Restart if needed
docker-compose restart
```

### "Ollama model not found"
```bash
ollama pull nomic-embed-text
ollama pull qwen2.5:7b
```

### "Cannot connect to backend"
```bash
# Check backend logs
python -m backend.api
# Look for error messages
```

### "Frontend not loading"
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
npm run dev
```

---

## 🎓 Next Steps

1. **Read the [Architecture Guide](ARCHITECTURE.md)** to understand the system deeply
2. **Configure `config.yaml`** to customize search parameters
3. **Enable file watcher** to auto-index new documents
4. **Explore conversation memory** for contextual follow-up queries

---

**🎉 You're all set! Start searching with Vantage!**
