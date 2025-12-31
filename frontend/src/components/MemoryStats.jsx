import React, { useState, useEffect } from 'react';
import './MemoryStats.css';

const StatCard = ({ title, value, icon, trend }) => (
    <div className="stat-card">
        <div className="stat-icon">{icon}</div>
        <div className="stat-content">
            <span className="stat-title">{title}</span>
            <span className="stat-value">{value}</span>
            {trend && <span className={`stat-trend ${trend > 0 ? 'positive' : 'negative'}`}>
                {trend > 0 ? '↑' : '↓'} {Math.abs(trend)}%
            </span>}
        </div>
    </div>
);

const MemoryStats = ({ userId }) => {
    const [stats, setStats] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchStats = async () => {
            try {
                const response = await fetch(`/api/memory/stats?user_id=${userId}`);
                if (response.ok) {
                    const data = await response.json();
                    setStats(data);
                }
            } catch (err) {
                console.error('Failed to fetch memory stats:', err);
            } finally {
                setLoading(false);
            }
        };

        if (userId) fetchStats();
        const interval = setInterval(fetchStats, 60000);
        return () => clearInterval(interval);
    }, [userId]);

    if (loading) {
        return <div className="memory-stats-loading">Loading stats...</div>;
    }

    if (!stats) {
        return <div className="memory-stats-empty">No stats available</div>;
    }

    return (
        <div className="memory-stats">
            <h3>Memory Statistics</h3>
            <div className="stats-grid">
                <StatCard title="Total Memories" value={stats.total_notes} icon="🧠" />
                <StatCard title="Avg Links/Note" value={stats.avg_links_per_note?.toFixed(1) || '0'} icon="🔗" />
                <StatCard title="Search Latency" value={`${stats.search_latency_ms || 0}ms`} icon="⚡" />
                <StatCard title="24h Growth" value={stats.memory_growth_24h || 0} icon="📈" trend={stats.memory_growth_24h > 0 ? 10 : 0} />
            </div>

            {stats.notes_by_type && Object.keys(stats.notes_by_type).length > 0 && (
                <div className="type-breakdown">
                    <h4>By Type</h4>
                    <div className="type-bars">
                        {Object.entries(stats.notes_by_type).map(([type, count]) => (
                            <div key={type} className="type-bar-item">
                                <span className="type-label">{type}</span>
                                <div className="type-bar">
                                    <div
                                        className="type-bar-fill"
                                        style={{ width: `${(count / stats.total_notes) * 100}%` }}
                                    ></div>
                                </div>
                                <span className="type-count">{count}</span>
                            </div>
                        ))}
                    </div>
                </div>
            )}
        </div>
    );
};

export default MemoryStats;
