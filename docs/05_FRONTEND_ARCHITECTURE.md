# VANTAGE - Frontend Architecture (Deep Dive)

## Table of Contents
- [Frontend Overview](#frontend-overview)
- [Component Architecture](#component-architecture)
- [State Management](#state-management)
- [Real-time Communication (SSE)](#real-time-communication-sse)
- [Component Details](#component-details)
- [Styling & Theming](#styling--theming)
- [Performance Optimizations](#performance-optimizations)

---

## Frontend Overview

The Vantage frontend is a **React 18-based single-page application** built with Vite for fast development and optimized production builds. It provides an interactive interface for document search, knowledge graph visualization, memory exploration, and conversational AI interaction.

### Technology Stack

```
┌─────────────────────────────────────────────────────────────────────┐
│                      FRONTEND TECH STACK                             │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  Core Framework:                                                     │
│    • React 18.2.0          (UI library)                              │
│    • React-DOM 18.2.0      (DOM rendering)                           │
│                                                                       │
│  Build Tool:                                                         │
│    • Vite 5.0.8            (Dev server & bundler)                    │
│    • ESBuild               (Fast transpilation)                      │
│    • Rollup                (Production bundling)                     │
│                                                                       │
│  Visualization:                                                      │
│    • React Force Graph 2D 1.29.0  (Knowledge graph)                  │
│    • D3.js (via force-graph)       (Graph rendering)                 │
│                                                                       │
│  Content Rendering:                                                  │
│    • React Markdown 9.1.0  (Markdown → React)                        │
│    • Remark/Rehype plugins (Syntax highlighting, etc.)               │
│                                                                       │
│  Styling:                                                            │
│    • CSS3 (Vanilla CSS)    (No CSS-in-JS)                            │
│    • CSS Modules           (Component-scoped styles)                 │
│    • CSS Variables         (Theming)                                 │
│                                                                       │
│  State Management:                                                   │
│    • React Hooks           (useState, useEffect, useContext)         │
│    • Custom Hooks          (useDarkMode, useKeyboardShortcuts)       │
│                                                                       │
│  HTTP Client:                                                        │
│    • Fetch API             (Native browser API)                      │
│    • EventSource           (Server-Sent Events)                      │
│                                                                       │
│  Development Tools:                                                  │
│    • ESLint 8.55.0         (Linting)                                 │
│    • Vite HMR              (Hot Module Replacement)                  │
└─────────────────────────────────────────────────────────────────────┘
```

### Directory Structure

```
frontend/
│
├── public/                         # Static assets
│   └── vite.svg                    # Favicon
│
├── src/
│   ├── App.jsx                     # Root component
│   ├── main.jsx                    # Entry point
│   ├── index.css                   # Global styles
│   │
│   ├── components/                 # React components
│   │   ├── ChatInterface.jsx       # Main chat UI
│   │   ├── ChatInterface.css
│   │   ├── ChatSidebar.jsx         # Conversation list
│   │   ├── DocumentSelector.jsx    # Document attachment
│   │   ├── EntityGraphModal.jsx    # Knowledge graph modal
│   │   ├── AgentThinkingCinematic.jsx # Agent visualization
│   │   ├── ConfidenceGraph.jsx     # Confidence visualization
│   │   ├── IndexingProgress.jsx    # Indexing progress bar
│   │   ├── OnboardingWizard.jsx    # First-time setup
│   │   ├── SettingsPanel.jsx       # Settings UI
│   │   ├── LoginSettings.jsx       # Authentication
│   │   ├── MemoryExplorer.jsx      # Memory system UI
│   │   ├── MemoryGraph.jsx         # Memory graph viz
│   │   ├── MemoryInsights.jsx      # Memory insights
│   │   ├── MemoryStats.jsx         # Memory statistics
│   │   ├── FeaturesShowcase.jsx    # Landing page
│   │   ├── CreatorBadge.jsx        # Attribution
│   │   ├── AIAgentAvatar.jsx       # Agent avatar
│   │   ├── AmbientParticles.jsx    # Background animation
│   │   └── index.js                # Component exports
│   │
│   ├── hooks/                      # Custom React hooks
│   │   ├── useDarkMode.jsx         # Dark mode toggle
│   │   ├── useKeyboardShortcuts.jsx # Keyboard shortcuts
│   │   └── index.js
│   │
│   └── styles/                     # Style files
│       ├── dark-mode.css           # Dark theme
│       └── ai-dashboard.css        # Dashboard styles
│
├── index.html                      # Main HTML entry
├── chat.html                       # Chat-only page
├── package.json                    # Dependencies
├── vite.config.js                  # Vite configuration
└── .eslintrc.cjs                   # ESLint config
```

---

## Component Architecture

### Component Hierarchy

```
┌─────────────────────────────────────────────────────────────────────┐
│                      COMPONENT TREE                                  │
└─────────────────────────────────────────────────────────────────────┘

App.jsx (Root)
│
├─ FeaturesShowcase.jsx             (Landing page - conditional)
│   ├─ CreatorBadge.jsx
│   ├─ AmbientParticles.jsx
│   └─ Interactive demo cards
│
└─ ChatInterface.jsx                (Main application)
    │
    ├─ ChatSidebar.jsx              (Left sidebar)
    │   ├─ Conversation list
    │   ├─ New conversation button
    │   └─ Conversation management
    │
    ├─ Message Display Area         (Center)
    │   ├─ Message bubbles
    │   │   ├─ User messages
    │   │   ├─ Assistant messages
    │   │   │   ├─ React Markdown renderer
    │   │   │   ├─ Source citations
    │   │   │   └─ Confidence badge
    │   │   └─ System messages
    │   │
    │   ├─ AgentThinkingCinematic.jsx (During processing)
    │   │   ├─ Thinking steps timeline
    │   │   ├─ Agent avatars
    │   │   └─ Progress indicators
    │   │
    │   └─ IndexingProgress.jsx     (During indexing)
    │       ├─ Progress bar
    │       ├─ File list
    │       └─ Status messages
    │
    ├─ Input Area                   (Bottom)
    │   ├─ DocumentSelector.jsx     (Attachment button)
    │   │   ├─ Document picker
    │   │   └─ Selected docs display
    │   │
    │   ├─ Text input field
    │   └─ Send button
    │
    ├─ EntityGraphModal.jsx         (Modal overlay)
    │   └─ React Force Graph 2D
    │       ├─ Node rendering
    │       ├─ Link rendering
    │       └─ Zoom/pan controls
    │
    ├─ MemoryExplorer.jsx           (Modal overlay)
    │   ├─ MemoryGraph.jsx
    │   ├─ MemoryInsights.jsx
    │   └─ MemoryStats.jsx
    │
    ├─ SettingsPanel.jsx            (Slide-out panel)
    │   ├─ Preferences
    │   ├─ Theme toggle
    │   ├─ Keyboard shortcuts
    │   └─ System info
    │
    ├─ LoginSettings.jsx            (Modal overlay)
    │   ├─ Login form
    │   └─ Register form
    │
    └─ OnboardingWizard.jsx         (First-time modal)
        ├─ Step 1: Welcome
        ├─ Step 2: Select documents
        ├─ Step 3: Indexing
        └─ Step 4: Ready
```

### Component Communication

```
┌─────────────────────────────────────────────────────────────────────┐
│                   COMPONENT DATA FLOW                                │
└─────────────────────────────────────────────────────────────────────┘

User Input (ChatInterface)
    ↓
    • Query text
    • Attached documents
    ↓
POST /search (Fetch API)
    ↓
    ┌─────────────────────────────────────────┐
    │      SSE Stream (EventSource)            │
    │                                          │
    │  Event: "thinking_step"                  │
    │    → Update AgentThinkingCinematic       │
    │                                          │
    │  Event: "search_results"                 │
    │    → Update message with results         │
    │                                          │
    │  Event: "response_chunk"                 │
    │    → Append to message (streaming)       │
    │                                          │
    │  Event: "confidence_score"               │
    │    → Update ConfidenceGraph              │
    │                                          │
    │  Event: "complete"                       │
    │    → Finalize message                    │
    │    → Update conversation list            │
    └─────────────────────────────────────────┘
    ↓
State Update (React useState)
    ↓
Re-render Components
```

---

## State Management

### Global State (App.jsx)

```javascript
const [darkMode, setDarkMode] = useState(false);
const [currentUser, setCurrentUser] = useState(null);
const [showOnboarding, setShowOnboarding] = useState(true);
```

### ChatInterface State

```javascript
// Conversation state
const [conversations, setConversations] = useState([]);
const [currentConversationId, setCurrentConversationId] = useState(null);
const [messages, setMessages] = useState([]);

// Input state
const [inputValue, setInputValue] = useState('');
const [attachedDocuments, setAttachedDocuments] = useState([]);

// UI state
const [isLoading, setIsLoading] = useState(false);
const [showGraph, setShowGraph] = useState(false);
const [showMemory, setShowMemory] = useState(false);
const [showSettings, setShowSettings] = useState(false);

// Agent thinking state
const [thinkingSteps, setThinkingSteps] = useState([]);
const [currentAgent, setCurrentAgent] = useState(null);

// Indexing state
const [isIndexing, setIsIndexing] = useState(false);
const [indexingProgress, setIndexingProgress] = useState(null);

// Session state
const [sessionId, setSessionId] = useState(null);
```

### State Update Patterns

```javascript
// Example: Adding a new message
const addMessage = (message) => {
  setMessages(prev => [...prev, message]);
};

// Example: Updating a streaming message
const updateLastMessage = (content) => {
  setMessages(prev => {
    const updated = [...prev];
    updated[updated.length - 1].content += content;
    return updated;
  });
};

// Example: Adding thinking step
const addThinkingStep = (step) => {
  setThinkingSteps(prev => [...prev, step]);
};
```

---

## Real-time Communication (SSE)

### Server-Sent Events Implementation

```javascript
// ============================
// SSE CONNECTION MANAGEMENT
// ============================

function streamSearch(query, attachedDocs, sessionId) {
  // Create EventSource for SSE
  const eventSource = new EventSource(
    `/stream-search-steps?query=${encodeURIComponent(query)}&session_id=${sessionId}`
  );

  // Handle different event types
  eventSource.addEventListener('thinking_step', (event) => {
    const step = JSON.parse(event.data);
    addThinkingStep({
      agent: step.agent,
      action: step.action,
      timestamp: new Date()
    });
  });

  eventSource.addEventListener('search_results', (event) => {
    const results = JSON.parse(event.data);
    setSearchResults(results);
  });

  eventSource.addEventListener('response_chunk', (event) => {
    const chunk = event.data;
    updateLastMessage(chunk);
  });

  eventSource.addEventListener('confidence_score', (event) => {
    const score = parseFloat(event.data);
    setConfidenceScore(score);
  });

  eventSource.addEventListener('graph_data', (event) => {
    const graphData = JSON.parse(event.data);
    setGraphData(graphData);
  });

  eventSource.addEventListener('complete', (event) => {
    const finalData = JSON.parse(event.data);
    finalizeMessage(finalData);
    eventSource.close();
  });

  eventSource.addEventListener('error', (event) => {
    console.error('SSE error:', event);
    eventSource.close();
    handleError('Connection lost');
  });

  // Cleanup on component unmount
  return () => {
    eventSource.close();
  };
}
```

### SSE Event Types

| Event Type | Payload | Purpose |
|------------|---------|---------|
| `thinking_step` | `{ agent, action, timestamp }` | Show agent activity |
| `search_results` | `{ results: [...] }` | Display search results |
| `response_chunk` | `string` | Stream response text |
| `confidence_score` | `float` | Update confidence UI |
| `graph_data` | `{ nodes, links }` | Populate knowledge graph |
| `memory_update` | `{ note, ... }` | Show memory changes |
| `complete` | `{ response, metadata }` | Finalize message |
| `error` | `{ error, message }` | Handle errors |

---

## Component Details

### ChatInterface.jsx

**Purpose**: Main chat interface and application container

```
┌─────────────────────────────────────────────────────────────────────┐
│                          CHAT INTERFACE                              │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  Layout (3-column):                                                  │
│                                                                       │
│  ┌────────────┬─────────────────────────────────┬────────────────┐  │
│  │            │                                  │                │  │
│  │  Sidebar   │      Message Display            │  (Optional)    │  │
│  │            │                                  │  Memory/Graph  │  │
│  │  • Conv    │  ┌────────────────────────────┐ │                │  │
│  │    List    │  │ User: "What is ML?"        │ │                │  │
│  │  • New     │  └────────────────────────────┘ │                │  │
│  │    Conv    │                                  │                │  │
│  │  • Search  │  ┌────────────────────────────┐ │                │  │
│  │  • Settings│  │ Assistant: "Machine        │ │                │  │
│  │            │  │ learning is..."            │ │                │  │
│  │            │  │                             │ │                │  │
│  │            │  │ Sources: [Doc1] [Doc2]     │ │                │  │
│  │            │  │ Confidence: ■■■■■□ 0.87    │ │                │  │
│  │            │  └────────────────────────────┘ │                │  │
│  │            │                                  │                │  │
│  │            │  ┌────────────────────────────┐ │                │  │
│  │            │  │ Agent Thinking:            │ │                │  │
│  │            │  │ [Athena] Classifying...    │ │                │  │
│  │            │  │ [Search] Retrieving...     │ │                │  │
│  │            │  └────────────────────────────┘ │                │  │
│  │            │                                  │                │  │
│  │            ├──────────────────────────────────┤                │  │
│  │            │ [📎] [Input field...] [Send]   │                │  │
│  │            └──────────────────────────────────┘                │  │
│  └────────────┴─────────────────────────────────┴────────────────┘  │
│                                                                       │
│  Features:                                                           │
│    • Message streaming (SSE)                                         │
│    • Markdown rendering (code blocks, tables, lists)                 │
│    • Document attachment                                             │
│    • Conversation persistence                                        │
│    • Export (Markdown, JSON)                                         │
│    • Keyboard shortcuts (Ctrl+K, Ctrl+N, Ctrl+Enter)                │
│    • Auto-scroll to latest message                                   │
│    • Message feedback (thumbs up/down)                               │
└─────────────────────────────────────────────────────────────────────┘
```

### EntityGraphModal.jsx

**Purpose**: Interactive knowledge graph visualization

```
┌─────────────────────────────────────────────────────────────────────┐
│                      KNOWLEDGE GRAPH MODAL                           │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  Components:                                                         │
│    • React Force Graph 2D (graph rendering)                          │
│    • D3 force simulation (physics engine)                            │
│    • Custom node/link renderers                                      │
│                                                                       │
│  Graph Structure:                                                    │
│    {                                                                 │
│      nodes: [                                                        │
│        { id: "node1", name: "GPT-4", type: "CONCEPT", ... },         │
│        { id: "node2", name: "OpenAI", type: "ORGANIZATION", ... }    │
│      ],                                                              │
│      links: [                                                        │
│        { source: "node1", target: "node2", type: "CREATED_BY" }      │
│      ]                                                               │
│    }                                                                 │
│                                                                       │
│  Node Styling:                                                       │
│    • PERSON: Blue circle                                             │
│    • ORGANIZATION: Green square                                      │
│    • LOCATION: Red triangle                                          │
│    • CONCEPT: Purple hexagon                                         │
│    • DOCUMENT: Orange rectangle                                      │
│                                                                       │
│  Interactions:                                                       │
│    • Click node → Show details                                       │
│    • Hover node → Highlight connections                              │
│    • Drag node → Reposition                                          │
│    • Zoom/Pan → Navigate graph                                       │
│    • Double-click node → Expand related nodes                        │
│                                                                       │
│  Features:                                                           │
│    • Physics simulation (force-directed layout)                      │
│    • Dynamic node sizing (based on importance)                       │
│    • Link strength visualization (thickness)                         │
│    • Filtering by entity type                                        │
│    • Search nodes                                                    │
│    • Export as PNG                                                   │
└─────────────────────────────────────────────────────────────────────┘
```

### AgentThinkingCinematic.jsx

**Purpose**: Visualize agent workflow in real-time

```
┌─────────────────────────────────────────────────────────────────────┐
│                   AGENT THINKING VISUALIZATION                       │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  Timeline View:                                                      │
│                                                                       │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │  [Athena Avatar]  Classifying query intent...        ✓ 0.2s   │ │
│  │  [Proteus Avatar] Searching documents...             ✓ 0.8s   │ │
│  │  [Reranker Icon]  Reranking results...               ✓ 0.3s   │ │
│  │  [Apollo Avatar]  Expanding graph context...         ✓ 0.4s   │ │
│  │  [Qwen Icon]      Generating response...             ⏳ 2.1s   │ │
│  │  [Themis Avatar]  Calculating confidence...          ⏸ Pending│ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                       │
│  Agent Avatars:                                                      │
│    • Each agent has unique icon/color                                │
│    • Animated while in progress                                      │
│    • Checkmark when complete                                         │
│                                                                       │
│  Step States:                                                        │
│    • Pending: Gray, waiting                                          │
│    • In Progress: Animated, pulsing                                  │
│    • Complete: Green checkmark, duration shown                       │
│    • Failed: Red X, error message                                    │
│                                                                       │
│  Features:                                                           │
│    • Real-time step updates (via SSE)                                │
│    • Elapsed time per step                                           │
│    • Collapsible/expandable                                          │
│    • Step details on hover                                           │
└─────────────────────────────────────────────────────────────────────┘
```

### MemoryExplorer.jsx

**Purpose**: Explore and visualize memory system

```
┌─────────────────────────────────────────────────────────────────────┐
│                        MEMORY EXPLORER                               │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  Tabs:                                                               │
│    1. Memory Graph (MemoryGraph.jsx)                                 │
│       • Interactive graph of memory notes                            │
│       • Similar to EntityGraphModal                                  │
│       • Color-coded by note type                                     │
│                                                                       │
│    2. Memory Insights (MemoryInsights.jsx)                           │
│       • Key learnings summary                                        │
│       • Recent insights                                              │
│       • Suggested topics                                             │
│                                                                       │
│    3. Memory Stats (MemoryStats.jsx)                                 │
│       • Total notes: 1,245                                           │
│       • Note types breakdown (pie chart)                             │
│       • Access patterns (heatmap)                                    │
│       • Memory consolidation history                                 │
│                                                                       │
│  Features:                                                           │
│    • Natural language memory queries                                 │
│    • Filter by note type, date, importance                           │
│    • Export memory dump                                              │
│    • Manual consolidation trigger                                    │
└─────────────────────────────────────────────────────────────────────┘
```

### DocumentSelector.jsx

**Purpose**: Select and attach documents to queries

```
┌─────────────────────────────────────────────────────────────────────┐
│                       DOCUMENT SELECTOR                              │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  Modal Layout:                                                       │
│                                                                       │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │  Search documents: [input field...] 🔍                          │ │
│  ├────────────────────────────────────────────────────────────────┤ │
│  │  Filters: [All] [PDFs] [Docs] [Images]                          │ │
│  ├────────────────────────────────────────────────────────────────┤ │
│  │                                                                  │ │
│  │  ☐ research_paper_1.pdf        ML Research      2024-01-10     │ │
│  │  ☑ neural_networks.docx        Tutorial         2024-01-15     │ │
│  │  ☐ architecture_diagram.png    Diagram          2024-01-20     │ │
│  │  ☑ meeting_notes.txt           Notes            2024-01-22     │ │
│  │                                                                  │ │
│  ├────────────────────────────────────────────────────────────────┤ │
│  │  Selected: 2 documents                [Attach] [Cancel]         │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                       │
│  Features:                                                           │
│    • Search by filename/content                                      │
│    • Filter by file type                                             │
│    • Sort by date/name/relevance                                     │
│    • Multi-select with checkboxes                                    │
│    • Document preview on hover                                       │
│    • Recent documents quick select                                   │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Styling & Theming

### Dark Mode Implementation

```css
/* CSS Variables for theming */
:root {
  --bg-primary: #ffffff;
  --bg-secondary: #f5f5f5;
  --text-primary: #000000;
  --text-secondary: #666666;
  --accent: #0066cc;
  --border: #e0e0e0;
}

[data-theme="dark"] {
  --bg-primary: #1a1a1a;
  --bg-secondary: #2d2d2d;
  --text-primary: #ffffff;
  --text-secondary: #b0b0b0;
  --accent: #3399ff;
  --border: #404040;
}

/* Component styles using variables */
.chat-interface {
  background-color: var(--bg-primary);
  color: var(--text-primary);
  border-color: var(--border);
}
```

### useDarkMode Hook

```javascript
function useDarkMode() {
  const [darkMode, setDarkMode] = useState(() => {
    // Load from localStorage
    const saved = localStorage.getItem('darkMode');
    return saved ? JSON.parse(saved) : false;
  });

  useEffect(() => {
    // Apply theme to document
    document.documentElement.setAttribute(
      'data-theme',
      darkMode ? 'dark' : 'light'
    );
    // Save to localStorage
    localStorage.setItem('darkMode', JSON.stringify(darkMode));
  }, [darkMode]);

  return [darkMode, setDarkMode];
}
```

### Responsive Design

```css
/* Mobile-first approach */
.chat-interface {
  display: flex;
  flex-direction: column;
}

/* Tablet */
@media (min-width: 768px) {
  .chat-interface {
    flex-direction: row;
  }
  .sidebar {
    width: 280px;
  }
}

/* Desktop */
@media (min-width: 1024px) {
  .sidebar {
    width: 320px;
  }
  .message-area {
    max-width: 900px;
  }
}
```

---

## Performance Optimizations

### 1. Code Splitting

```javascript
// Lazy load heavy components
const EntityGraphModal = lazy(() => import('./EntityGraphModal'));
const MemoryExplorer = lazy(() => import('./MemoryExplorer'));

// Usage with Suspense
<Suspense fallback={<div>Loading...</div>}>
  {showGraph && <EntityGraphModal />}
</Suspense>
```

### 2. Memoization

```javascript
// Memoize expensive computations
const sortedConversations = useMemo(() => {
  return conversations.sort((a, b) =>
    new Date(b.updated_at) - new Date(a.updated_at)
  );
}, [conversations]);

// Memoize components
const MessageBubble = memo(({ message }) => {
  return <div className="message">{message.content}</div>;
});
```

### 3. Virtual Scrolling (for long message lists)

```javascript
// Use react-window for virtualization
import { FixedSizeList } from 'react-window';

<FixedSizeList
  height={600}
  itemCount={messages.length}
  itemSize={100}
  width="100%"
>
  {({ index, style }) => (
    <div style={style}>
      <MessageBubble message={messages[index]} />
    </div>
  )}
</FixedSizeList>
```

### 4. Debouncing

```javascript
// Debounce search input
const debouncedSearch = useCallback(
  debounce((query) => {
    performSearch(query);
  }, 300),
  []
);

const handleInputChange = (e) => {
  setInputValue(e.target.value);
  debouncedSearch(e.target.value);
};
```

### 5. Optimistic Updates

```javascript
// Update UI immediately, revert on error
const sendMessage = async (message) => {
  const tempId = Date.now();

  // Optimistic update
  addMessage({ id: tempId, content: message, role: 'user' });

  try {
    const response = await fetch('/search', {
      method: 'POST',
      body: JSON.stringify({ query: message })
    });
    // Update with real data
    updateMessage(tempId, await response.json());
  } catch (error) {
    // Revert on error
    removeMessage(tempId);
    showError('Failed to send message');
  }
};
```

---

## Keyboard Shortcuts

**Implementation**: `frontend/src/hooks/useKeyboardShortcuts.jsx`

```javascript
function useKeyboardShortcuts() {
  useEffect(() => {
    const handleKeyDown = (e) => {
      // Ctrl+K: Focus search
      if (e.ctrlKey && e.key === 'k') {
        e.preventDefault();
        document.getElementById('search-input')?.focus();
      }

      // Ctrl+N: New conversation
      if (e.ctrlKey && e.key === 'n') {
        e.preventDefault();
        startNewConversation();
      }

      // Ctrl+Enter: Send message
      if (e.ctrlKey && e.key === 'Enter') {
        e.preventDefault();
        submitMessage();
      }

      // Ctrl+G: Open graph
      if (e.ctrlKey && e.key === 'g') {
        e.preventDefault();
        toggleGraph();
      }

      // Ctrl+M: Open memory
      if (e.ctrlKey && e.key === 'm') {
        e.preventDefault();
        toggleMemory();
      }

      // Escape: Close modals
      if (e.key === 'Escape') {
        closeAllModals();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);
}
```

### Supported Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl+K` | Focus search input |
| `Ctrl+N` | Start new conversation |
| `Ctrl+Enter` | Send message |
| `Ctrl+G` | Toggle knowledge graph |
| `Ctrl+M` | Toggle memory explorer |
| `Ctrl+S` | Open settings |
| `Escape` | Close modals |

---

**Document Version**: 1.0
**Last Updated**: 2025-12-31
**Related Docs**: `01_OVERALL_SYSTEM_ARCHITECTURE.md`
