// Updated LoginSettings with better user management UX
import React, { useState, useEffect } from 'react';
import './LoginSettings.css';

const LoginSettings = ({ onLogin }) => {
    const [userId, setUserId] = useState('');
    const [indexPath, setIndexPath] = useState('');
    const [showSettings, setShowSettings] = useState(false);
    const [recentUsers, setRecentUsers] = useState([]);

    useEffect(() => {
        // Load recent users from localStorage
        const recent = JSON.parse(localStorage.getItem('locallens_recent_users') || '[]');
        setRecentUsers(recent);
    }, []);

    const handleLogin = () => {
        if (userId.trim()) {
            // Save to recent users
            const recent = JSON.parse(localStorage.getItem('locallens_recent_users') || '[]');
            const updated = [userId, ...recent.filter(u => u !== userId)].slice(0, 5);
            localStorage.setItem('locallens_recent_users', JSON.stringify(updated));

            onLogin(userId, indexPath || null);
        }
    };

    const selectRecentUser = (user) => {
        setUserId(user);
    };

    const removeRecentUser = (user, e) => {
        e.stopPropagation();
        const recent = JSON.parse(localStorage.getItem('locallens_recent_users') || '[]');
        const updated = recent.filter(u => u !== user);
        localStorage.setItem('locallens_recent_users', JSON.stringify(updated));
        setRecentUsers(updated);
    };

    const generateRandomUserId = () => {
        const randomId = `user_${Math.floor(Math.random() * 10000).toString().padStart(4, '0')}`;
        setUserId(randomId);
    };

    return (
        <div className="login-overlay">
            <div className="login-container">
                <h1>🔍 LocalLens</h1>
                <p>AI-Powered Document Search</p>

                <div className="login-form">
                    <div className="input-group">
                        <input
                            type="text"
                            placeholder="Enter user ID (e.g., user_001)"
                            value={userId}
                            onChange={(e) => setUserId(e.target.value)}
                            onKeyPress={(e) => e.key === 'Enter' && handleLogin()}
                            className="login-input"
                            autoFocus
                        />
                        <button
                            className="random-btn"
                            onClick={generateRandomUserId}
                            title="Generate random user ID"
                        >
                            🎲
                        </button>
                    </div>

                    {recentUsers.length > 0 && (
                        <div className="recent-users">
                            <label>Recent Users:</label>
                            <div className="user-list">
                                {recentUsers.map(user => (
                                    <div
                                        key={user}
                                        className="user-chip"
                                        onClick={() => selectRecentUser(user)}
                                    >
                                        <span>👤 {user}</span>
                                        <button
                                            className="remove-btn"
                                            onClick={(e) => removeRecentUser(user, e)}
                                            title="Remove from recent"
                                        >
                                            ×
                                        </button>
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}

                    <div className="info-box">
                        <strong>ℹ️ How it works:</strong>
                        <ul>
                            <li>Enter any user ID - it will be created automatically</li>
                            <li>Each user has their own conversation history</li>
                            <li>Use the same ID to access your previous chats</li>
                        </ul>
                    </div>

                    <button
                        className="folder-select-btn"
                        onClick={() => setShowSettings(!showSettings)}
                    >
                        ⚙️ {showSettings ? 'Hide' : 'Show'} Advanced Settings
                    </button>

                    {showSettings && (
                        <div className="settings-panel">
                            <label>Optional - Document Folder Path:</label>
                            <div className="folder-input-group">
                                <input
                                    type="text"
                                    placeholder="C:\Users\YourName\Documents"
                                    value={indexPath}
                                    onChange={(e) => setIndexPath(e.target.value)}
                                    className="folder-input"
                                />
                            </div>

                            <div className="settings-info">
                                <small>
                                    💡 <strong>Note:</strong> This app uses pre-indexed documents.
                                    <br />
                                    <br />
                                    To index new documents:
                                    <br />
                                    • Use Streamlit UI (port 8501) for folder indexing
                                    <br />
                                    • Or run backend ingestion directly
                                    <br />
                                    <br />
                                    Then search your documents here!
                                </small>
                            </div>
                        </div>
                    )}

                    <button
                        onClick={handleLogin}
                        disabled={!userId.trim()}
                        className="login-btn"
                    >
                        Start Searching →
                    </button>
                </div>

                <div className="login-footer">
                    <small>LocalLens v2.0 - Your Personal AI Document Assistant</small>
                </div>
            </div>
        </div>
    );
};

export default LoginSettings;
