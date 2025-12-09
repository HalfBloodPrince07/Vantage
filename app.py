# app.py - Modern Gemini-like Interface for LocalLens

import streamlit as st
import httpx
import asyncio
import yaml
from pathlib import Path
from typing import List, Dict, Any, Optional
import time
import subprocess
import platform
import json
import uuid

# Page Configuration - Must be first
st.set_page_config(
    page_title="LocalLens",
    page_icon="✨",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Load Configuration
with open("config.yaml", "r", encoding="utf-8") as f:
    config = yaml.safe_load(f)

# --- CSS STYLING (Gemini-like) ---
st.markdown("""
<style>
    /* Global Font & Colors */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    /* Main Container */
    .main {
        background-color: #ffffff;
    }
    
    /* Chat Input Styling */
    .stChatInput {
        position: fixed;
        bottom: 30px;
        padding-bottom: 0px;
        left: 50%;
        transform: translateX(-40%); /* Offset for sidebar */
        width: 60%;
        max-width: 900px;
        z-index: 100;
    }
    
    .stChatInput textarea {
        border-radius: 24px;
        border: 1px solid #e0e0e0;
        padding: 12px 20px;
        background-color: #f8f9fa;
        color: #1f1f1f;
        font-size: 16px;
    }
    
    .stChatInput textarea:focus {
        border-color: #4285f4;
        box-shadow: 0 0 0 2px rgba(66, 133, 244, 0.2);
    }

    /* Message Bubbles */
    .stChatMessage {
        background-color: transparent;
        border: none;
    }

    /* User Message */
    .stChatMessage[data-testid="stChatMessage"]:nth-child(odd) {
        background-color: transparent;
    }

    /* Thinking Process Expander */
    .streamlit-expanderHeader {
        background-color: #f0f4f9;
        border-radius: 12px;
        font-size: 14px;
        color: #444746;
        border: none;
    }
    
    .streamlit-expanderContent {
        background-color: #f8f9fa;
        border-radius: 0 0 12px 12px;
        border: none;
        padding: 16px;
        font-size: 13px;
    }

    /* Cards for Results */
    .result-card {
        background-color: #ffffff;
        border: 1px solid #e0e0e0;
        border-radius: 12px;
        padding: 16px;
        margin-bottom: 12px;
        transition: transform 0.2s, box-shadow 0.2s;
    }
    
    .result-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
        border-color: #4285f4;
    }

    .result-title {
        color: #1f1f1f;
        font-weight: 600;
        font-size: 15px;
        margin-bottom: 4px;
        text-decoration: none;
    }

    .result-meta {
        font-size: 12px;
        color: #757575;
        margin-bottom: 8px;
        display: flex;
        gap: 10px;
        align-items: center;
    }

    .score-badge {
        background-color: #e8f0fe;
        color: #1967d2;
        padding: 2px 8px;
        border-radius: 12px;
        font-weight: 500;
    }

    .result-snippet {
        color: #444746;
        font-size: 14px;
        line-height: 1.5;
    }

    /* Agent Steps Visualization */
    .step-item {
        display: flex;
        gap: 12px;
        margin-bottom: 12px;
        align-items: flex-start;
    }
    
    .step-icon {
        background: #e3e3e3;
        width: 24px;
        height: 24px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 12px;
        flex-shrink: 0;
    }
    
    .step-content {
        flex: 1;
    }
    
    .step-title {
        font-weight: 600;
        font-size: 13px;
        color: #1f1f1f;
    }
    
    .step-desc {
        font-size: 12px;
        color: #757575;
    }

    /* Custom Header */
    h1 {
        background: -webkit-linear-gradient(45deg, #4285f4, #9b72cb);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 700 !important;
    }
    
    /* Hide Sidebar Default */
    section[data-testid="stSidebar"] {
        background-color: #f8f9fa;
        border-right: 1px solid #e0e0e0;
    }
</style>
""", unsafe_allow_html=True)

# API Client
class LocalLensAPI:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
    
    async def search_enhanced(
        self,
        query: str,
        top_k: int = 5,
        use_hybrid: bool = True,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                response = await client.post(
                    f"{self.base_url}/search/enhanced",
                    json={
                        "query": query,
                        "top_k": top_k,
                        "use_hybrid": use_hybrid,
                        "session_id": session_id,
                        "user_id": user_id
                    }
                )
                return response.json()
            except Exception as e:
                return {"status": "error", "message": str(e)}

    async def start_indexing(self, directory: str, watch_mode: bool = False) -> Dict[str, Any]:
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.post(
                    f"{self.base_url}/index",
                    json={"directory": directory, "watch_mode": watch_mode}
                )
                return response.json()
            except Exception as e:
                return {"status": "error", "message": str(e)}

api = LocalLensAPI()

# Session State Init
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'session_id' not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())[:16]
if 'user_id' not in st.session_state:
    st.session_state.user_id = "user_1"
if 'use_hybrid' not in st.session_state:
    st.session_state.use_hybrid = True  # Default to hybrid search enabled
if 'top_k' not in st.session_state:
    st.session_state.top_k = 5

# --- SIDEBAR (Settings) ---
with st.sidebar:
    st.header("⚙️ Settings")
    
    # Statistics Section
    st.markdown("### 📊 Statistics")
    stats_container = st.container()
    with stats_container:
        try:
            stats_response = httpx.get(f"{api.base_url}/stats", timeout=5.0)
            if stats_response.status_code == 200:
                stats = stats_response.json()
                col1, col2 = st.columns(2)
                with col1:
                    st.metric(
                        label="Documents",
                        value=stats.get("total_documents", 0),
                        help="Total indexed documents"
                    )
                with col2:
                    avg_time = stats.get("avg_search_time", 0)
                    st.metric(
                        label="Avg Search",
                        value=f"{avg_time:.2f}s",
                        help="Average search time"
                    )
            else:
                st.caption("📊 Stats unavailable")
        except Exception as e:
            st.caption("📊 Stats unavailable")
    
    st.divider()
    
    # Search Settings
    with st.expander("🔍 Search Settings"):
        st.session_state.use_hybrid = st.checkbox(
            "Enable Hybrid Search",
            value=st.session_state.use_hybrid,
            help="Combines semantic (vector) search with keyword (BM25) search"
        )
        
        st.session_state.top_k = st.slider(
            "Results to Show",
            min_value=1,
            max_value=20,
            value=st.session_state.top_k,
            help="Number of results to display"
        )
        
        search_mode = "Hybrid" if st.session_state.use_hybrid else "Vector-only"
        st.caption(f"🔎 {search_mode} • Top {st.session_state.top_k}")
    
    st.divider()
    
    # Document Indexing
    with st.expander("📁 Index Documents", expanded=False):
        target_dir = st.text_input(
            "Directory Path",
            value=str(Path.home() / "Documents"),
            help="Path to directory containing documents to index"
        )
        
        watch_files = st.checkbox(
            "📡 Watch for changes",
            value=False,
            help="Monitor directory and auto-reindex on file changes"
        )
        
        if st.button("🚀 Start Indexing", use_container_width=True, type="primary"):
            with st.spinner("Indexing documents..."):
                res = asyncio.run(api.start_indexing(target_dir, watch_mode=watch_files))
                if res.get("status") == "success":
                    msg = "✅ " + res.get("message", "Indexing started")
                    if watch_files:
                        msg += " 👁️ Watcher active"
                    st.success(msg)
                else:
                    st.error(f"❌ {res.get('message', 'Indexing failed')}")
    
    st.divider()
    
    # Session Management
    st.caption(f"**Session:** `{st.session_state.session_id}`")
    if st.button("🔄 New Session", use_container_width=True):
        st.session_state.session_id = str(uuid.uuid4())[:16]
        st.session_state.messages = []
        st.rerun()

# --- MAIN INTERFACE ---

st.title("LocalLens")
st.caption("Ask questions about your documents")

# Welcome Message
if len(st.session_state.messages) == 0:
    st.markdown("""
    <div style="text-align: center; margin-top: 50px; color: #757575;">
        <h3>How can I help you today?</h3>
        <p>I can find documents, summarize content, or answer questions based on your files.</p>
    </div>
    """, unsafe_allow_html=True)

# Display Chat History
for msg in st.session_state.messages:
    with st.chat_message(msg["role"], avatar="🧑‍💻" if msg["role"] == "user" else "✨"):
        if msg["role"] == "assistant":
            # 1. Show Thinking Process (if available)
            if "steps" in msg and msg["steps"]:
                with st.expander("✨ Thought Process", expanded=False):
                    for step in msg["steps"]:
                        icon = "🧠"
                        if "Search" in step.get('agent', ''): icon = "🔍"
                        elif "Summariz" in step.get('agent', ''): icon = "📝"
                        elif "Critic" in step.get('agent', ''): icon = "⚖️"
                        elif "Clarif" in step.get('agent', ''): icon = "🤔"
                        elif "Classif" in step.get('agent', ''): icon = "🧭"
                        
                        st.markdown(f"""
                        <div class="step-item">
                            <div class="step-icon">{icon}</div>
                            <div class="step-content">
                                <div class="step-title">{step.get('action', 'Action')}</div>
                                <div class="step-desc">{step.get('details', '')}</div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)

            # 2. Show Main Content
            st.markdown(msg["content"])

            # 3. Show Document Cards (if available)
            if "results" in msg and msg["results"]:
                for res in msg["results"]:
                    score = res.get('score', 0)
                    file_path = res.get('file_path', 'Unknown path')
                    summary = res.get('content_summary', '') or "No summary available"
                    
                    st.markdown(f"""
                    <div class="result-card">
                        <div class="result-header">
                            <span class="result-title">📄 {res.get('filename', 'Document')}</span>
                        </div>
                        <div class="result-meta">
                            <span class="score-badge">Match: {int(score * 100)}%</span>
                            <span>{file_path}</span>
                        </div>
                        <div class="result-snippet">
                            {summary[:200]}...
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # File Open Button Logic
                    # Using columns to position button
                    col1, col2 = st.columns([1, 5])
                    with col1:
                        # Use a stable key based on message ID and file path hash
                        btn_key = f"open_{hash(file_path)}_{msg.get('id', 0)}"
                        if st.button("Open", key=btn_key):
                            try:
                                if platform.system() == 'Windows':
                                    subprocess.Popen(['start', file_path], shell=True)
                                elif platform.system() == 'Darwin':
                                    subprocess.Popen(['open', file_path])
                                else:
                                    subprocess.Popen(['xdg-open', file_path])
                            except Exception as e:
                                st.toast(f"Could not open file: {e}", icon="❌")

        else:
            # User Message
            st.write(msg["content"])

# --- CHAT INPUT & LOGIC ---

if prompt := st.chat_input("Ask about your documents..."):
    # 1. Add User Message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="🧑‍💻"):
        st.write(prompt)

    # 2. Generate Assistant Response
    with st.chat_message("assistant", avatar="✨"):
        # Placeholder for streaming/thinking
        thinking_placeholder = st.empty()
        
        with thinking_placeholder.container():
            st.markdown("`Thinking...`")
            progress_bar = st.progress(0)
            
            # Simulate "real-time" feel while waiting for backend
            for i in range(1, 90):
                time.sleep(0.01)
                progress_bar.progress(i)

        # Call Backend
        response = asyncio.run(api.search_enhanced(
            query=prompt,
            top_k=st.session_state.top_k,
            use_hybrid=st.session_state.use_hybrid,
            session_id=st.session_state.session_id,
            user_id=st.session_state.user_id
        ))
        
        # Clear loading state
        thinking_placeholder.empty()

        if response.get("status") == "success":
            # Extract data
            message_text = response.get("response_message", "Here are the results.")
            steps = response.get("steps", []) # From backend update
            results = response.get("results", [])
            
            # Save to history
            st.session_state.messages.append({
                "role": "assistant",
                "content": message_text,
                "steps": steps,
                "results": results,
                "id": time.time()
            })
            
            # Rerender to show the full styled message
            st.rerun()
            
        else:
            st.error(f"Error: {response.get('message', 'Unknown error')}")