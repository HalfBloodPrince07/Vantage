// frontend/components/DocumentSelector.jsx
// Document selector for chat-with-documents feature

import React, { useState, useEffect, useImperativeHandle, forwardRef, useRef } from 'react';
import './DocumentSelector.css';

const DocumentSelector = forwardRef(({ conversationId, onDocumentsChange }, ref) => {
    const [availableDocuments, setAvailableDocuments] = useState([]);
    const [attachedDocuments, setAttachedDocuments] = useState([]);
    const [searchQuery, setSearchQuery] = useState('');
    const [showSelector, setShowSelector] = useState(false);
    const [loading, setLoading] = useState(false);
    const searchTimeoutRef = useRef(null);

    useEffect(() => {
        if (conversationId) {
            loadAttachedDocuments();
        }
    }, [conversationId]);

    // Load all documents when selector is opened for the first time
    useEffect(() => {
        if (showSelector && availableDocuments.length === 0 && !searchQuery) {
            loadAllDocuments();
        }
    }, [showSelector]);

    // Debounced search effect
    useEffect(() => {
        if (searchTimeoutRef.current) {
            clearTimeout(searchTimeoutRef.current);
        }

        if (searchQuery.trim()) {
            searchTimeoutRef.current = setTimeout(() => {
                searchDocuments(searchQuery);
            }, 300); // Wait 300ms after user stops typing
        } else if (showSelector) {
            // When search is cleared, reload all documents
            loadAllDocuments();
        }

        return () => {
            if (searchTimeoutRef.current) {
                clearTimeout(searchTimeoutRef.current);
            }
        };
    }, [searchQuery]);

    const loadAttachedDocuments = async () => {
        try {
            const response = await fetch(
                `http://localhost:8000/conversations/${conversationId}/documents`
            );
            const data = await response.json();

            if (data.status === 'success') {
                setAttachedDocuments(data.document_ids || []);
                onDocumentsChange?.(data.document_ids || []);
            }
        } catch (error) {
            console.error('Failed to load attached documents:', error);
        }
    };

    const loadAllDocuments = async () => {
        setLoading(true);
        try {
            // Use a wildcard search to get all documents
            const response = await fetch('http://localhost:8000/search', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    query: '*', // Wildcard to match all documents
                    top_k: 100,
                    use_hybrid: false
                })
            });

            const data = await response.json();
            setAvailableDocuments(data.results || []);
        } catch (error) {
            console.error('Failed to load documents:', error);
            setAvailableDocuments([]);
        } finally {
            setLoading(false);
        }
    };

    const searchDocuments = async (query) => {
        if (!query.trim()) {
            setAvailableDocuments([]);
            return;
        }

        setLoading(true);
        try {
            const response = await fetch('http://localhost:8000/search', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    query,
                    top_k: 20,
                    use_hybrid: true
                })
            });

            const data = await response.json();
            setAvailableDocuments(data.results || []);
        } catch (error) {
            console.error('Failed to search documents:', error);
        } finally {
            setLoading(false);
        }
    };

    const attachDocument = async (documentId) => {
        if (!conversationId) return;

        try {
            await fetch(`http://localhost:8000/conversations/${conversationId}/documents`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ document_ids: [documentId] })
            });

            const newAttached = [...attachedDocuments, documentId];
            setAttachedDocuments(newAttached);
            onDocumentsChange?.(newAttached);
        } catch (error) {
            console.error('Failed to attach document:', error);
        }
    };

    const detachDocument = async (documentId) => {
        if (!conversationId) return;

        try {
            await fetch(
                `http://localhost:8000/conversations/${conversationId}/documents/${documentId}`,
                { method: 'DELETE' }
            );

            const newAttached = attachedDocuments.filter(id => id !== documentId);
            setAttachedDocuments(newAttached);
            onDocumentsChange?.(newAttached);
        } catch (error) {
            console.error('Failed to detach document:', error);
        }
    };

    // Expose methods to parent via ref
    useImperativeHandle(ref, () => ({
        attachDocument
    }));

    const getFileIcon = (fileType) => {
        if (!fileType) return '📄';
        if (fileType.includes('pdf')) return '📕';
        if (fileType.includes('image') || fileType.match(/\.(jpg|jpeg|png|gif)/)) return '🖼️';
        if (fileType.includes('excel') || fileType.includes('spreadsheet')) return '📊';
        if (fileType.includes('word') || fileType.includes('doc')) return '📝';
        return '📄';
    };

    return (
        <div className="document-selector">
            {/* Attached Documents Badge */}
            {attachedDocuments.length > 0 && (
                <div className="attached-badge">
                    <span className="badge-icon">📎</span>
                    <span className="badge-text">
                        Chatting with {attachedDocuments.length} document{attachedDocuments.length > 1 ? 's' : ''}
                    </span>
                    <button
                        className="badge-toggle"
                        onClick={() => setShowSelector(!showSelector)}
                    >
                        {showSelector ? '▼' : '▶'}
                    </button>
                </div>
            )}

            {/* Add Documents Button */}
            {attachedDocuments.length === 0 && (
                <button
                    className="add-docs-btn"
                    onClick={() => setShowSelector(!showSelector)}
                >
                    📎 Attach Documents
                </button>
            )}

            {/* Document Selector Panel */}
            {showSelector && (
                <div className="selector-panel">
                    <div className="panel-header">
                        <h3>Attach Documents</h3>
                        <button className="close-btn" onClick={() => setShowSelector(false)}>
                            ✕
                        </button>
                    </div>

                    <div className="panel-search">
                        <input
                            type="text"
                            placeholder="🔍 Filter documents by filename or content..."
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                        />
                        {searchQuery && (
                            <button
                                className="clear-search-btn"
                                onClick={() => setSearchQuery('')}
                                title="Clear search"
                            >
                                ✕
                            </button>
                        )}
                    </div>

                    {/* Attached Documents List */}
                    {attachedDocuments.length > 0 && (
                        <div className="attached-list">
                            <h4>Attached ({attachedDocuments.length})</h4>
                            {availableDocuments
                                .filter(doc => attachedDocuments.includes(doc.id))
                                .map(doc => (
                                    <div key={doc.id} className="doc-item attached">
                                        <span className="doc-icon">{getFileIcon(doc.file_type)}</span>
                                        <div className="doc-info">
                                            <div className="doc-name">{doc.filename}</div>
                                            <div className="doc-meta">{doc.file_type}</div>
                                        </div>
                                        <button
                                            className="detach-btn"
                                            onClick={() => detachDocument(doc.id)}
                                        >
                                            Remove
                                        </button>
                                    </div>
                                ))}
                        </div>
                    )}

                    {/* Available Documents */}
                    <div className="available-list">
                        <h4>
                            {searchQuery ? `Search Results (${availableDocuments.filter(doc => !attachedDocuments.includes(doc.id)).length})` : `Available Documents (${availableDocuments.filter(doc => !attachedDocuments.includes(doc.id)).length})`}
                        </h4>
                        {loading && <div className="loading">Loading documents...</div>}
                        {!loading && availableDocuments.length === 0 && (
                            <div className="no-docs-message">
                                {searchQuery
                                    ? `No documents found matching "${searchQuery}". Try different keywords.`
                                    : 'No documents found. Index some documents first in Settings.'}
                            </div>
                        )}
                        {!loading && availableDocuments
                            .filter(doc => !attachedDocuments.includes(doc.id))
                            .map(doc => (
                                <div key={doc.id} className="doc-item">
                                    <span className="doc-icon">{getFileIcon(doc.file_type)}</span>
                                    <div className="doc-info">
                                        <div className="doc-name">{doc.filename}</div>
                                        <div className="doc-meta">{doc.file_type}</div>
                                    </div>
                                    <button
                                        className="attach-btn"
                                        onClick={() => attachDocument(doc.id)}
                                    >
                                        Attach
                                    </button>
                                </div>
                            ))}
                    </div>
                </div>
            )}
        </div>
    );
});

export default DocumentSelector;
