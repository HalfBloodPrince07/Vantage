// Enhanced ChatInterface with grid view, image previews, and performance optimizations
import React, { useState, useEffect, useRef, useCallback, useMemo } from 'react';
import ChatSidebar from './ChatSidebar';
import DocumentSelector from './DocumentSelector';
import SettingsPanel from './SettingsPanel';
import './ChatInterface.css';

// Helper functions
const getFileIcon = (fileType) => {
    if (!fileType) return '📄';
    const type = fileType.toLowerCase();
    if (type.includes('pdf')) return '📕';
    if (type.includes('image') || type.includes('jpg') || type.includes('png')) return '🖼️';
    if (type.includes('excel') || type.includes('spreadsheet') || type.includes('xlsx')) return '📊';
    if (type.includes('word') || type.includes('doc')) return '📝';
    if (type.includes('text') || type.includes('txt')) return '📄';
    return '📄';
};

const formatFileSize = (bytes) => {
    if (!bytes) return 'Unknown size';
    const kb = bytes / 1024;
    const mb = kb / 1024;
    if (mb >= 1) return `${mb.toFixed(1)} MB`;
    if (kb >= 1) return `${kb.toFixed(0)} KB`;
    return `${bytes} bytes`;
};

const isImageFile = (filePath) => {
    if (!filePath) return false;
    const imageExtensions = ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp', '.svg'];
    return imageExtensions.some(ext => filePath.toLowerCase().endsWith(ext));
};

// Extracted Components
const ResultCard = React.memo(({ result, onImageClick, onAttach, onOpen, query, userId }) => {
    const isImage = isImageFile(result.file_path);
    const score = result.score != null ? (result.score * 100).toFixed(0) : null;
    const summary = result.detailed_summary || result.content_summary || result.text || '';
    const summaryPreview = summary.substring(0, 400) + (summary.length > 400 ? '...' : '');
    const [feedback, setFeedback] = useState(null); // 1 = helpful, -1 = not helpful
    const [feedbackLoading, setFeedbackLoading] = useState(false);

    const handleFeedback = async (isHelpful) => {
        if (feedbackLoading) return;
        setFeedbackLoading(true);
        try {
            const response = await fetch('http://localhost:8000/feedback', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    user_id: userId || 'anonymous',
                    query: query || '',
                    document_id: result.id,
                    is_helpful: isHelpful
                })
            });
            if (response.ok) {
                setFeedback(isHelpful ? 1 : -1);
            }
        } catch (error) {
            console.error('Failed to submit feedback:', error);
        } finally {
            setFeedbackLoading(false);
        }
    };

    return (
        <div className="result-card">
            <div className="result-card-preview">
                {isImage ? (
                    <div
                        className="image-preview"
                        onClick={() => onImageClick(result.file_path)}
                    >
                        <img
                            src={`http://localhost:8000/files/serve?file_path=${encodeURIComponent(result.file_path)}`}
                            alt={result.filename}
                            onError={(e) => {
                                e.target.style.display = 'none';
                                e.target.nextSibling.style.display = 'flex';
                            }}
                        />
                        <div className="image-fallback" style={{ display: 'none' }}>
                            {getFileIcon(result.file_type)}
                        </div>
                    </div>
                ) : (
                    <div className="file-icon-large">
                        {getFileIcon(result.file_type)}
                    </div>
                )}
            </div>
            <div className="result-card-content">
                <div className="result-card-header">
                    <span className="result-filename">
                        {getFileIcon(result.file_type)} {result.filename}
                    </span>
                    {score !== null && (
                        <span className="result-score">
                            {score}% match
                        </span>
                    )}
                </div>
                {/* Summary Preview - shown inline */}
                {summaryPreview && (
                    <div className="result-summary-inline">
                        {summaryPreview}
                    </div>
                )}
                <div className="result-meta">
                    {result.file_type} • {formatFileSize(result.file_size || result.file_size_bytes)}
                </div>
                <div className="result-actions">
                    <button
                        className="result-action-btn attach"
                        onClick={() => onAttach(result.id, result.filename)}
                        title="Attach to conversation"
                    >
                        📎 Attach
                    </button>
                    <button
                        className="result-action-btn open"
                        onClick={() => onOpen(result)}
                        title="Open file"
                    >
                        📂 Open
                    </button>
                </div>
                {/* Feedback Buttons */}
                <div className="feedback-buttons">
                    <span className="feedback-label">Was this helpful?</span>
                    <button
                        className={`feedback-btn helpful ${feedback === 1 ? 'active' : ''}`}
                        onClick={() => handleFeedback(true)}
                        disabled={feedbackLoading}
                        title="Yes, helpful"
                    >
                        👍
                    </button>
                    <button
                        className={`feedback-btn not-helpful ${feedback === -1 ? 'active' : ''}`}
                        onClick={() => handleFeedback(false)}
                        disabled={feedbackLoading}
                        title="Not helpful"
                    >
                        👎
                    </button>
                </div>
            </div>
        </div>
    );
});

const ResultItem = React.memo(({ result, onAttach, onOpen, query, userId }) => {
    const score = result.score != null ? (result.score * 100).toFixed(0) : null;
    const summary = result.detailed_summary || result.content_summary || result.text || '';
    const summaryPreview = summary.substring(0, 300) + (summary.length > 300 ? '...' : '');
    const [feedback, setFeedback] = useState(null);
    const [feedbackLoading, setFeedbackLoading] = useState(false);

    const handleFeedback = async (isHelpful) => {
        if (feedbackLoading) return;
        setFeedbackLoading(true);
        try {
            const response = await fetch('http://localhost:8000/feedback', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    user_id: userId || 'anonymous',
                    query: query || '',
                    document_id: result.id,
                    is_helpful: isHelpful
                })
            });
            if (response.ok) {
                setFeedback(isHelpful ? 1 : -1);
            }
        } catch (error) {
            console.error('Failed to submit feedback:', error);
        } finally {
            setFeedbackLoading(false);
        }
    };

    return (
        <div className="result-item">
            <div className="result-header">
                <span className="result-filename">
                    {getFileIcon(result.file_type)} {result.filename}
                </span>
                {score !== null && (
                    <span className="result-score">
                        {score}% match
                    </span>
                )}
            </div>
            {/* Summary shown inline */}
            {summaryPreview && (
                <div className="result-summary-inline">
                    {summaryPreview}
                </div>
            )}
            <div className="result-meta">
                {result.file_type} • {formatFileSize(result.file_size || result.file_size_bytes)}
            </div>
            <div className="result-actions">
                <button
                    className="result-action-btn attach"
                    onClick={() => onAttach(result.id, result.filename)}
                    title="Attach to conversation"
                >
                    📎 Attach
                </button>
                <button
                    className="result-action-btn open"
                    onClick={() => onOpen(result)}
                    title="Open file"
                >
                    📂 Open
                </button>
            </div>
            {/* Feedback Buttons */}
            <div className="feedback-buttons">
                <span className="feedback-label">Was this helpful?</span>
                <button
                    className={`feedback-btn helpful ${feedback === 1 ? 'active' : ''}`}
                    onClick={() => handleFeedback(true)}
                    disabled={feedbackLoading}
                    title="Yes, helpful"
                >
                    👍
                </button>
                <button
                    className={`feedback-btn not-helpful ${feedback === -1 ? 'active' : ''}`}
                    onClick={() => handleFeedback(false)}
                    disabled={feedbackLoading}
                    title="Not helpful"
                >
                    👎
                </button>
            </div>
        </div>
    );
});

const Message = React.memo(({ message, viewMode, onViewModeChange, onImageClick, onAttach, onOpen, query, userId }) => {
    const isUser = message.role === 'user';

    return (
        <div className={`message ${isUser ? 'user-message' : 'assistant-message'}`}>
            <div className="message-avatar">
                {isUser ? '👤' : '🤖'}
            </div>
            <div className="message-content">
                <div className="message-text">{message.content}</div>

                {/* Document Mode Indicator */}
                {!isUser && message.document_mode && (
                    <div className="document-mode-badge">
                        🏛️ Document Chat Mode (Daedalus)
                    </div>
                )}

                {message.results && message.results.length > 0 && (
                    <div className="message-results">
                        <div className="results-header">
                            <h4>📄 Found {message.results.length} results:</h4>
                            <div className="view-toggle">
                                <button
                                    className={`view-btn ${viewMode === 'list' ? 'active' : ''}`}
                                    onClick={() => onViewModeChange('list')}
                                    title="List view"
                                >
                                    ☰
                                </button>
                                <button
                                    className={`view-btn ${viewMode === 'grid' ? 'active' : ''}`}
                                    onClick={() => onViewModeChange('grid')}
                                    title="Grid view"
                                >
                                    ⊞
                                </button>
                            </div>
                        </div>

                        {viewMode === 'grid' ? (
                            <div className="results-grid">
                                {message.results.map((result, idx) => (
                                    <ResultCard
                                        key={idx}
                                        result={result}
                                        onImageClick={onImageClick}
                                        onAttach={onAttach}
                                        onOpen={onOpen}
                                        query={query || message.query}
                                        userId={userId}
                                    />
                                ))}
                            </div>
                        ) : (
                            <div className="results-list">
                                {message.results.map((result, idx) => (
                                    <ResultItem
                                        key={idx}
                                        result={result}
                                        onAttach={onAttach}
                                        onOpen={onOpen}
                                        query={query || message.query}
                                        userId={userId}
                                    />
                                ))}
                            </div>
                        )}
                    </div>
                )}

                <div className="message-time">
                    {new Date(message.timestamp).toLocaleTimeString()}
                </div>
            </div>
        </div>
    );
});

const ChatInterface = ({ userId = 'user_1', onLogout, onIndexingStart }) => {
    const [currentConversationId, setCurrentConversationId] = useState(null);
    const [messages, setMessages] = useState([]);
    const [query, setQuery] = useState('');
    const [loading, setLoading] = useState(false);
    const [steps, setSteps] = useState([]);
    const [sseConnected, setSSEConnected] = useState(false);
    const [showSettings, setShowSettings] = useState(false);
    const [viewMode, setViewMode] = useState('list'); // 'list' or 'grid'
    const [lightboxImage, setLightboxImage] = useState(null);
    const [attachedDocuments, setAttachedDocuments] = useState([]); // Track attached documents

    const sidebarRef = useRef(null);
    const documentSelectorRef = useRef(null);
    const messagesEndRef = useRef(null);
    const inputRef = useRef(null);

    const handleDocumentClick = useCallback(async (document) => {
        if (document.file_path) {
            try {
                const response = await fetch('http://localhost:8000/files/open', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ file_path: document.file_path })
                });
                const data = await response.json();
                if (data.status !== 'success') {
                    console.error('Failed to open file:', data);
                }
            } catch (error) {
                console.error('Error opening file:', error);
            }
        }
    }, []);

    const handleAttachDocument = useCallback((docId, filename) => {
        // Use DocumentSelector ref instead of ChatSidebar
        if (documentSelectorRef.current?.attachDocument) {
            documentSelectorRef.current.attachDocument(docId, filename);
        }
    }, []);

    const handleLogout = useCallback(() => {
        if (confirm('Are you sure you want to logout?')) {
            localStorage.removeItem('locallens_user');
            if (onLogout) {
                onLogout();
            } else {
                window.location.reload();
            }
        }
    }, [onLogout]);

    const handleNewChat = useCallback(() => {
        setCurrentConversationId(null);
        setMessages([]);
        setSteps([]);
    }, []);

    const handleConversationSelect = useCallback((conversationId) => {
        setCurrentConversationId(conversationId);
        setSteps([]);
    }, []);

    const refreshSidebar = useCallback(() => {
        if (sidebarRef.current?.refreshConversations) {
            sidebarRef.current.refreshConversations();
        }
    }, []);

    // Auto-scroll to bottom when new messages arrive
    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages]);

    useEffect(() => {
        if (currentConversationId) {
            loadMessages();
        } else {
            setMessages([]);
        }
    }, [currentConversationId]);

    const loadMessages = async () => {
        if (!currentConversationId) return;

        try {
            const response = await fetch(
                `http://localhost:8000/conversations/${currentConversationId}/messages`
            );
            const data = await response.json();

            if (data.status === 'success') {
                setMessages(data.messages || []);
            }
        } catch (error) {
            console.error('Failed to load messages:', error);
        }
    };

    const handleSearch = async (e) => {
        e?.preventDefault();
        if (!query.trim() || loading) return;

        const searchQuery = query;
        setQuery('');
        setLoading(true);
        setSteps([]);

        const userMessage = {
            role: 'user',
            content: searchQuery,
            timestamp: new Date().toISOString()
        };
        setMessages(prev => [...prev, userMessage]);

        const sessionId = `session_${Date.now()}`;
        const eventSource = new EventSource(
            `http://localhost:8000/search/enhanced/stream/${sessionId}`
        );

        eventSource.onmessage = (event) => {
            const data = JSON.parse(event.data);

            if (data.type === 'step') {
                setSteps(prev => [...prev, data]);
            } else if (data.type === 'complete') {
                eventSource.close();
                setSSEConnected(false);
            }
        };

        eventSource.onerror = () => {
            eventSource.close();
            setSSEConnected(false);
        };

        setSSEConnected(true);

        try {
            const response = await fetch('http://localhost:8000/search/enhanced', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    query: searchQuery,
                    user_id: userId,
                    session_id: sessionId,
                    conversation_id: currentConversationId,
                    attached_documents: attachedDocuments, // Pass attached docs for Daedalus
                    top_k: 5
                })
            });

            const result = await response.json();

            if (result.conversation_id && !currentConversationId) {
                setCurrentConversationId(result.conversation_id);
                setTimeout(() => refreshSidebar(), 800);
            }

            const assistantMessage = {
                role: 'assistant',
                content: result.response_message || 'Search completed.',
                results: result.results || [],
                timestamp: new Date().toISOString(),
                document_mode: result.document_mode || false, // Track if Daedalus was used
                agents_used: result.agents_used || []
            };
            setMessages(prev => [...prev, assistantMessage]);

        } catch (error) {
            console.error('Search error:', error);
            const errorMessage = {
                role: 'assistant',
                content: `Error: ${error.message}`,
                timestamp: new Date().toISOString()
            };
            setMessages(prev => [...prev, errorMessage]);
        } finally {
            setLoading(false);
            setSteps([]);
        }
    };

    return (
        <>
            <div className="chat-interface">
                <ChatSidebar
                    ref={sidebarRef}
                    userId={userId}
                    currentConversationId={currentConversationId}
                    onConversationSelect={handleConversationSelect}
                    onNewChat={handleNewChat}
                />

                <div className="chat-main">
                    <div className="chat-header">
                        <h1>Vantage</h1>
                        <div className="header-info">
                            <span className="user-badge">👤 {userId}</span>
                            {currentConversationId && (
                                <span className="conversation-indicator">
                                    💬 Active Conversation
                                </span>
                            )}
                            <button
                                className="settings-btn"
                                onClick={() => setShowSettings(true)}
                                title="Settings & Management"
                            >
                                ⚙️
                            </button>
                            <button className="logout-btn" onClick={handleLogout} title="Logout">
                                🚪
                            </button>
                        </div>
                    </div>

                    <DocumentSelector
                        ref={documentSelectorRef}
                        conversationId={currentConversationId}
                        onDocumentsChange={(docIds) => {
                            console.log('Documents changed:', docIds);
                            setAttachedDocuments(docIds); // Update attached documents state
                        }}
                    />

                    <div className="chat-messages">
                        {messages.map((msg, idx) => (
                            <Message
                                key={idx}
                                message={msg}
                                viewMode={viewMode}
                                onViewModeChange={setViewMode}
                                onImageClick={setLightboxImage}
                                onAttach={handleAttachDocument}
                                onOpen={handleDocumentClick}
                                userId={userId}
                            />
                        ))}

                        {steps.length > 0 && (
                            <div className="thinking-steps">
                                <h4>
                                    🤖 {steps.length > 0 && steps[steps.length - 1].agent
                                        ? `${steps[steps.length - 1].agent} is ${steps[steps.length - 1].action.toLowerCase()}...`
                                        : 'Thinking...'}
                                </h4>
                                <div className="steps-list">
                                    {steps.map((step, idx) => (
                                        <div key={idx} className="step-item">
                                            <div className="step-indicator">
                                                <div className="step-dot"></div>
                                                {idx < steps.length - 1 && <div className="step-line"></div>}
                                            </div>
                                            <div className="step-content">
                                                <div className="step-header">
                                                    <span className="step-agent">📍 {step.agent || 'Agent'}</span>
                                                    <span className="step-timestamp">
                                                        {step.timestamp ? new Date(step.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' }) : ''}
                                                    </span>
                                                </div>
                                                <div className="step-action">{step.action}</div>
                                                {step.details && (
                                                    <div className="step-details">{step.details}</div>
                                                )}
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}
                        <div ref={messagesEndRef} />
                    </div>

                    <div className="input-container">
                        <form onSubmit={handleSearch}>
                            <input
                                ref={inputRef}
                                type="text"
                                value={query}
                                onChange={(e) => setQuery(e.target.value)}
                                placeholder="Ask about your documents..."
                                disabled={loading}
                                className="search-input"
                                autoComplete="off"
                                spellCheck="false"
                            />
                            <button
                                type="submit"
                                disabled={loading || !query.trim()}
                                className="search-button"
                            >
                                {loading ? '⏳' : '🔍'} {loading ? 'Searching...' : 'Search'}
                            </button>
                        </form>
                    </div>
                </div>
            </div>

            {showSettings && (
                <SettingsPanel
                    onClose={() => setShowSettings(false)}
                    onIndexingStart={onIndexingStart}
                />
            )}

            {lightboxImage && (
                <div className="lightbox" onClick={() => setLightboxImage(null)}>
                    <div className="lightbox-content" onClick={(e) => e.stopPropagation()}>
                        <button className="lightbox-close" onClick={() => setLightboxImage(null)}>
                            ✕
                        </button>
                        <img
                            src={`http://localhost:8000/files/serve?file_path=${encodeURIComponent(lightboxImage)}`}
                            alt="Full size preview"
                        />
                    </div>
                </div>
            )}
        </>
    );
};

export default ChatInterface;
