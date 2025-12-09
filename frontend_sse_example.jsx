// frontend/SearchWithSteps.jsx
// Example React component for real-time step streaming

import React, { useState, useEffect } from 'react';

function SearchWithSteps() {
    const [query, setQuery] = useState('');
    const [steps, setSteps] = useState([]);
    const [results, setResults] = useState([]);
    const [sessionId, setSessionId] = useState('');
    const [searching, setSearching] = useState(false);

    const search = async () => {
        if (!query.trim()) return;

        setSearching(true);
        setSteps([]);
        setResults([]);

        // Generate or use existing session ID
        const sid = sessionId || `session_${Date.now()}`;
        setSessionId(sid);

        // 1. Connect to SSE stream FIRST
        const eventSource = new EventSource(`http://localhost:8000/search/enhanced/stream/${sid}`);

        eventSource.onmessage = (event) => {
            const data = JSON.parse(event.data);

            if (data.type === 'step') {
                // Add step to UI: [Memory] Loading Context: Retrieving session history
                setSteps(prev => [...prev, data.message]);
            } else if (data.type === 'complete') {
                // Search complete
                eventSource.close();
            } else if (data.type === 'error') {
                console.error('Stream error:', data.message);
                eventSource.close();
            }
        };

        eventSource.onerror = () => {
            console.error('SSE connection error');
            eventSource.close();
        };

        // 2. Start the search (will emit steps to the stream)
        try {
            const response = await fetch('http://localhost:8000/search/enhanced', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    query,
                    session_id: sid,
                    user_id: 'user_1',
                    top_k: 5
                })
            });

            const result = await response.json();
            setResults(result.results || []);
            setSearching(false);
        } catch (error) {
            console.error('Search error:', error);
            setSearching(false);
            eventSource.close();
        }
    };

    return (
        <div className="search-container">
            <div className="search-input">
                <input
                    type="text"
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && search()}
                    placeholder="Ask about your documents..."
                />
                <button onClick={search} disabled={searching}>
                    {searching ? 'Searching...' : 'Search'}
                </button>
            </div>

            {/* Real-time Steps Display */}
            {steps.length > 0 && (
                <div className="thinking-steps">
                    <h3>🤖 Thinking...</h3>
                    {steps.map((step, idx) => (
                        <div key={idx} className="step-item">
                            {step}
                        </div>
                    ))}
                </div>
            )}

            {/* Results */}
            {results.length > 0 && (
                <div className="results">
                    <h3>Results ({results.length})</h3>
                    {results.map((result, idx) => (
                        <div key={idx} className="result-item">
                            <h4>{result.filename}</h4>
                            <p>{result.content_summary || result.text}</p>
                            <span>Score: {result.score?.toFixed(3)}</span>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}

// CSS for styling
const styles = `
.thinking-steps {
  background: #f0f0f0;
  padding: 15px;
  border-radius: 8px;
  margin: 15px 0;
}

.step-item {
  font-family: 'Courier New', monospace;
  font-size: 14px;
  color: #333;
  padding: 4px 0;
  opacity: 0;
  animation: fadeIn 0.3s forwards;
}

@keyframes fadeIn {
  to {
    opacity: 1;
  }
}

.result-item {
  border: 1px solid #ddd;
  padding: 15px;
  margin: 10px 0;
  border-radius: 8px;
}
`;

export default SearchWithSteps;
