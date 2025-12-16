// EntityGraphModal.jsx - Display document entities as a visual graph
import React, { useState, useEffect, useRef } from 'react';
import './EntityGraphModal.css';

const EntityGraphModal = ({ documentId, documentName, isOpen, onClose }) => {
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [data, setData] = useState(null);
    const canvasRef = useRef(null);

    useEffect(() => {
        if (isOpen && documentId) {
            fetchEntityData();
        }
    }, [isOpen, documentId]);

    const fetchEntityData = async () => {
        setLoading(true);
        setError(null);
        try {
            const response = await fetch(`http://localhost:8000/documents/${documentId}/entities`);
            if (!response.ok) {
                throw new Error('Failed to fetch entity data');
            }
            const result = await response.json();
            setData(result);
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        if (data && data.graph && canvasRef.current) {
            drawGraph(canvasRef.current, data.graph);
        }
    }, [data]);

    const drawGraph = (canvas, graph) => {
        const ctx = canvas.getContext('2d');
        const width = canvas.width;
        const height = canvas.height;

        ctx.clearRect(0, 0, width, height);

        if (!graph.nodes || graph.nodes.length === 0) return;

        // Position nodes in a radial layout
        const centerX = width / 2;
        const centerY = height / 2;
        const radius = Math.min(width, height) * 0.35;

        const nodePositions = {};
        const nodeCount = graph.nodes.length - 1; // Exclude center node

        graph.nodes.forEach((node, i) => {
            if (node.id === 'doc') {
                nodePositions[node.id] = { x: centerX, y: centerY };
            } else {
                const angle = (2 * Math.PI * (i - 1)) / nodeCount;
                nodePositions[node.id] = {
                    x: centerX + radius * Math.cos(angle),
                    y: centerY + radius * Math.sin(angle)
                };
            }
        });

        // Draw edges
        ctx.strokeStyle = 'rgba(139, 92, 246, 0.3)';
        ctx.lineWidth = 1;
        graph.edges.forEach(edge => {
            const from = nodePositions[edge.source];
            const to = nodePositions[edge.target];
            if (from && to) {
                ctx.beginPath();
                ctx.moveTo(from.x, from.y);
                ctx.lineTo(to.x, to.y);
                ctx.stroke();
            }
        });

        // Draw nodes
        graph.nodes.forEach(node => {
            const pos = nodePositions[node.id];
            if (!pos) return;

            const size = node.size || 10;

            // Node colors based on type
            let color = '#8b5cf6'; // default purple
            if (node.type === 'document') color = '#3b82f6'; // blue
            else if (node.type === 'entity') color = '#10b981'; // green
            else if (node.type === 'keyword') color = '#f59e0b'; // orange
            else if (node.type === 'topic') color = '#ec4899'; // pink

            // Draw circle
            ctx.beginPath();
            ctx.arc(pos.x, pos.y, size, 0, 2 * Math.PI);
            ctx.fillStyle = color;
            ctx.fill();
            ctx.strokeStyle = '#1f2937';
            ctx.lineWidth = 2;
            ctx.stroke();

            // Draw label
            ctx.fillStyle = '#e5e7eb';
            ctx.font = node.id === 'doc' ? 'bold 12px Inter, sans-serif' : '10px Inter, sans-serif';
            ctx.textAlign = 'center';
            ctx.textBaseline = 'top';

            // Truncate long labels
            let label = node.label;
            if (label.length > 15) label = label.substring(0, 12) + '...';
            ctx.fillText(label, pos.x, pos.y + size + 4);
        });
    };

    if (!isOpen) return null;

    return (
        <div className="entity-graph-overlay" onClick={onClose}>
            <div className="entity-graph-modal" onClick={e => e.stopPropagation()}>
                <div className="modal-header">
                    <h3>📊 Knowledge Graph</h3>
                    <span className="modal-filename">{documentName}</span>
                    <button className="modal-close" onClick={onClose}>×</button>
                </div>

                <div className="modal-body">
                    {loading && (
                        <div className="loading-state">
                            <div className="spinner"></div>
                            <p>Loading entity graph...</p>
                        </div>
                    )}

                    {error && (
                        <div className="error-state">
                            <p>⚠️ {error}</p>
                        </div>
                    )}

                    {!loading && !error && data && (
                        <>
                            <canvas
                                ref={canvasRef}
                                width={600}
                                height={400}
                                className="graph-canvas"
                            />

                            <div className="graph-legend">
                                <span className="legend-item">
                                    <span className="dot document"></span> Document
                                </span>
                                <span className="legend-item">
                                    <span className="dot entity"></span> Entity ({data.entities?.length || 0})
                                </span>
                                <span className="legend-item">
                                    <span className="dot keyword"></span> Keyword ({data.keywords?.length || 0})
                                </span>
                                <span className="legend-item">
                                    <span className="dot topic"></span> Topic ({data.topics?.length || 0})
                                </span>
                            </div>

                            {/* List view of entities */}
                            <div className="entity-lists">
                                {data.entities?.length > 0 && (
                                    <div className="entity-section">
                                        <h4>🏷️ Entities</h4>
                                        <div className="tag-cloud">
                                            {data.entities.slice(0, 20).map((e, i) => (
                                                <span key={i} className="tag entity">{e}</span>
                                            ))}
                                        </div>
                                    </div>
                                )}

                                {data.keywords?.length > 0 && (
                                    <div className="entity-section">
                                        <h4>🔑 Keywords</h4>
                                        <div className="tag-cloud">
                                            {data.keywords.slice(0, 15).map((k, i) => (
                                                <span key={i} className="tag keyword">{k}</span>
                                            ))}
                                        </div>
                                    </div>
                                )}

                                {data.topics?.length > 0 && (
                                    <div className="entity-section">
                                        <h4>📂 Topics</h4>
                                        <div className="tag-cloud">
                                            {data.topics.slice(0, 10).map((t, i) => (
                                                <span key={i} className="tag topic">{t}</span>
                                            ))}
                                        </div>
                                    </div>
                                )}

                                {(!data.entities?.length && !data.keywords?.length && !data.topics?.length) && (
                                    <div className="no-data">
                                        <p>📭 No entities extracted yet.</p>
                                        <p className="hint">Re-index this document to extract entities.</p>
                                    </div>
                                )}
                            </div>
                        </>
                    )}
                </div>
            </div>
        </div>
    );
};

export default EntityGraphModal;
