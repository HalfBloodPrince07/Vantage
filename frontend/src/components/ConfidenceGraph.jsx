// ConfidenceGraph.jsx - Interactive SVG confidence visualization
import React, { useState, useRef } from 'react';
import './ConfidenceGraph.css';

const ConfidenceGraph = ({
    interactions = [],
    width = 400,
    height = 200,
    className = ''
}) => {
    const [hoveredNode, setHoveredNode] = useState(null);
    const [tooltipPos, setTooltipPos] = useState({ x: 0, y: 0 });
    const svgRef = useRef(null);

    // Sample data if none provided
    const data = interactions.length > 0 ? interactions : [
        { id: 1, label: 'Query 1', confidence: 0.45, status: 'complete' },
        { id: 2, label: 'Query 2', confidence: 0.82, status: 'complete' },
        { id: 3, label: 'Query 3', confidence: 0.68, status: 'complete' }
    ];

    const padding = { top: 30, right: 30, bottom: 40, left: 50 };
    const graphWidth = width - padding.left - padding.right;
    const graphHeight = height - padding.top - padding.bottom;

    // Scale functions
    const xScale = (index) => padding.left + (index / (data.length - 1 || 1)) * graphWidth;
    const yScale = (value) => padding.top + (1 - value) * graphHeight;

    // Generate path for the line
    const linePath = data.map((d, i) => {
        const x = xScale(i);
        const y = yScale(d.confidence);
        return `${i === 0 ? 'M' : 'L'} ${x} ${y}`;
    }).join(' ');

    // Generate path for the area fill
    const areaPath = `${linePath} L ${xScale(data.length - 1)} ${yScale(0)} L ${xScale(0)} ${yScale(0)} Z`;

    const handleNodeHover = (node, event) => {
        const svgRect = svgRef.current.getBoundingClientRect();
        setHoveredNode(node);
        setTooltipPos({
            x: event.clientX - svgRect.left,
            y: event.clientY - svgRect.top - 60
        });
    };

    const getConfidenceColor = (confidence) => {
        if (confidence >= 0.7) return '#00ff88';
        if (confidence >= 0.5) return '#00d4ff';
        return '#ff6b6b';
    };

    const getConfidenceLabel = (confidence) => {
        if (confidence >= 0.8) return 'High';
        if (confidence >= 0.6) return 'Medium';
        if (confidence >= 0.4) return 'Low';
        return 'Very Low';
    };

    return (
        <div className={`confidence-graph-container ${className}`}>
            <div className="graph-header">
                <h3>System Confidence</h3>
                <div className="legend">
                    <span className="legend-item high">● High (&gt;80%)</span>
                    <span className="legend-item medium">● Medium (60-80%)</span>
                    <span className="legend-item low">● Low (&lt;60%)</span>
                </div>
            </div>

            <svg
                ref={svgRef}
                width={width}
                height={height}
                className="confidence-graph"
            >
                {/* Grid lines */}
                <g className="grid-lines">
                    {[0, 0.25, 0.5, 0.75, 1].map((tick) => (
                        <g key={tick}>
                            <line
                                x1={padding.left}
                                y1={yScale(tick)}
                                x2={width - padding.right}
                                y2={yScale(tick)}
                                className="grid-line"
                            />
                            <text
                                x={padding.left - 10}
                                y={yScale(tick) + 4}
                                className="axis-label"
                                textAnchor="end"
                            >
                                {Math.round(tick * 100)}%
                            </text>
                        </g>
                    ))}
                </g>

                {/* Gradient definition */}
                <defs>
                    <linearGradient id="confidence-gradient" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="0%" stopColor="rgba(0, 212, 255, 0.3)" />
                        <stop offset="100%" stopColor="rgba(0, 212, 255, 0)" />
                    </linearGradient>
                    <filter id="glow">
                        <feGaussianBlur stdDeviation="3" result="coloredBlur" />
                        <feMerge>
                            <feMergeNode in="coloredBlur" />
                            <feMergeNode in="SourceGraphic" />
                        </feMerge>
                    </filter>
                </defs>

                {/* Area fill */}
                <path
                    d={areaPath}
                    fill="url(#confidence-gradient)"
                    className="area-fill"
                />

                {/* Line */}
                <path
                    d={linePath}
                    fill="none"
                    stroke="url(#line-gradient)"
                    strokeWidth="3"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    className="confidence-line"
                    filter="url(#glow)"
                />

                {/* Line gradient */}
                <defs>
                    <linearGradient id="line-gradient" x1="0%" y1="0%" x2="100%" y2="0%">
                        <stop offset="0%" stopColor="#00d4ff" />
                        <stop offset="100%" stopColor="#8b5cf6" />
                    </linearGradient>
                </defs>

                {/* Data nodes */}
                {data.map((d, i) => {
                    const x = xScale(i);
                    const y = yScale(d.confidence);
                    const isHovered = hoveredNode?.id === d.id;
                    const color = getConfidenceColor(d.confidence);
                    const nodeSize = 8 + (d.confidence * 6); // Size based on confidence

                    return (
                        <g key={d.id} className="data-node">
                            {/* Glow ring */}
                            <circle
                                cx={x}
                                cy={y}
                                r={nodeSize + 8}
                                fill={color}
                                opacity={isHovered ? 0.3 : 0.1}
                                className="node-glow"
                            />
                            {/* Main node */}
                            <circle
                                cx={x}
                                cy={y}
                                r={isHovered ? nodeSize + 4 : nodeSize}
                                fill={color}
                                className="node-circle"
                                onMouseEnter={(e) => handleNodeHover(d, e)}
                                onMouseLeave={() => setHoveredNode(null)}
                                style={{ cursor: 'pointer' }}
                            />
                            {/* Inner dot */}
                            <circle
                                cx={x}
                                cy={y}
                                r={3}
                                fill="#fff"
                                pointerEvents="none"
                            />
                            {/* X-axis label */}
                            <text
                                x={x}
                                y={height - 10}
                                className="x-label"
                                textAnchor="middle"
                            >
                                {d.label}
                            </text>
                        </g>
                    );
                })}
            </svg>

            {/* Tooltip */}
            {hoveredNode && (
                <div
                    className="graph-tooltip"
                    style={{
                        left: tooltipPos.x,
                        top: tooltipPos.y
                    }}
                >
                    <div className="tooltip-header">{hoveredNode.label}</div>
                    <div className="tooltip-confidence">
                        <span
                            className="confidence-dot"
                            style={{ background: getConfidenceColor(hoveredNode.confidence) }}
                        ></span>
                        <span className="confidence-value">
                            {Math.round(hoveredNode.confidence * 100)}%
                        </span>
                        <span className="confidence-label">
                            {getConfidenceLabel(hoveredNode.confidence)}
                        </span>
                    </div>
                </div>
            )}
        </div>
    );
};

export default ConfidenceGraph;
