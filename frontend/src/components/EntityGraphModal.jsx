// EntityGraphModal.jsx - Interactive Knowledge Graph with Focus Mode
// Features: Sticky dragging, interactive highlighting, cinematic movement, smooth transitions
import React, { useState, useEffect, useRef, useCallback } from 'react';
import './EntityGraphModal.css';

// ============================================
// CONSTANTS
// ============================================
const GRAPH_WIDTH = 800;  // Wide enough for 250px radius
const GRAPH_HEIGHT = 550; // Tall enough for full radial layout
const CENTER_X = GRAPH_WIDTH / 2;
const CENTER_Y = GRAPH_HEIGHT / 2;
const TRANSITION_DURATION = 400; // ms for smooth transitions
const PAN_ANIMATION_SPEED = 0.12; // lerp factor for smooth pan

const EntityGraphModal = ({ documentId, documentName, isOpen, onClose }) => {
    // ============================================
    // STATE MANAGEMENT
    // ============================================

    // Data state
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [data, setData] = useState(null);
    const [nodes, setNodes] = useState([]);
    const [edges, setEdges] = useState([]);

    // Interaction state
    const [hoveredNode, setHoveredNode] = useState(null);
    const [isFullscreen, setIsFullscreen] = useState(false);

    // Focus Mode state
    const [focusedNode, setFocusedNode] = useState(null);
    const [highlightedNodes, setHighlightedNodes] = useState(new Set());

    // Sticky Dragging state
    const [draggingNode, setDraggingNode] = useState(null);
    const [dragOffset, setDragOffset] = useState({ x: 0, y: 0 });

    // Zoom and pan state
    const [zoom, setZoom] = useState(1);
    const [pan, setPan] = useState({ x: 0, y: 0 });
    const [targetPan, setTargetPan] = useState({ x: 0, y: 0 });
    const [isPanning, setIsPanning] = useState(false);
    const [panStart, setPanStart] = useState({ x: 0, y: 0 });

    // Refs
    const svgRef = useRef(null);
    const animationRef = useRef(null);

    // ============================================
    // DATA FETCHING
    // ============================================

    useEffect(() => {
        if (isOpen && documentId) {
            fetchEntityData();
            // Reset state when opening
            setFocusedNode(null);
            setHighlightedNodes(new Set());
            setZoom(1);
            setPan({ x: 0, y: 0 });
            setTargetPan({ x: 0, y: 0 });
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

    // ============================================
    // GRAPH INITIALIZATION
    // ============================================

    const initializeGraph = useCallback((graphData) => {
        if (!graphData?.graph?.nodes) return;

        // ========================================
        // HIERARCHICAL RADIAL LAYOUT
        // ========================================

        // Generous radii for each level (center, categories, items)
        const levelRadius = {
            0: 0,     // Center document
            1: 130,   // Category nodes (Skills, Experience, etc.)
            2: 250    // Item nodes (individual entities)
        };

        // Find category nodes (level 1) and calculate their angles
        const categories = graphData.graph.nodes.filter(n => n.level === 1);
        const categoryAngles = {};
        const angleOffset = -Math.PI / 2; // Start from top

        categories.forEach((cat, i) => {
            categoryAngles[cat.id] = (2 * Math.PI * i) / categories.length + angleOffset;
        });

        // Group level-2 nodes by their parent category
        const childrenByParent = {};
        graphData.graph.edges.forEach(edge => {
            const parent = edge.source;
            const child = edge.target;
            if (!childrenByParent[parent]) childrenByParent[parent] = [];
            if (!childrenByParent[parent].includes(child)) {
                childrenByParent[parent].push(child);
            }
        });

        // Position each node
        const initialNodes = graphData.graph.nodes.map((node) => {
            let x, y;
            let size = 8; // Default small size

            if (node.level === 0 || node.id === 'center') {
                // CENTER: Document node
                x = CENTER_X;
                y = CENTER_Y;
                size = 25;
            } else if (node.level === 1) {
                // LEVEL 1: Category nodes in a ring
                const angle = categoryAngles[node.id] || 0;
                x = CENTER_X + levelRadius[1] * Math.cos(angle);
                y = CENTER_Y + levelRadius[1] * Math.sin(angle);
                size = 16;
            } else {
                // LEVEL 2: Entity nodes spread around their parent category
                const parentEdge = graphData.graph.edges.find(e => e.target === node.id);
                const parentId = parentEdge?.source;
                const parentAngle = categoryAngles[parentId] || 0;

                // Get siblings under same parent
                const siblings = childrenByParent[parentId] || [node.id];
                const siblingIndex = siblings.indexOf(node.id);
                const siblingCount = siblings.length;

                // Wide arc for spreading siblings (full 120 degrees)
                const arcSpread = Math.PI * 0.6; // 108 degrees
                const startAngle = parentAngle - arcSpread / 2;
                const angleStep = siblingCount > 1 ? arcSpread / (siblingCount - 1) : 0;
                const itemAngle = startAngle + siblingIndex * angleStep;

                // Stagger radius slightly based on index to reduce overlap
                const radiusJitter = (siblingIndex % 2) * 20;
                const radius = levelRadius[2] + radiusJitter;

                x = CENTER_X + radius * Math.cos(itemAngle);
                y = CENTER_Y + radius * Math.sin(itemAngle);
                size = 10;
            }

            return {
                ...node,
                x,
                y,
                fx: null,
                fy: null,
                size: node.size || size,
                pulsePhase: Math.random() * Math.PI * 2,
            };
        });

        setNodes(initialNodes);
        setEdges(graphData.graph.edges || []);
        startAnimation();
    }, []);

    // ============================================
    // ANIMATION LOOP
    // ============================================

    const startAnimation = useCallback(() => {
        const animate = () => {
            // Smooth pan animation (lerp toward target)
            setPan(prev => {
                const dx = targetPan.x - prev.x;
                const dy = targetPan.y - prev.y;
                // Only update if there's meaningful movement
                if (Math.abs(dx) < 0.01 && Math.abs(dy) < 0.01) {
                    return prev;
                }
                return {
                    x: prev.x + dx * PAN_ANIMATION_SPEED,
                    y: prev.y + dy * PAN_ANIMATION_SPEED
                };
            });

            // NOTE: Removed floating animation - nodes now stay in place
            // This enables proper sticky dragging behavior

            animationRef.current = requestAnimationFrame(animate);
        };
        animate();
    }, [targetPan]);

    // ============================================
    // FOCUS MODE - NEIGHBOR DETECTION
    // ============================================

    const getConnectedNodes = useCallback((nodeId) => {
        const connected = new Set([nodeId]); // Include the node itself
        edges.forEach(edge => {
            if (edge.source === nodeId) connected.add(edge.target);
            if (edge.target === nodeId) connected.add(edge.source);
        });
        return connected;
    }, [edges]);

    // ============================================
    // FOCUS MODE - CLICK HANDLERS
    // ============================================

    const handleNodeClick = useCallback((node, e) => {
        e.stopPropagation();

        // If clicking same node, toggle off
        if (focusedNode?.id === node.id) {
            clearFocus();
            return;
        }

        // Set focus
        setFocusedNode(node);
        const connected = getConnectedNodes(node.id);
        setHighlightedNodes(connected);

        // Cinematic pan to center on node
        animatePanToNode(node);
    }, [focusedNode, getConnectedNodes]);

    const clearFocus = useCallback(() => {
        setFocusedNode(null);
        setHighlightedNodes(new Set());
    }, []);

    const handleBackgroundClick = useCallback((e) => {
        // Only clear if clicking the SVG background
        if (e.target === svgRef.current || e.target.tagName === 'svg') {
            clearFocus();
        }
    }, [clearFocus]);

    // ============================================
    // CINEMATIC MOVEMENT - PAN TO NODE
    // ============================================

    const animatePanToNode = useCallback((node) => {
        // Calculate pan offset to center node
        const offsetX = CENTER_X - node.x;
        const offsetY = CENTER_Y - node.y;

        // Adjust for current zoom
        setTargetPan({
            x: offsetX * zoom,
            y: offsetY * zoom
        });
    }, [zoom]);

    // ============================================
    // STICKY DRAGGING
    // ============================================

    const handleDragStart = useCallback((e, node) => {
        e.stopPropagation();
        if (e.button !== 0) return; // Only left click

        const svg = svgRef.current;
        if (!svg) return;

        const rect = svg.getBoundingClientRect();
        const svgX = ((e.clientX - rect.left) / rect.width) * GRAPH_WIDTH;
        const svgY = ((e.clientY - rect.top) / rect.height) * GRAPH_HEIGHT;

        // Account for pan and zoom
        const adjustedX = (svgX - pan.x - CENTER_X * (1 - zoom)) / zoom;
        const adjustedY = (svgY - pan.y - CENTER_Y * (1 - zoom)) / zoom;

        setDragOffset({ x: node.x - adjustedX, y: node.y - adjustedY });
        setDraggingNode(node.id);

        // Fix node position (sticky)
        setNodes(prev => prev.map(n =>
            n.id === node.id
                ? { ...n, fx: n.x, fy: n.y }
                : n
        ));
    }, [pan, zoom]);

    const handleMouseMove = useCallback((e) => {
        if (!draggingNode || !svgRef.current) return;

        const svg = svgRef.current;
        const rect = svg.getBoundingClientRect();
        const svgX = ((e.clientX - rect.left) / rect.width) * GRAPH_WIDTH;
        const svgY = ((e.clientY - rect.top) / rect.height) * GRAPH_HEIGHT;

        // Account for pan and zoom
        const adjustedX = (svgX - pan.x - CENTER_X * (1 - zoom)) / zoom;
        const adjustedY = (svgY - pan.y - CENTER_Y * (1 - zoom)) / zoom;

        const newX = adjustedX + dragOffset.x;
        const newY = adjustedY + dragOffset.y;

        // Update fixed position (sticky drag)
        setNodes(prev => prev.map(n =>
            n.id === draggingNode
                ? { ...n, x: newX, y: newY, fx: newX, fy: newY }
                : n
        ));
    }, [draggingNode, dragOffset, pan, zoom]);

    const handleMouseUp = useCallback(() => {
        if (draggingNode) {
            // Release the node but keep its position
            setNodes(prev => prev.map(n =>
                n.id === draggingNode
                    ? { ...n, fx: null, fy: null }
                    : n
            ));
            setDraggingNode(null);
        }
        setIsPanning(false);
    }, [draggingNode]);

    // ============================================
    // ZOOM CONTROLS
    // ============================================

    const handleWheel = useCallback((e) => {
        e.preventDefault();
        const delta = e.deltaY > 0 ? 0.9 : 1.1;
        setZoom(prev => Math.min(Math.max(0.3, prev * delta), 3));
    }, []);

    const zoomIn = () => setZoom(prev => Math.min(prev * 1.2, 3));
    const zoomOut = () => setZoom(prev => Math.max(prev * 0.8, 0.3));
    const resetView = () => {
        setZoom(1);
        setPan({ x: 0, y: 0 });
        setTargetPan({ x: 0, y: 0 });
        clearFocus();
    };

    // Pan with middle mouse or shift+drag
    const handlePanStart = useCallback((e) => {
        if (e.button === 1 || e.shiftKey) {
            e.preventDefault();
            setIsPanning(true);
            setPanStart({ x: e.clientX - pan.x, y: e.clientY - pan.y });
        }
    }, [pan]);

    const handlePanMove = useCallback((e) => {
        if (isPanning) {
            const newPan = { x: e.clientX - panStart.x, y: e.clientY - panStart.y };
            setPan(newPan);
            setTargetPan(newPan);
        }
    }, [isPanning, panStart]);

    // ============================================
    // VISUAL HELPERS
    // ============================================

    const getNodeColor = (node) => {
        if (node.color) return node.color;
        switch (node.type) {
            case 'person': return '#3b82f6';
            case 'category': return '#8b5cf6';
            case 'item': return '#10b981';
            case 'document': return '#3b82f6';
            case 'entity': return '#10b981';
            case 'keyword': return '#f59e0b';
            case 'topic': return '#ec4899';
            default: return '#8b5cf6';
        }
    };

    // Focus Mode opacity calculation
    const getNodeOpacity = useCallback((node) => {
        if (!focusedNode) return 1; // No focus - full opacity
        if (highlightedNodes.has(node.id)) return 1; // Highlighted
        return 0.12; // Dimmed
    }, [focusedNode, highlightedNodes]);

    const getEdgeOpacity = useCallback((edge) => {
        if (!focusedNode) return 0.4;
        const isConnected = edge.source === focusedNode.id || edge.target === focusedNode.id;
        return isConnected ? 0.9 : 0.08;
    }, [focusedNode]);

    // ============================================
    // RENDER
    // ============================================

    if (!isOpen) return null;

    return (
        <div className="entity-graph-overlay" onClick={onClose}>
            <div
                className={`entity-graph-modal interactive ${isFullscreen ? 'fullscreen' : ''}`}
                onClick={e => e.stopPropagation()}
            >
                <div className="modal-header">
                    <h3>📊 Knowledge Graph</h3>
                    <span className="modal-filename">{documentName}</span>
                    <div className="modal-actions">
                        <button
                            className="modal-fullscreen"
                            onClick={() => setIsFullscreen(!isFullscreen)}
                            title={isFullscreen ? 'Exit fullscreen' : 'Fullscreen'}
                        >
                            {isFullscreen ? '⛶' : '⛶'}
                        </button>
                        <button className="modal-close" onClick={onClose}>×</button>
                    </div>
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
                            {/* Zoom Controls */}
                            <div className="zoom-controls">
                                <button onClick={zoomIn} title="Zoom In">+</button>
                                <span className="zoom-level">{Math.round(zoom * 100)}%</span>
                                <button onClick={zoomOut} title="Zoom Out">−</button>
                                <button onClick={resetView} title="Reset View">⟲</button>
                            </div>

                            {/* Focus Mode hint */}
                            {focusedNode && (
                                <div className="focus-hint">
                                    <span>🔍 Focused: <strong>{focusedNode.label}</strong></span>
                                    <button onClick={clearFocus}>Clear Focus</button>
                                </div>
                            )}

                            <svg
                                ref={svgRef}
                                className={`graph-svg ${focusedNode ? 'focus-mode' : ''}`}
                                viewBox={`0 0 ${GRAPH_WIDTH} ${GRAPH_HEIGHT}`}
                                onMouseMove={(e) => { handleMouseMove(e); handlePanMove(e); }}
                                onMouseUp={handleMouseUp}
                                onMouseLeave={handleMouseUp}
                                onMouseDown={handlePanStart}
                                onClick={handleBackgroundClick}
                                onWheel={handleWheel}
                                style={{ cursor: draggingNode ? 'grabbing' : isPanning ? 'grabbing' : 'default' }}
                            >
                                {/* SVG Filters for Glow */}
                                <defs>
                                    {['#3b82f6', '#10b981', '#f59e0b', '#ec4899', '#8b5cf6'].map((color, i) => (
                                        <filter key={i} id={`glow-${i}`} x="-100%" y="-100%" width="300%" height="300%">
                                            <feGaussianBlur stdDeviation="6" result="blur" />
                                            <feFlood floodColor={color} floodOpacity="0.8" />
                                            <feComposite in2="blur" operator="in" />
                                            <feMerge>
                                                <feMergeNode />
                                                <feMergeNode in="SourceGraphic" />
                                            </feMerge>
                                        </filter>
                                    ))}
                                    {/* Focus bloom filter */}
                                    <filter id="focus-bloom" x="-150%" y="-150%" width="400%" height="400%">
                                        <feGaussianBlur stdDeviation="8" result="blur" />
                                        <feFlood floodColor="#fff" floodOpacity="0.5" />
                                        <feComposite in2="blur" operator="in" />
                                        <feMerge>
                                            <feMergeNode />
                                            <feMergeNode in="SourceGraphic" />
                                        </feMerge>
                                    </filter>
                                </defs>

                                {/* Zoomable/pannable content group */}
                                <g transform={`translate(${pan.x + CENTER_X * (1 - zoom)}, ${pan.y + CENTER_Y * (1 - zoom)}) scale(${zoom})`}>

                                    {/* Edges with focus opacity */}
                                    {edges.map((edge, i) => {
                                        const from = nodes.find(n => n.id === edge.source);
                                        const to = nodes.find(n => n.id === edge.target);
                                        if (!from || !to) return null;

                                        const opacity = getEdgeOpacity(edge);
                                        const isHighlighted = focusedNode &&
                                            (edge.source === focusedNode.id || edge.target === focusedNode.id);

                                        return (
                                            <g key={i} className="edge" style={{ transition: 'opacity 0.4s ease' }}>
                                                <line
                                                    x1={from.x}
                                                    y1={from.y}
                                                    x2={to.x}
                                                    y2={to.y}
                                                    stroke={isHighlighted ? "rgba(139, 92, 246, 1)" : "rgba(139, 92, 246, 0.5)"}
                                                    strokeWidth={isHighlighted ? 2.5 : 1}
                                                    opacity={opacity}
                                                    style={{ transition: 'all 0.4s ease' }}
                                                />
                                                {/* Animated pulse for focused edges */}
                                                {isHighlighted && (
                                                    <circle r="4" fill="#a78bfa">
                                                        <animateMotion
                                                            dur="1.5s"
                                                            repeatCount="indefinite"
                                                            path={`M${from.x},${from.y} L${to.x},${to.y}`}
                                                        />
                                                    </circle>
                                                )}
                                            </g>
                                        );
                                    })}

                                    {/* Nodes with focus opacity and glow */}
                                    {nodes.map((node) => {
                                        const color = getNodeColor(node);
                                        const opacity = getNodeOpacity(node);
                                        const isFocused = focusedNode?.id === node.id;
                                        const isHovered = hoveredNode?.id === node.id;
                                        const isHighlighted = highlightedNodes.has(node.id);
                                        const glowFilterIndex = ['#3b82f6', '#10b981', '#f59e0b', '#ec4899', '#8b5cf6'].indexOf(color);

                                        return (
                                            <g
                                                key={node.id}
                                                className={`graph-node ${isFocused ? 'focused' : ''} ${isHighlighted ? 'highlighted' : ''} ${isHovered ? 'hovered' : ''}`}
                                                onMouseEnter={() => setHoveredNode(node)}
                                                onMouseLeave={() => setHoveredNode(null)}
                                                onMouseDown={(e) => handleDragStart(e, node)}
                                                onClick={(e) => handleNodeClick(node, e)}
                                                style={{
                                                    cursor: draggingNode === node.id ? 'grabbing' : 'pointer',
                                                    transition: 'opacity 0.4s ease'
                                                }}
                                                opacity={opacity}
                                            >
                                                {/* Focus bloom ring */}
                                                {isFocused && (
                                                    <circle
                                                        cx={node.x}
                                                        cy={node.y}
                                                        r={node.size + 15}
                                                        fill="none"
                                                        stroke={color}
                                                        strokeWidth="3"
                                                        opacity="0.6"
                                                        filter="url(#focus-bloom)"
                                                    >
                                                        <animate
                                                            attributeName="r"
                                                            from={node.size + 10}
                                                            to={node.size + 25}
                                                            dur="1.5s"
                                                            repeatCount="indefinite"
                                                        />
                                                        <animate
                                                            attributeName="opacity"
                                                            from="0.6"
                                                            to="0"
                                                            dur="1.5s"
                                                            repeatCount="indefinite"
                                                        />
                                                    </circle>
                                                )}

                                                {/* Outer glow */}
                                                <circle
                                                    cx={node.x}
                                                    cy={node.y}
                                                    r={node.size + 6}
                                                    fill={color}
                                                    opacity={isFocused ? 0.4 : isHovered ? 0.3 : 0.15}
                                                    style={{ transition: 'all 0.3s ease' }}
                                                />

                                                {/* Main node */}
                                                <circle
                                                    cx={node.x}
                                                    cy={node.y}
                                                    r={isFocused ? node.size + 5 : isHovered ? node.size + 3 : node.size}
                                                    fill={color}
                                                    filter={isFocused || isHovered ? `url(#glow-${Math.max(0, glowFilterIndex)})` : ''}
                                                    style={{ transition: 'all 0.3s ease' }}
                                                />

                                                {/* Inner highlight */}
                                                <circle
                                                    cx={node.x - node.size * 0.25}
                                                    cy={node.y - node.size * 0.25}
                                                    r={node.size * 0.25}
                                                    fill="rgba(255,255,255,0.35)"
                                                />

                                                {/* Label */}
                                                <text
                                                    x={node.x}
                                                    y={node.y + node.size + 14}
                                                    textAnchor="middle"
                                                    fill={isFocused ? "#fff" : isHighlighted ? "#e5e7eb" : "#9ca3af"}
                                                    fontSize={isFocused ? 12 : 10}
                                                    fontWeight={isFocused ? 700 : isHighlighted ? 500 : 400}
                                                    style={{ transition: 'all 0.3s ease' }}
                                                >
                                                    {node.label?.length > 15 ? node.label.substring(0, 12) + '...' : node.label}
                                                </text>
                                            </g>
                                        );
                                    })}
                                </g>
                            </svg>

                            {/* Tooltip */}
                            {hoveredNode && !draggingNode && (
                                <div
                                    className="node-tooltip"
                                    style={{
                                        left: `calc(50% + ${(hoveredNode.x - CENTER_X) * zoom + pan.x}px)`,
                                        top: `calc(${(hoveredNode.y - hoveredNode.size - 60) * zoom + pan.y + 50}px)`
                                    }}
                                >
                                    <div className="tooltip-title">{hoveredNode.label}</div>
                                    <div className="tooltip-type">
                                        <span className="type-dot" style={{ background: getNodeColor(hoveredNode) }}></span>
                                        {hoveredNode.type}{hoveredNode.category ? ` (${hoveredNode.category})` : ''}
                                    </div>
                                    <div className="tooltip-hint">Click to focus • Drag to move</div>
                                </div>
                            )}

                            {/* Legend */}
                            <div className="graph-legend">
                                <span className="legend-item"><span className="dot document"></span> Document</span>
                                <span className="legend-item"><span className="dot entity"></span> Entity ({data.entities?.length || 0})</span>
                                <span className="legend-item"><span className="dot keyword"></span> Keyword ({data.keywords?.length || 0})</span>
                                <span className="legend-item"><span className="dot topic"></span> Topic ({data.topics?.length || 0})</span>
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
