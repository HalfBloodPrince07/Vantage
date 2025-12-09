// Vanilla JavaScript Example for SSE Step Streaming
// Add this to your existing frontend code

// Example usage in your search function
async function searchWithSteps(query) {
    const sessionId = `session_${Date.now()}`;

    // 1. Connect to SSE stream to see steps in real-time
    const eventSource = new EventSource(`http://localhost:8000/search/enhanced/stream/${sessionId}`);

    // Container for displaying steps
    const stepsContainer = document.getElementById('thinking-steps');
    stepsContainer.innerHTML = '<h3>🤖 Thinking...</h3>';

    eventSource.onmessage = (event) => {
        const data = JSON.parse(event.data);

        if (data.type === 'step') {
            // Display step: [Memory] Loading Context: Retrieving session history
            const stepDiv = document.createElement('div');
            stepDiv.className = 'step-item';
            stepDiv.textContent = data.message;
            stepsContainer.appendChild(stepDiv);
        } else if (data.type === 'complete') {
            eventSource.close();
            stepsContainer.innerHTML += '<p>✅ Complete!</p>';
        } else if (data.type === 'error') {
            console.error('Stream error:', data.message);
            eventSource.close();
        }
    };

    // 2. Start the search
    const response = await fetch('http://localhost:8000/search/enhanced', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            query: query,
            session_id: sessionId,
            user_id: 'user_1',
            top_k: 5
        })
    });

    const result = await response.json();

    // 3. Display results
    displayResults(result.results);

    return result;
}

// Add CSS for step animations
const styleSheet = document.createElement('style');
styleSheet.textContent = `
  #thinking-steps {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    padding: 20px;
    border-radius: 12px;
    margin: 20px 0;
    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
  }

  #thinking-steps h3 {
    margin: 0 0 15px 0;
    font-size: 18px;
  }

  .step-item {
    font-family: 'Monaco', 'Courier New', monospace;
    font-size: 13px;
    padding: 8px 12px;
    margin: 6px 0;
    background: rgba(255,255,255,0.1);
    border-left: 3px solid rgba(255,255,255,0.5);
    border-radius: 4px;
    opacity: 0;
    transform: translateX(-20px);
    animation: slideIn 0.3s forwards;
  }

  @keyframes slideIn {
    to {
      opacity: 1;
      transform: translateX(0);
    }
  }
`;
document.head.appendChild(styleSheet);

// HTML structure (add to your page)
/*
<div id="search-container">
  <input type="text" id="search-input" placeholder="Ask about your documents...">
  <button onclick="searchWithSteps(document.getElementById('search-input').value)">
    Search
  </button>
  
  <div id="thinking-steps"></div>
  <div id="results"></div>
</div>
*/
