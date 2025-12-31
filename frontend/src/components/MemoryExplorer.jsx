import React, { useState, useEffect } from 'react';
import './MemoryExplorer.css';

const MemoryExplorer = ({ userId }) => {
    const [memories, setMemories] = useState([]);
    const [loading, setLoading] = useState(false);
    const [searchQuery, setSearchQuery] = useState('');
    const [selectedType, setSelectedType] = useState('all');
    const [commandInput, setCommandInput] = useState('');
    const [commandResult, setCommandResult] = useState(null);

    const fetchMemories = async (query = '') => {
        setLoading(true);
        try {
            const url = query
                ? `/api/memory/search?query=${encodeURIComponent(query)}&user_id=${userId}`
                : `/api/memory/list?user_id=${userId}&limit=50`;
            const response = await fetch(url);
            if (response.ok) {
                const data = await response.json();
                setMemories(data.memories || data);
            }
        } catch (err) {
            console.error('Failed to fetch memories:', err);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        if (userId) fetchMemories();
    }, [userId]);

    const handleSearch = (e) => {
        e.preventDefault();
        fetchMemories(searchQuery);
    };

    const handleCommand = async (e) => {
        e.preventDefault();
        if (!commandInput.trim()) return;

        try {
            const response = await fetch('/api/memory/command', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ command: commandInput, user_id: userId })
            });
            const result = await response.json();
            setCommandResult(result);
            if (result.success) {
                fetchMemories();
                setCommandInput('');
            }
        } catch (err) {
            setCommandResult({ success: false, message: err.message });
        }
    };

    const filteredMemories = selectedType === 'all'
        ? memories
        : memories.filter(m => m.note_type === selectedType);

    return (
        <div className="memory-explorer">
            <div className="explorer-header">
                <h3>Memory Explorer</h3>

                <form onSubmit={handleSearch} className="search-form">
                    <input
                        type="text"
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        placeholder="Search memories..."
                        className="search-input"
                    />
                    <button type="submit" className="search-btn">🔍</button>
                </form>

                <div className="type-filter">
                    {['all', 'insight', 'query', 'document', 'code'].map(type => (
                        <button
                            key={type}
                            className={`filter-btn ${selectedType === type ? 'active' : ''}`}
                            onClick={() => setSelectedType(type)}
                        >
                            {type}
                        </button>
                    ))}
                </div>
            </div>

            <form onSubmit={handleCommand} className="command-form">
                <input
                    type="text"
                    value={commandInput}
                    onChange={(e) => setCommandInput(e.target.value)}
                    placeholder="Natural language command (e.g., 'remember that...', 'forget about...')"
                    className="command-input"
                />
                <button type="submit" className="command-btn">Execute</button>
            </form>

            {commandResult && (
                <div className={`command-result ${commandResult.success ? 'success' : 'error'}`}>
                    {commandResult.message}
                </div>
            )}

            <div className="memories-list">
                {loading ? (
                    <div className="loading">Loading memories...</div>
                ) : filteredMemories.length === 0 ? (
                    <div className="empty">No memories found</div>
                ) : (
                    filteredMemories.map(memory => (
                        <div key={memory.id} className="memory-card">
                            <div className="memory-header">
                                <span className={`type-badge ${memory.note_type}`}>{memory.note_type}</span>
                                <span className="importance">
                                    {'★'.repeat(Math.round((memory.importance || 0.5) * 5))}
                                </span>
                            </div>
                            <p className="memory-content">{memory.content?.substring(0, 200)}...</p>
                            <div className="memory-footer">
                                <span className="keywords">{memory.keywords?.slice(0, 3).join(', ')}</span>
                                <span className="links">{memory.links?.length || 0} links</span>
                            </div>
                        </div>
                    ))
                )}
            </div>
        </div>
    );
};

export default MemoryExplorer;
