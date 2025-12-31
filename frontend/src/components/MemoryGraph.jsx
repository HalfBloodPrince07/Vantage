import React, { useState, useEffect, useCallback } from 'react';
import ForceGraph2D from 'react-force-graph-2d';
import './MemoryGraph.css';

const getColorByType = (noteType) => {
    const colors = {
        insight: '#10b981',
        query: '#3b82f6',
        feedback: '#f59e0b',
        document: '#8b5cf6',
        consolidated: '#ec4899',
        code: '#06b6d4',
        image: '#f97316'
    };
    return colors[noteType] || '#6b7280';
};

const MemoryGraph = ({ userId, onNodeClick }) => {
    const [graphData, setGraphData] = useState({ nodes: [], links: [] });
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [selectedNode, setSelectedNode] = useState(null);

    useEffect(() => {
        if (!userId) return;

        const fetchGraph = async () => {
            try {
                setLoading(true);
                const response = await fetch(`/api/memory/graph/${userId}`);
                if (!response.ok) throw new Error('Failed to fetch memory graph');
                const data = await response.json();
                setGraphData({
                    nodes: data.nodes.map(n => ({
                        id: n.id,
                        name: n.content?.substring(0, 50) || 'Untitled',
                        type: n.note_type,
                        importance: n.importance,
                        val: Math.max(1, n.importance * 10)
                    })),
                    links: data.edges.map(e => ({
                        source: e.source,
                        target: e.target,
                        strength: e.strength || 0.5
                    }))
                });
            } catch (err) {
                setError(err.message);
            } finally {
                setLoading(false);
            }
        };

        fetchGraph();
    }, [userId]);

    const handleNodeClick = useCallback((node) => {
        setSelectedNode(node);
        onNodeClick?.(node);
    }, [onNodeClick]);

    if (loading) {
        return (
            <div className="memory-graph-loading">
                <div className="spinner"></div>
                <p>Loading memory graph...</p>
            </div>
        );
    }

    if (error) {
        return <div className="memory-graph-error">Error: {error}</div>;
    }

    return (
        <div className="memory-graph-container">
            <div className="memory-graph-legend">
                {Object.entries({
                    insight: 'Insight', query: 'Query', feedback: 'Feedback',
                    document: 'Document', consolidated: 'Consolidated', code: 'Code', image: 'Image'
                }).map(([type, label]) => (
                    <div key={type} className="legend-item">
                        <span className="legend-dot" style={{ backgroundColor: getColorByType(type) }}></span>
                        <span>{label}</span>
                    </div>
                ))}
            </div>

            <ForceGraph2D
                graphData={graphData}
                nodeLabel={n => `${n.name}\nImportance: ${(n.importance * 100).toFixed(0)}%`}
                nodeColor={n => getColorByType(n.type)}
                nodeRelSize={6}
                linkWidth={l => l.strength * 2}
                linkColor={() => 'rgba(255,255,255,0.2)'}
                onNodeClick={handleNodeClick}
                backgroundColor="#0f172a"
                width={800}
                height={500}
            />

            {selectedNode && (
                <div className="selected-node-info">
                    <h4>{selectedNode.name}</h4>
                    <p>Type: {selectedNode.type}</p>
                    <p>Importance: {(selectedNode.importance * 100).toFixed(0)}%</p>
                </div>
            )}
        </div>
    );
};

export default MemoryGraph;
