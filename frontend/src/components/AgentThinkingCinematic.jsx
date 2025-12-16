// AgentThinkingCinematic.jsx - Highly stylized AI agent communication visualization
import React, { useState, useEffect, useRef, useCallback } from 'react';
import './AgentThinkingCinematic.css';

// Agent definitions with personality and interaction styles
const AGENTS = {
    // Core orchestration agents
    zeus: { name: 'Zeus', emoji: '⚡', color: '#f59e0b', role: 'Conductor' },
    orchestrator: { name: 'Zeus', emoji: '⚡', color: '#f59e0b', role: 'Orchestrator' },
    enhancedorchestrator: { name: 'Zeus', emoji: '⚡', color: '#f59e0b', role: 'Orchestrator' },
    theconductor: { name: 'Zeus', emoji: '⚡', color: '#f59e0b', role: 'Conductor' },

    // Strategy agents
    athena: { name: 'Athena', emoji: '🦉', color: '#8b5cf6', role: 'Strategist' },
    queryclassifier: { name: 'Athena', emoji: '🦉', color: '#8b5cf6', role: 'Query Classifier' },
    classifier: { name: 'Athena', emoji: '🦉', color: '#8b5cf6', role: 'Classifier' },
    thestrategist: { name: 'Athena', emoji: '🦉', color: '#8b5cf6', role: 'Strategist' },

    // Search/Exploration agents (Apollo)
    apollo: { name: 'Apollo', emoji: '☀️', color: '#f97316', role: 'Explorer' },
    graphexpansion: { name: 'Apollo', emoji: '☀️', color: '#f97316', role: 'Graph Explorer' },
    theilluminated: { name: 'Apollo', emoji: '☀️', color: '#f97316', role: 'Illuminated' },

    // Adaptive agents (Proteus)
    proteus: { name: 'Proteus', emoji: '🔮', color: '#06b6d4', role: 'Shape-Shifter' },
    adaptivestrategy: { name: 'Proteus', emoji: '🔮', color: '#06b6d4', role: 'Strategy Adapter' },
    theshapeshifter: { name: 'Proteus', emoji: '🔮', color: '#06b6d4', role: 'Shape-Shifter' },

    // Navigation/Reasoning agents (Odysseus)
    odysseus: { name: 'Odysseus', emoji: '🧭', color: '#10b981', role: 'Navigator' },
    multihop: { name: 'Odysseus', emoji: '🧭', color: '#10b981', role: 'Multi-hop Navigator' },
    reasoningplanner: { name: 'Odysseus', emoji: '🧭', color: '#10b981', role: 'Planner' },

    // Judgment/Verification agents (Themis)
    themis: { name: 'Themis', emoji: '⚖️', color: '#ec4899', role: 'Judge' },
    thejust: { name: 'Themis', emoji: '⚖️', color: '#ec4899', role: 'The Just' },
    confidence: { name: 'Themis', emoji: '⚖️', color: '#ec4899', role: 'Confidence' },
    confidencescorer: { name: 'Themis', emoji: '⚖️', color: '#ec4899', role: 'Confidence Scorer' },

    // Diogenes - Quality Critic
    diogenes: { name: 'Diogenes', emoji: '🔦', color: '#fbbf24', role: 'Truth Seeker' },
    critic: { name: 'Diogenes', emoji: '🔦', color: '#fbbf24', role: 'Critic' },
    criticagent: { name: 'Diogenes', emoji: '🔦', color: '#fbbf24', role: 'Critic' },
    qualitycheck: { name: 'Diogenes', emoji: '🔦', color: '#fbbf24', role: 'Quality Checker' },

    // Socrates - Clarification
    socrates: { name: 'Socrates', emoji: '🤔', color: '#a855f7', role: 'Inquirer' },
    theinquirer: { name: 'Socrates', emoji: '🤔', color: '#a855f7', role: 'Inquirer' },
    clarification: { name: 'Socrates', emoji: '🤔', color: '#a855f7', role: 'Clarifier' },
    clarificationagent: { name: 'Socrates', emoji: '🤔', color: '#a855f7', role: 'Clarifier' },

    // Aristotle - Analysis
    aristotle: { name: 'Aristotle', emoji: '📊', color: '#22c55e', role: 'Analyst' },
    theanalyst: { name: 'Aristotle', emoji: '📊', color: '#22c55e', role: 'Analyst' },
    analysisagent: { name: 'Aristotle', emoji: '📊', color: '#22c55e', role: 'Analyst' },
    analysis: { name: 'Aristotle', emoji: '📊', color: '#22c55e', role: 'Analysis' },

    // Thoth - Summarization
    thoth: { name: 'Thoth', emoji: '📜', color: '#f97316', role: 'Scribe' },
    summarization: { name: 'Thoth', emoji: '📜', color: '#f97316', role: 'Summarizer' },
    summarizationagent: { name: 'Thoth', emoji: '📜', color: '#f97316', role: 'Summarizer' },

    // Hermes - Explanation
    hermes: { name: 'Hermes', emoji: '📨', color: '#3b82f6', role: 'Messenger' },
    explanation: { name: 'Hermes', emoji: '📨', color: '#3b82f6', role: 'Explainer' },
    explanationagent: { name: 'Hermes', emoji: '📨', color: '#3b82f6', role: 'Explainer' },

    // Memory agents (Mnemosyne)
    memory: { name: 'Mnemosyne', emoji: '🧠', color: '#14b8a6', role: 'Memory Keeper' },
    memorymanager: { name: 'Mnemosyne', emoji: '🧠', color: '#14b8a6', role: 'Memory Manager' },
    mnemosyne: { name: 'Mnemosyne', emoji: '🧠', color: '#14b8a6', role: 'Memory Keeper' },
    loadingcontext: { name: 'Mnemosyne', emoji: '🧠', color: '#14b8a6', role: 'Loading Context' },

    // Search agents (Argus)
    search: { name: 'Argus', emoji: '🔍', color: '#6366f1', role: 'Finder' },
    searchagent: { name: 'Argus', emoji: '🔍', color: '#6366f1', role: 'Search Agent' },
    hybridsearch: { name: 'Argus', emoji: '🔍', color: '#6366f1', role: 'Hybrid Search' },
    argus: { name: 'Argus', emoji: '🔍', color: '#6366f1', role: 'All-Seeing' },
    searching: { name: 'Argus', emoji: '🔍', color: '#6366f1', role: 'Searching' },

    // Document agents
    daedalus: { name: 'Daedalus', emoji: '🏛️', color: '#d97706', role: 'Architect' },
    thearchitect: { name: 'Daedalus', emoji: '🏛️', color: '#d97706', role: 'Architect' },
    documentorchestrator: { name: 'Daedalus', emoji: '🏛️', color: '#d97706', role: 'Document Master' },
    prometheus: { name: 'Prometheus', emoji: '🔥', color: '#ef4444', role: 'Illuminator' },
    hypatia: { name: 'Hypatia', emoji: '📚', color: '#8b5cf6', role: 'Semantic Analyzer' },

    // Ranking agents (Hephaestus)
    ranker: { name: 'Hephaestus', emoji: '🔨', color: '#78716c', role: 'Ranker' },
    personalizedranker: { name: 'Hephaestus', emoji: '🔨', color: '#78716c', role: 'Personalized Ranker' },
    hephaestus: { name: 'Hephaestus', emoji: '🔨', color: '#78716c', role: 'Forge Master' },

    // LLM
    llm: { name: 'Oracle', emoji: '💬', color: '#a855f7', role: 'Language Model' },
    generatinganswer: { name: 'Oracle', emoji: '💬', color: '#a855f7', role: 'Generating Answer' },

    // Default fallback
    agent: { name: 'Agent', emoji: '🤖', color: '#6366f1', role: 'Processing' },
    default: { name: 'Agent', emoji: '🤖', color: '#6366f1', role: 'Processing' }
};

// Smart agent matching function
const getAgentInfo = (agentName) => {
    if (!agentName) return AGENTS.default;

    // Normalize the name: lowercase, remove spaces, dashes, underscores
    const normalized = agentName.toLowerCase().replace(/[-_\s]/g, '');

    // Direct match
    if (AGENTS[normalized]) return AGENTS[normalized];

    // Partial match - check if any key is contained in the name
    for (const [key, value] of Object.entries(AGENTS)) {
        if (normalized.includes(key) || key.includes(normalized)) {
            return value;
        }
    }

    // Action-based inference from step action/message
    return AGENTS.default;
};

// Interaction types with visual representations
const INTERACTION_TYPES = {
    handoff: { label: 'Passing Control', anim: 'handshake' },
    query: { label: 'Requesting Info', anim: 'token-send' },
    response: { label: 'Sharing Results', anim: 'token-receive' },
    collaborate: { label: 'Collaborating', anim: 'merge' },
    verify: { label: 'Verifying', anim: 'pulse-check' },
    refine: { label: 'Refining', anim: 'polish' }
};

// Neural particle for connection visualization
const NeuralParticle = ({ startX, startY, endX, endY, color, delay }) => {
    return (
        <circle
            className="neural-particle"
            r="3"
            fill={color}
            style={{ animationDelay: `${delay}s` }}
        >
            <animate
                attributeName="cx"
                from={startX}
                to={endX}
                dur="1.5s"
                repeatCount="indefinite"
                begin={`${delay}s`}
            />
            <animate
                attributeName="cy"
                from={startY}
                to={endY}
                dur="1.5s"
                repeatCount="indefinite"
                begin={`${delay}s`}
            />
            <animate
                attributeName="opacity"
                values="0;1;1;0"
                dur="1.5s"
                repeatCount="indefinite"
                begin={`${delay}s`}
            />
        </circle>
    );
};

// Glowing token for knowledge transfer
const KnowledgeToken = ({ x, y, color, type }) => (
    <g className={`knowledge-token ${type}`} transform={`translate(${x}, ${y})`}>
        <circle r="8" fill={color} opacity="0.3" className="token-glow">
            <animate attributeName="r" values="8;16;8" dur="1s" repeatCount="indefinite" />
            <animate attributeName="opacity" values="0.3;0.6;0.3" dur="1s" repeatCount="indefinite" />
        </circle>
        <circle r="5" fill={color} />
        <circle r="2" fill="white" opacity="0.8" />
    </g>
);

// Agent Avatar Component with symbolic representation
const AgentAvatar = ({ agent, status, position, onHover }) => {
    const { x, y } = position;
    const isActive = status === 'active';
    const isThinking = status === 'thinking';
    const isComplete = status === 'complete';

    return (
        <g
            className={`agent-avatar-cinematic ${status}`}
            transform={`translate(${x}, ${y})`}
            onMouseEnter={() => onHover?.(agent)}
            onMouseLeave={() => onHover?.(null)}
        >
            {/* Outer aura */}
            <circle
                r="45"
                fill="none"
                stroke={agent.color}
                strokeWidth="1.5"
                opacity={isActive ? 0.5 : 0.15}
                className="agent-aura"
            />

            {/* Neural network pattern for thinking */}
            {isThinking && (
                <g className="neural-pattern">
                    {[0, 60, 120, 180, 240, 300].map((angle, i) => (
                        <line
                            key={i}
                            x1="0"
                            y1="0"
                            x2={Math.cos(angle * Math.PI / 180) * 40}
                            y2={Math.sin(angle * Math.PI / 180) * 40}
                            stroke={agent.color}
                            strokeWidth="1"
                            opacity="0.3"
                            strokeDasharray="4 4"
                            className="neural-thread"
                            style={{ animationDelay: `${i * 0.1}s` }}
                        />
                    ))}
                </g>
            )}

            {/* Orbital rings for active state */}
            {isActive && (
                <>
                    <ellipse
                        rx="38"
                        ry="14"
                        fill="none"
                        stroke={agent.color}
                        strokeWidth="1.5"
                        opacity="0.6"
                        className="orbit-ring-1"
                    />
                    <ellipse
                        rx="38"
                        ry="14"
                        fill="none"
                        stroke={agent.color}
                        strokeWidth="1"
                        opacity="0.4"
                        className="orbit-ring-2"
                    />
                </>
            )}

            {/* Main avatar circle */}
            <circle
                r="30"
                fill={`url(#gradient-${agent.name})`}
                className="avatar-core"
            />

            {/* Inner glow */}
            <circle
                r="26"
                fill="none"
                stroke="rgba(255,255,255,0.3)"
                strokeWidth="1.5"
            />

            {/* Emoji/Symbol */}
            <text
                textAnchor="middle"
                dominantBaseline="central"
                fontSize="24"
                className="agent-symbol"
            >
                {agent.emoji}
            </text>

            {/* Status indicator */}
            {isComplete && (
                <g transform="translate(20, -20)">
                    <circle r="10" fill="#10b981" />
                    <text textAnchor="middle" dominantBaseline="central" fontSize="12" fill="white">✓</text>
                </g>
            )}

            {/* Name label - more prominent */}
            <text
                y="55"
                textAnchor="middle"
                fill="white"
                fontSize="14"
                fontWeight="700"
                opacity="1"
                className="agent-name"
            >
                {agent.name}
            </text>

            {/* Role label */}
            <text
                y="72"
                textAnchor="middle"
                fill={agent.color}
                fontSize="10"
                opacity="0.8"
                fontWeight="500"
            >
                {agent.role}
            </text>
        </g>
    );
};

// Connection line between agents with animated particles
const AgentConnection = ({ from, to, type, color, isActive }) => {
    const midX = (from.x + to.x) / 2;
    const midY = (from.y + to.y) / 2;

    // Calculate control points for curved path
    const dx = to.x - from.x;
    const dy = to.y - from.y;
    const perpX = -dy * 0.2;
    const perpY = dx * 0.2;

    const path = `M ${from.x} ${from.y} Q ${midX + perpX} ${midY + perpY} ${to.x} ${to.y}`;

    return (
        <g className={`agent-connection ${type} ${isActive ? 'active' : ''}`}>
            {/* Base line */}
            <path
                d={path}
                fill="none"
                stroke={color}
                strokeWidth={isActive ? 2 : 1}
                opacity={isActive ? 0.6 : 0.15}
                className="connection-base"
            />

            {/* Animated flow path */}
            {isActive && (
                <>
                    <path
                        d={path}
                        fill="none"
                        stroke={color}
                        strokeWidth="3"
                        opacity="0.8"
                        strokeDasharray="8 16"
                        className="connection-flow"
                    />

                    {/* Multiple particles flowing */}
                    {[0, 0.3, 0.6].map((delay, i) => (
                        <circle
                            key={i}
                            r="4"
                            fill={color}
                            className="flow-particle"
                            style={{ animationDelay: `${delay}s` }}
                        >
                            <animateMotion
                                dur="1.2s"
                                repeatCount="indefinite"
                                path={path}
                                begin={`${delay}s`}
                            />
                            <animate
                                attributeName="opacity"
                                values="0;1;1;0"
                                dur="1.2s"
                                repeatCount="indefinite"
                                begin={`${delay}s`}
                            />
                        </circle>
                    ))}
                </>
            )}

            {/* Interaction label */}
            {isActive && type && (
                <g transform={`translate(${midX}, ${midY - 15})`}>
                    <rect
                        x="-40"
                        y="-10"
                        width="80"
                        height="20"
                        rx="10"
                        fill="rgba(0,0,0,0.7)"
                    />
                    <text
                        textAnchor="middle"
                        dominantBaseline="central"
                        fill="white"
                        fontSize="9"
                        fontWeight="500"
                    >
                        {INTERACTION_TYPES[type]?.label || type}
                    </text>
                </g>
            )}
        </g>
    );
};

const AgentThinkingCinematic = ({ steps, isLoading }) => {
    const [activeAgents, setActiveAgents] = useState([]);
    const [connections, setConnections] = useState([]);
    const [hoveredAgent, setHoveredAgent] = useState(null);
    const svgRef = useRef(null);
    const containerRef = useRef(null);

    // Process steps into agent positions and connections
    useEffect(() => {
        if (!steps || steps.length === 0) return;

        const agents = [];
        const conns = [];
        const agentMap = {};

        // Calculate positions in a flowing layout (larger for visibility)
        const centerX = 400;
        const centerY = 180;
        const radius = 130;

        steps.forEach((step, i) => {
            // Use smart agent matching
            const agentDef = getAgentInfo(step.agent);
            const agentKey = agentDef.name.toLowerCase().replace(/[-_\s]/g, '');

            if (!agentMap[agentKey]) {
                const angle = (i / Math.max(steps.length, 4)) * Math.PI * 2 - Math.PI / 2;
                const x = centerX + Math.cos(angle) * radius;
                const y = centerY + Math.sin(angle) * radius;

                agentMap[agentKey] = {
                    ...agentDef,
                    key: agentKey,
                    position: { x, y },
                    status: i === steps.length - 1 ? 'active' : 'complete',
                    stepIndex: i
                };
            } else {
                agentMap[agentKey].status = i === steps.length - 1 ? 'active' : 'complete';
            }

            // Create connection to previous agent
            if (i > 0) {
                const prevAgentDef = getAgentInfo(steps[i - 1].agent);
                const prevAgentKey = prevAgentDef.name.toLowerCase().replace(/[-_\s]/g, '');
                if (prevAgentKey !== agentKey && agentMap[prevAgentKey]) {
                    conns.push({
                        from: agentMap[prevAgentKey].position,
                        to: agentMap[agentKey].position,
                        fromAgent: prevAgentKey,
                        toAgent: agentKey,
                        color: agentDef.color,
                        type: determineInteractionType(step),
                        isActive: i === steps.length - 1
                    });
                }
            }
        });

        setActiveAgents(Object.values(agentMap));
        setConnections(conns);
    }, [steps]);

    const determineInteractionType = (step) => {
        const action = (step.action || step.message || '').toLowerCase();
        if (action.includes('routing') || action.includes('handoff')) return 'handoff';
        if (action.includes('query') || action.includes('search')) return 'query';
        if (action.includes('result') || action.includes('found')) return 'response';
        if (action.includes('collaborat') || action.includes('together')) return 'collaborate';
        if (action.includes('verify') || action.includes('check')) return 'verify';
        if (action.includes('refin') || action.includes('improv')) return 'refine';
        return 'handoff';
    };

    // Auto-scroll into view when component renders or steps update
    useEffect(() => {
        if (containerRef.current && (steps?.length > 0 || isLoading)) {
            // Use setTimeout to ensure DOM has updated
            setTimeout(() => {
                containerRef.current?.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
            }, 100);
        }
    }, [steps, isLoading]);

    if (!isLoading && (!steps || steps.length === 0)) return null;

    return (
        <div className="agent-thinking-cinematic-container" ref={containerRef}>
            {/* Header */}
            <div className="cinematic-header">
                <div className="header-orb">
                    <span className="orb-icon">🧠</span>
                    <div className="orb-rings"></div>
                </div>
                <div className="header-text">
                    <h4>AI Agents Collaborating</h4>
                    <p>{steps?.length || 0} agents working on your query</p>
                </div>
            </div>

            {/* Main visualization */}
            <div className="visualization-container">
                <svg
                    ref={svgRef}
                    viewBox="0 0 800 360"
                    className="agent-svg"
                    preserveAspectRatio="xMidYMid meet"
                >
                    {/* Gradient definitions */}
                    <defs>
                        {Object.values(AGENTS).map(agent => (
                            <radialGradient key={agent.name} id={`gradient-${agent.name}`}>
                                <stop offset="0%" stopColor={agent.color} stopOpacity="0.9" />
                                <stop offset="70%" stopColor={agent.color} stopOpacity="0.7" />
                                <stop offset="100%" stopColor={agent.color} stopOpacity="0.5" />
                            </radialGradient>
                        ))}

                        {/* Glow filter */}
                        <filter id="glow" x="-50%" y="-50%" width="200%" height="200%">
                            <feGaussianBlur stdDeviation="3" result="blur" />
                            <feMerge>
                                <feMergeNode in="blur" />
                                <feMergeNode in="SourceGraphic" />
                            </feMerge>
                        </filter>
                    </defs>

                    {/* Background ambient effect */}
                    <circle
                        cx="400"
                        cy="180"
                        r="150"
                        fill="none"
                        stroke="rgba(99, 102, 241, 0.1)"
                        strokeWidth="60"
                        className="ambient-circle"
                    />

                    {/* Connections */}
                    {connections.map((conn, i) => (
                        <AgentConnection key={i} {...conn} />
                    ))}

                    {/* Agent avatars */}
                    {activeAgents.map((agent, i) => (
                        <AgentAvatar
                            key={agent.key}
                            agent={agent}
                            status={agent.status}
                            position={agent.position}
                            onHover={setHoveredAgent}
                        />
                    ))}
                </svg>

                {/* Hovered agent tooltip */}
                {hoveredAgent && (
                    <div className="agent-tooltip-cinematic">
                        <span className="tooltip-emoji">{hoveredAgent.emoji}</span>
                        <div className="tooltip-content">
                            <strong>{hoveredAgent.name}</strong>
                            <span>{hoveredAgent.role}</span>
                        </div>
                    </div>
                )}
            </div>

            {/* Progress indicator */}
            {isLoading && (
                <div className="cinematic-progress">
                    <div className="progress-track">
                        <div className="progress-glow"></div>
                    </div>
                    <span className="progress-label">Agents synthesizing response...</span>
                </div>
            )}
        </div>
    );
};

export default AgentThinkingCinematic;
