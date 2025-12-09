// Fixed IndexingProgress - faster polling and better status handling
import React, { useState, useEffect } from 'react';
import './IndexingProgress.css';

const IndexingProgress = ({ taskId, onComplete }) => {
    const [progress, setProgress] = useState({ processed: 0, total: 0, status: 'indexing' });
    const [isExpanded, setIsExpanded] = useState(true);
    const [lastUpdate, setLastUpdate] = useState(Date.now());

    useEffect(() => {
        if (!taskId) return;

        console.log('[IndexingProgress] Starting to track task:', taskId);

        const pollStatus = setInterval(async () => {
            try {
                const response = await fetch(`http://localhost:8000/index/status/${taskId}`);
                const data = await response.json();

                console.log('[IndexingProgress] Poll response:', data);

                if (data.status === 'success' && data.progress) {
                    const prog = data.progress;
                    const newProgress = {
                        processed: prog.processed || 0,
                        total: prog.total_files || prog.total || 0,
                        status: prog.status,
                        message: prog.message
                    };

                    setProgress(newProgress);
                    setLastUpdate(Date.now());

                    console.log('[IndexingProgress] Updated progress:', newProgress);

                    if (prog.status === 'completed') {
                        console.log('[IndexingProgress] Indexing completed!');
                        clearInterval(pollStatus);
                        setTimeout(() => {
                            if (onComplete) onComplete();
                        }, 3000);
                    }
                } else if (data.status === 'not_found') {
                    console.log('[IndexingProgress] Task not found yet, waiting...');
                }
            } catch (error) {
                console.error('[IndexingProgress] Poll error:', error);
            }
        }, 1000); // Poll every 1 second

        return () => {
            console.log('[IndexingProgress] Cleanup polling');
            clearInterval(pollStatus);
        };
    }, [taskId]);

    if (!taskId) return null;

    const percentage = progress.total > 0
        ? Math.round((progress.processed / progress.total) * 100)
        : 0;

    return (
        <div className={`indexing-progress-float ${isExpanded ? 'expanded' : 'collapsed'}`}>
            <div className="progress-header" onClick={() => setIsExpanded(!isExpanded)}>
                <span className="progress-icon">
                    {progress.status === 'completed' ? '✅' : '🔄'}
                </span>
                <span className="progress-title">
                    {progress.status === 'completed' ? 'Indexing Complete!' : 'Indexing...'}
                </span>
                <button className="collapse-btn">
                    {isExpanded ? '▼' : '▲'}
                </button>
            </div>

            {isExpanded && (
                <div className="progress-body">
                    <div className="progress-bar-container">
                        <div
                            className="progress-bar-fill"
                            style={{ width: `${percentage}%` }}
                        />
                    </div>
                    <div className="progress-text">
                        {progress.status === 'completed' ? (
                            <span>✅ {progress.total} files indexed!</span>
                        ) : (
                            <span>
                                {progress.processed} / {progress.total || '?'} files
                                {progress.total > 0 && ` (${percentage}%)`}
                            </span>
                        )}
                    </div>
                    {progress.message && (
                        <div className="progress-message">{progress.message}</div>
                    )}
                    <div className="progress-debug">
                        Last update: {new Date(lastUpdate).toLocaleTimeString()}
                    </div>
                </div>
            )}
        </div>
    );
};

export default IndexingProgress;
