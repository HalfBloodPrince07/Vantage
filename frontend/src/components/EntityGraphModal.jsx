// EntityGraphModal.jsx - Interactive animated knowledge graph
import React, { useState, useEffect, useRef, useCallback } from 'react';
import './EntityGraphModal.css';

const EntityGraphModal = ({ documentId, documentName, isOpen, onClose }) => {
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [data, setData] = useState(null);
    const [nodes, setNodes] = useState([]);
    const [edges, setEdges] = useState([]);
    const [hoveredNode, setHoveredNode] = useState(null);
    const [selectedNode, setSelectedNode] = useState(null);
    const [dragging, setDragging] = useState(null);
    const svgRef = useRef(null);
    const animationRef = useRef(null);

    useEffect(() => {
        if (isOpen && documentId) {
            fetchEntityData();
        }
        return () => {
            if (animationRef.current) cancelAnimationFrame(animationRef.current);
        };
    }, [isOpen, documentId]);

    const fetchEntityData = async () => {
        setLoading(true);
        setError(null);
        try {
            const response = await fetch(`http://localhost:8000/documents/${documentId}/entities`);
            if (!response.ok) throw new Error('Failed to fetch entity data');
            const result = await response.json();
            setData(result);
            initializeGraph(result);
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    // Initialize nodes with physics properties
    const initializeGraph = useCallback((graphData) => {
        if (!graphData?.graph?.nodes) return;

        const width = 600;
        const height = 380;
        const centerX = width / 2;
        const centerY = height / 2;

        const initialNodes = graphData.graph.nodes.map((node, i) => {
            const isCenter = node.id === 'doc';
            const angle = isCenter ? 0 : (2 * Math.PI * i) / (graphData.graph.nodes.length - 1);
            const radius = isCenter ? 0 : 120 + Math.random() * 40;

            return {
                ...node,
                x: centerX + radius * Math.cos(angle),
                y: centerY + radius * Math.sin(angle),
                vx: 0,
                vy: 0,
                targetX: centerX + radius * Math.cos(angle),
                targetY: centerY + radius * Math.sin(angle),
                size: isCenter ? 35 : 12 + Math.random() * 8,
                pulsePhase: Math.random() * Math.PI * 2,
                glowIntensity: 0.5
            };
        });

        setNodes(initialNodes);
        setEdges(graphData.graph.edges || []);
        startAnimation();
    }, []);

    // Animation loop for smooth physics
    const startAnimation = useCallback(() => {
        const animate = () => {
            setNodes(prev => prev.map(node => {
                // Gentle floating animation
                const floatX = Math.sin(Date.now() / 2000 + node.pulsePhase) * 2;
                const floatY = Math.cos(Date.now() / 2500 + node.pulsePhase) * 2;

                // Spring physics toward target
                const dx = (node.targetX + floatX) - node.x;
                const dy = (node.targetY + floatY) - node.y;

                return {
                    ...node,
                    x: node.x + dx * 0.08,
                    y: node.y + dy * 0.08,
                    glowIntensity: node.id === hoveredNode?.id ? 1 : 0.5 + Math.sin(Date.now() / 500 + node.pulsePhase) * 0.2
                };
            }));
            animationRef.current = requestAnimationFrame(animate);
        };
        animate();
    }, [hoveredNode]);

    // Handle mouse events for dragging
    const handleMouseDown = (e, node) => {
        e.stopPropagation();
        setDragging(node.id);
        setSelectedNode(node);
    };

    const handleMouseMove = useCallback((e) => {
        if (!dragging || !svgRef.current) return;

        const svg = svgRef.current;
        const rect = svg.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;

        setNodes(prev => prev.map(node =>
            node.id === dragging
                ? { ...node, targetX: x, targetY: y, x, y }
                : node
        ));
    }, [dragging]);

    const handleMouseUp = useCallback(() => {
        setDragging(null);
    }, []);

    // Get node color by type
    const getNodeColor = (type) => {
        switch (type) {
            case 'document': return '#3b82f6';
            case 'entity': return '#10b981';
            case 'keyword': return '#f59e0b';
            case 'topic': return '#ec4899';
            default: return '#8b5cf6';
        }
    };

    // Get connected nodes for highlighting
    const getConnectedNodes = (nodeId) => {
        const connected = new Set();
        edges.forEach(edge => {
            if (edge.source === nodeId) connected.add(edge.target);
            if (edge.target === nodeId) connected.add(edge.source);
        });
        return connected;
    };

    if (!isOpen) return null;

    const connectedToHovered = hoveredNode ? getConnectedNodes(hoveredNode.id) : new Set();

    return (
        <div className="entity-graph-overlay" onClick={onClose}>
            <div className="entity-graph-modal interactive" onClick={e => e.stopPropagation()}>
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

                    {!loading && !error && nodes.length > 0 && (
                        <>
                            <svg
                                ref={svgRef}
                                className="graph-svg"
                                viewBox="0 0 600 380"
                                onMouseMove={handleMouseMove}
                                onMouseUp={handleMouseUp}
                                onMouseLeave={handleMouseUp}
                            >
                                {/* Glow filters */}
                                <defs>
                                    {['#3b82f6', '#10b981', '#f59e0b', '#ec4899', '#8b5cf6'].map((color, i) => (
                                        <filter key={i} id={`glow-${i}`} x="-50%" y="-50%" width="200%" height="200%">
                                            <feGaussianBlur stdDeviation="4" result="blur" />
                                            <feFlood floodColor={color} floodOpacity="0.6" />
                                            <feComposite in2="blur" operator="in" />
                                            <feMerge>
                                                <feMergeNode />
                                                <feMergeNode in="SourceGraphic" />
                                            </feMerge>
                                        </filter>
                                    ))}
                                    <linearGradient id="edge-gradient" x1="0%" y1="0%" x2="100%" y2="0%">
                                        <stop offset="0%" stopColor="rgba(139, 92, 246, 0.1)" />
                                        <stop offset="50%" stopColor="rgba(139, 92, 246, 0.6)" />
                                        <stop offset="100%" stopColor="rgba(139, 92, 246, 0.1)" />
                                    </linearGradient>
                                </defs>

                                {/* Animated edges */}
                                {edges.map((edge, i) => {
                                    const from = nodes.find(n => n.id === edge.source);
                                    const to = nodes.find(n => n.id === edge.target);
                                    if (!from || !to) return null;

                                    const isHighlighted = hoveredNode &&
                                        (edge.source === hoveredNode.id || edge.target === hoveredNode.id);

                                    return (
                                        <g key={i} className={`edge ${isHighlighted ? 'highlighted' : ''}`}>
                                            <line
                                                x1={from.x}
                                                y1={from.y}
                                                x2={to.x}
                                                y2={to.y}
                                                stroke={isHighlighted ? "rgba(139, 92, 246, 0.8)" : "rgba(139, 92, 246, 0.2)"}
                                                strokeWidth={isHighlighted ? 2 : 1}
                                            />
                                            {/* Animated data pulse along edge */}
                                            {isHighlighted && (
                                                <circle r="3" fill="#8b5cf6">
                                                    <animateMotion
                                                        dur="1s"
                                                        repeatCount="indefinite"
                                                        path={`M${from.x},${from.y} L${to.x},${to.y}`}
                                                    />
                                                </circle>
                                            )}
                                        </g>
                                    );
                                })}

                                {/* Interactive nodes */}
                                {nodes.map((node) => {
                                    const color = getNodeColor(node.type);
                                    const isHovered = hoveredNode?.id === node.id;
                                    const isConnected = connectedToHovered.has(node.id);
                                    const isSelected = selectedNode?.id === node.id;
                                    const glowFilterIndex = ['#3b82f6', '#10b981', '#f59e0b', '#ec4899', '#8b5cf6'].indexOf(color);

                                    return (
                                        <g
                                            key={node.id}
                                            className={`graph-node ${isHovered ? 'hovered' : ''} ${isConnected ? 'connected' : ''}`}
                                            onMouseEnter={() => setHoveredNode(node)}
                                            onMouseLeave={() => setHoveredNode(null)}
                                            onMouseDown={(e) => handleMouseDown(e, node)}
                                            style={{ cursor: 'grab' }}
                                        >
                                            {/* Outer glow ring */}
                                            <circle
                                                cx={node.x}
                                                cy={node.y}
                                                r={node.size + 8}
                                                fill={color}
                                                opacity={isHovered ? 0.3 : node.glowIntensity * 0.15}
                                                className="node-glow"
                                            />

                                            {/* Pulse ring animation */}
                                            {(isHovered || isSelected) && (
                                                <circle
                                                    cx={node.x}
                                                    cy={node.y}
                                                    r={node.size}
                                                    fill="none"
                                                    stroke={color}
                                                    strokeWidth="2"
                                                    opacity="0.6"
                                                    className="pulse-ring"
                                                >
                                                    <animate
                                                        attributeName="r"
                                                        from={node.size}
                                                        to={node.size + 20}
                                                        dur="1s"
                                                        repeatCount="indefinite"
                                                    />
                                                    <animate
                                                        attributeName="opacity"
                                                        from="0.6"
                                                        to="0"
                                                        dur="1s"
                                                        repeatCount="indefinite"
                                                    />
                                                </circle>
                                            )}

                                            {/* Main node circle */}
                                            <circle
                                                cx={node.x}
                                                cy={node.y}
                                                r={isHovered ? node.size + 4 : node.size}
                                                fill={color}
                                                filter={isHovered ? `url(#glow-${glowFilterIndex})` : ''}
                                                className="node-circle"
                                            />

                                            {/* Inner highlight */}
                                            <circle
                                                cx={node.x - node.size * 0.25}
                                                cy={node.y - node.size * 0.25}
                                                r={node.size * 0.3}
                                                fill="rgba(255,255,255,0.3)"
                                            />

                                            {/* Label */}
                                            <text
                                                x={node.x}
                                                y={node.y + node.size + 14}
                                                textAnchor="middle"
                                                fill={isHovered ? "#fff" : "#9ca3af"}
                                                fontSize={node.id === 'doc' ? 12 : 10}
                                                fontWeight={isHovered ? 600 : 400}
                                                className="node-label"
                                            >
                                                {node.label.length > 15 ? node.label.substring(0, 12) + '...' : node.label}
                                            </text>
                                        </g>
                                    );
                                })}
                            </svg>

                            {/* Tooltip for hovered node */}
                            {hoveredNode && (
                                <div
                                    className="node-tooltip"
                                    style={{
                                        left: hoveredNode.x,
                                        top: hoveredNode.y - hoveredNode.size - 60
                                    }}
                                >
                                    <div className="tooltip-title">{hoveredNode.label}</div>
                                    <div className="tooltip-type">
                                        <span className="type-dot" style={{ background: getNodeColor(hoveredNode.type) }}></span>
                                        {hoveredNode.type}
                                    </div>
                                    <div className="tooltip-hint">Click & drag to move</div>
                                </div>
                            )}

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
                        </>
                    )}

                    {/* Entity tag lists */}
                    {!loading && !error && data && (
                        <div className="entity-lists">
                            {data.keywords?.length > 0 && (
                                <div className="entity-section">
                                    <h4>🔑 Keywords</h4>
                                    <div className="tag-cloud">
                                        {data.keywords.slice(0, 15).map((k, i) => (
                                            <span key={i} className="tag keyword interactive">{k}</span>
                                        ))}
                                    </div>
                                </div>
                            )}

                            {data.topics?.length > 0 && (
                                <div className="entity-section">
                                    <h4>📂 Topics</h4>
                                    <div className="tag-cloud">
                                        {data.topics.slice(0, 10).map((t, i) => (
                                            <span key={i} className="tag topic interactive">{t}</span>
                                        ))}
                                    </div>
                                </div>
                            )}
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};

export default EntityGraphModal;
