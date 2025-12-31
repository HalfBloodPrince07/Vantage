import React, { useState, useEffect } from 'react';
import './MemoryInsights.css';

const InsightCard = ({ title, icon, items, emptyMessage }) => (
    <div className="insight-card">
        <div className="insight-header">
            <span className="insight-icon">{icon}</span>
            <h4>{title}</h4>
        </div>
        <div className="insight-content">
            {items?.length > 0 ? (
                <ul>
                    {items.map((item, i) => (
                        <li key={i}>{typeof item === 'string' ? item : item.topic || item.query}</li>
                    ))}
                </ul>
            ) : (
                <p className="empty-message">{emptyMessage}</p>
            )}
        </div>
    </div>
);

const MemoryInsights = ({ userId }) => {
    const [insights, setInsights] = useState({
        gaps: [],
        staleClusters: [],
        hotTopics: []
    });
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchInsights = async () => {
            try {
                const response = await fetch(`/api/memory/insights?user_id=${userId}`);
                if (response.ok) {
                    const data = await response.json();
                    setInsights(data);
                }
            } catch (err) {
                console.error('Failed to fetch insights:', err);
            } finally {
                setLoading(false);
            }
        };

        if (userId) fetchInsights();
    }, [userId]);

    if (loading) {
        return <div className="memory-insights-loading">Analyzing your memory...</div>;
    }

    return (
        <div className="memory-insights">
            <h3>Memory Insights</h3>

            <div className="insights-grid">
                <InsightCard
                    title="Knowledge Gaps"
                    icon="🕳️"
                    items={insights.gaps}
                    emptyMessage="No gaps detected - your knowledge is comprehensive!"
                />

                <InsightCard
                    title="Hot Topics"
                    icon="🔥"
                    items={insights.hotTopics}
                    emptyMessage="Start adding memories to see trending topics"
                />

                <InsightCard
                    title="Stale Memories"
                    icon="🧹"
                    items={insights.staleClusters?.map(c => `${c.length} memories need attention`)}
                    emptyMessage="All memories are active and connected!"
                />
            </div>

            {insights.suggestions?.length > 0 && (
                <div className="proactive-suggestions">
                    <h4>💡 You might find these useful:</h4>
                    <div className="suggestions-list">
                        {insights.suggestions.map((suggestion, i) => (
                            <div key={i} className="suggestion-item">
                                <p>{suggestion.content?.substring(0, 100)}...</p>
                                <span className="suggestion-reason">Relevance: {(suggestion.score * 100).toFixed(0)}%</span>
                            </div>
                        ))}
                    </div>
                </div>
            )}
        </div>
    );
};

export default MemoryInsights;
