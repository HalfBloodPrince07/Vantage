// Updated SettingsPanel to use batch upload endpoint
import React, { useState, useEffect, useRef } from 'react';
import './SettingsPanel.css';

const SettingsPanel = ({ onClose, onIndexingStart }) => {
    const [activeTab, setActiveTab] = useState('indexing');
    const [selectedFolder, setSelectedFolder] = useState('');
    const [selectedFiles, setSelectedFiles] = useState([]);
    const [indexMethod, setIndexMethod] = useState('path');
    const [indexingStatus, setIndexingStatus] = useState(null);
    const [indexedDocs, setIndexedDocs] = useState([]);
    const [systemHealth, setSystemHealth] = useState(null);
    const [loading, setLoading] = useState(false);
    const fileInputRef = useRef(null);
    const folderInputRef = useRef(null);

    useEffect(() => {
        loadSystemHealth();
        loadIndexedDocuments();
    }, []);

    const loadSystemHealth = async () => {
        try {
            const response = await fetch('http://localhost:8000/health');
            const data = await response.json();
            setSystemHealth(data);
        } catch (error) {
            console.error('Failed to load system health:', error);
        }
    };

    const loadIndexedDocuments = async () => {
        try {
            const response = await fetch('http://localhost:8000/search', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    query: '*',
                    top_k: 100
                })
            });
            const data = await response.json();
            setIndexedDocs(data.results || []);
        } catch (error) {
            console.error('Failed to load indexed documents:', error);
        }
    };

    const handleBrowseFiles = () => {
        fileInputRef.current?.click();
    };

    const handleBrowseFolder = () => {
        folderInputRef.current?.click();
    };

    const handleFilesSelected = (e) => {
        const files = Array.from(e.target.files);
        setSelectedFiles(files);
        setIndexMethod('files');
    };

    const handleFolderSelected = (e) => {
        const files = Array.from(e.target.files);
        setSelectedFiles(files);
        setIndexMethod('files');

        if (files.length > 0) {
            const folderName = files[0].webkitRelativePath.split('/')[0];
            setSelectedFolder(folderName);
        }
    };

    const startIndexing = async () => {
        if (indexMethod === 'path') {
            await startPathIndexing();
        } else if (indexMethod === 'files') {
            await startFileUpload();
        }
    };

    const [enableWatcher, setEnableWatcher] = useState(false);

    const enableFileWatcher = async (directory) => {
        try {
            await fetch('http://localhost:8000/watcher/enable', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ directory_path: directory })
            });
            console.log('[Watcher] Enabled for directory:', directory);
        } catch (error) {
            console.error('[Watcher] Failed to enable:', error);
        }
    };

    const startPathIndexing = async () => {
        if (!selectedFolder) {
            alert('Please enter a folder path');
            return;
        }

        setLoading(true);

        try {
            const response = await fetch('http://localhost:8000/index/directory', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    directory_path: selectedFolder,
                    recursive: true
                })
            });

            const result = await response.json();

            if (result.status === 'success') {
                setIndexingStatus({
                    status: 'started',
                    message: result.message
                });

                // Enable watcher if selected
                if (enableWatcher) {
                    await enableFileWatcher(selectedFolder);
                }

                // Notify parent to show progress
                if (onIndexingStart) {
                    onIndexingStart(result.task_id);
                }

                // Close settings panel
                setTimeout(() => onClose(), 1000);
            } else {
                throw new Error(result.detail || 'Failed to start indexing');
            }
        } catch (error) {
            alert(`Indexing failed: ${error.message}`);
        } finally {
            setLoading(false);
        }
    };

    const startFileUpload = async () => {
        if (selectedFiles.length === 0) {
            alert('Please select files first');
            return;
        }

        setLoading(true);
        setIndexingStatus({
            status: 'uploading',
            message: 'Uploading files...',
            processed: 0,
            total: selectedFiles.length
        });

        try {
            const formData = new FormData();
            selectedFiles.forEach(file => {
                formData.append('files', file);
            });

            const response = await fetch('http://localhost:8000/upload-batch', {
                method: 'POST',
                body: formData
            });

            const result = await response.json();

            if (result.status === 'success') {
                setIndexingStatus({
                    status: 'completed',
                    message: result.message
                });

                // Notify parent to show progress
                if (onIndexingStart) {
                    onIndexingStart(result.task_id);
                }

                // Reload documents after a delay
                setTimeout(() => {
                    loadIndexedDocuments();
                    onClose();
                }, 2000);
            } else {
                throw new Error(result.message || 'Upload failed');
            }
        } catch (error) {
            setIndexingStatus({
                status: 'error',
                message: error.message
            });
            alert(`Upload failed: ${error.message}`);
        } finally {
            setLoading(false);
        }
    };

    const deleteDocument = async (docId) => {
        if (!confirm('Delete this document from the index?')) return;

        try {
            await fetch(`http://localhost:8000/documents/${docId}`, {
                method: 'DELETE'
            });
            loadIndexedDocuments();
        } catch (error) {
            alert('Failed to delete document: ' + error.message);
        }
    };

    const renderIndexingTab = () => (
        <div className="tab-content">
            <h3>📁 Document Indexing</h3>

            <div className="method-selector">
                <button
                    className={`method-btn ${indexMethod === 'path' ? 'active' : ''}`}
                    onClick={() => setIndexMethod('path')}
                >
                    📂 Index by Path
                </button>
                <button
                    className={`method-btn ${indexMethod === 'files' ? 'active' : ''}`}
                    onClick={() => setIndexMethod('files')}
                >
                    📤 Upload Files
                </button>
            </div>

            {indexMethod === 'path' && (
                <div className="index-section">
                    <label>Enter Folder Path</label>
                    <div className="folder-selector">
                        <input
                            type="text"
                            value={selectedFolder}
                            onChange={(e) => setSelectedFolder(e.target.value)}
                            placeholder="C:\Users\YourName\Documents\MyFiles"
                            className="path-input"
                        />
                    </div>

                    <div className="path-hint">
                        💡 Enter the full path on your server/computer
                    </div>

                    <div className="watcher-option" style={{ marginTop: '15px', marginBottom: '15px' }}>
                        <label className="checkbox-label" style={{ display: 'flex', alignItems: 'center', gap: '10px', cursor: 'pointer' }}>
                            <input
                                type="checkbox"
                                checked={enableWatcher}
                                onChange={(e) => setEnableWatcher(e.target.checked)}
                                style={{ width: '18px', height: '18px' }}
                            />
                            <span>📂 Enable Auto-Index (watch for new files)</span>
                        </label>
                    </div>

                    <button
                        onClick={startIndexing}
                        disabled={loading || !selectedFolder}
                        className="index-btn"
                    >
                        {loading ? '⏳ Starting...' : '🚀 Start Indexing'}
                    </button>
                </div>
            )}

            {indexMethod === 'files' && (
                <div className="index-section">
                    <label>Select Files or Folder</label>

                    <div className="file-buttons">
                        <button onClick={handleBrowseFiles} className="browse-btn">
                            📄 Select Files
                        </button>
                        <button onClick={handleBrowseFolder} className="browse-btn">
                            📁 Select Folder
                        </button>
                    </div>

                    <input
                        ref={fileInputRef}
                        type="file"
                        multiple
                        onChange={handleFilesSelected}
                        style={{ display: 'none' }}
                        accept=".pdf,.txt,.docx,.xlsx,.csv,.jpg,.jpeg,.png,.gif"
                    />

                    <input
                        ref={folderInputRef}
                        type="file"
                        webkitdirectory=""
                        multiple
                        onChange={handleFolderSelected}
                        style={{ display: 'none' }}
                    />

                    {selectedFiles.length > 0 && (
                        <div className="selected-files-box">
                            <strong>✅ {selectedFiles.length} files selected</strong>
                            {selectedFolder && <div style={{ fontSize: '12px', color: '#999', marginTop: '5px' }}>
                                From: {selectedFolder}
                            </div>}
                            <div className="file-preview">
                                {selectedFiles.slice(0, 5).map((file, idx) => (
                                    <div key={idx} className="file-preview-item">
                                        📄 {file.name}
                                    </div>
                                ))}
                                {selectedFiles.length > 5 && (
                                    <div className="file-preview-item">
                                        ... and {selectedFiles.length - 5} more files
                                    </div>
                                )}
                            </div>
                        </div>
                    )}

                    <button
                        onClick={startIndexing}
                        disabled={loading || selectedFiles.length === 0}
                        className="index-btn"
                    >
                        {loading ? '⏳ Uploading...' : `🚀 Upload & Index ${selectedFiles.length} Files`}
                    </button>
                </div>
            )}

            {indexingStatus && (
                <div className={`status-box ${indexingStatus.status}`}>
                    {indexingStatus.status === 'uploading' && (
                        <>
                            {indexingStatus.total > 0 && (
                                <>
                                    <div className="progress-bar">
                                        <div
                                            className="progress-fill"
                                            style={{ width: `${(indexingStatus.processed / indexingStatus.total) * 100}%` }}
                                        />
                                    </div>
                                    <p>📤 Uploading: {indexingStatus.processed} / {indexingStatus.total} files</p>
                                </>
                            )}
                        </>
                    )}
                    {indexingStatus.status === 'completed' && (
                        <p>✅ {indexingStatus.message}</p>
                    )}
                    {indexingStatus.status === 'error' && (
                        <p>❌ Error: {indexingStatus.message}</p>
                    )}
                </div>
            )}

            <div className="indexed-docs">
                <h4>📄 Indexed Documents ({indexedDocs.length})</h4>
                {indexedDocs.length === 0 && (
                    <div style={{ padding: '20px', textAlign: 'center', color: '#999' }}>
                        No documents indexed yet. Use the options above!
                    </div>
                )}
                <div className="docs-list">
                    {indexedDocs.slice(0, 50).map((doc, idx) => (
                        <div key={idx} className="doc-row">
                            <span className="doc-icon">{getFileIcon(doc.file_type)}</span>
                            <div className="doc-info">
                                <div className="doc-name">{doc.filename}</div>
                                <div className="doc-meta">{doc.file_type} • {formatDate(doc.created_at)}</div>
                            </div>
                            <button
                                className="delete-doc-btn"
                                onClick={() => deleteDocument(doc.id)}
                                title="Delete from index"
                            >
                                🗑️
                            </button>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );

    const renderSystemTab = () => (
        <div className="tab-content">
            <h3>📊 System Status</h3>

            {systemHealth && (
                <div className="health-grid">
                    <div className="health-card">
                        <div className="health-icon">🟢</div>
                        <div className="health-info">
                            <div className="health-label">Status</div>
                            <div className="health-value">{systemHealth.status}</div>
                        </div>
                    </div>

                    <div className="health-card">
                        <div className="health-icon">🔍</div>
                        <div className="health-info">
                            <div className="health-label">OpenSearch</div>
                            <div className="health-value">{systemHealth.opensearch ? 'Connected' : 'Disconnected'}</div>
                        </div>
                    </div>

                    <div className="health-card">
                        <div className="health-icon">🤖</div>
                        <div className="health-info">
                            <div className="health-label">Ollama</div>
                            <div className="health-value">{systemHealth.ollama !== false ? 'Available' : 'Unavailable'}</div>
                        </div>
                    </div>

                    <div className="health-card">
                        <div className="health-icon">💾</div>
                        <div className="health-info">
                            <div className="health-label">Memory</div>
                            <div className="health-value">{systemHealth.memory_manager ? 'Active' : 'Inactive'}</div>
                        </div>
                    </div>
                </div>
            )}

            <div className="config-section">
                <h4>⚙️ Configuration</h4>
                <div className="config-item">
                    <label>Index Name:</label>
                    <input type="text" value="locallens_index" disabled className="config-input" />
                </div>
                <div className="config-item">
                    <label>Embedding Model:</label>
                    <input type="text" value="nomic-embed-text" disabled className="config-input" />
                </div>
                <div className="config-item">
                    <label>LLM Model:</label>
                    <input type="text" value="qwen2.5:7b" disabled className="config-input" />
                </div>
            </div>

            <button className="refresh-btn" onClick={loadSystemHealth}>
                🔄 Refresh Status
            </button>
        </div>
    );

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

    const formatDate = (dateString) => {
        if (!dateString) return 'Unknown';
        return new Date(dateString).toLocaleDateString();
    };

    return (
        <div className="settings-overlay">
            <div className="settings-panel">
                <div className="settings-header">
                    <h2>⚙️ Settings & Management</h2>
                    <button className="close-btn" onClick={onClose}>✕</button>
                </div>

                <div className="settings-tabs">
                    <button
                        className={`tab ${activeTab === 'indexing' ? 'active' : ''}`}
                        onClick={() => setActiveTab('indexing')}
                    >
                        📁 Indexing
                    </button>
                    <button
                        className={`tab ${activeTab === 'system' ? 'active' : ''}`}
                        onClick={() => setActiveTab('system')}
                    >
                        📊 System
                    </button>
                </div>

                <div className="settings-body">
                    {activeTab === 'indexing' && renderIndexingTab()}
                    {activeTab === 'system' && renderSystemTab()}
                </div>
            </div>
        </div>
    );
};

export default SettingsPanel;
