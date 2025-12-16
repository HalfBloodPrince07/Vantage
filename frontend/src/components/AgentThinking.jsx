// AgentThinking.jsx - Animated AI Agents Thinking Display
import React from 'react';
import './AgentThinking.css';

// Agent definitions with personality
const AGENTS = {
    zeus: { name: 'Zeus', emoji: '⚡', color: '#f59e0b', role: 'Orchestrator' },
    athena: { name: 'Athena', emoji: '🦉', color: '#8b5cf6', role: 'Search Strategist' },
    apollo: { name: 'Apollo', emoji: '☀️', color: '#f97316', role: 'Graph Explorer' },
    proteus: { name: 'Proteus', emoji: '🔄', color: '#06b6d4', role: 'Adaptive Ranker' },
    odysseus: { name: 'Odysseus', emoji: '🧭', color: '#10b981', role: 'Multi-hop Reasoner' },
    themis: { name: 'Themis', emoji: '⚖️', color: '#ec4899', role: 'Confidence Scorer' },
    daedalus: { name: 'Daedalus', emoji: '🏛️', color: '#3b82f6', role: 'Document Analyst' },
    prometheus: { name: 'Prometheus', emoji: '🔥', color: '#ef4444', role: 'Text Extractor' },
    hypatia: { name: 'Hypatia', emoji: '📚', color: '#a855f7', role: 'Semantic Analyzer' },
    mnemosyne: { name: 'Mnemosyne', emoji: '🧠', color: '#14b8a6', role: 'Memory Keeper' },
    default: { name: 'AI Agent', emoji: '🤖', color: '#6366f1', role: 'Processing' }
};

const AgentThinking = ({ steps, isLoading }) => {
    if (!isLoading && (!steps || steps.length === 0)) return null;

    const getAgent = (agentName) => {
        if (!agentName) return AGENTS.default;
        const key = agentName.toLowerCase().replace(/[-_\s]/g, '');
        return AGENTS[key] || AGENTS.default;
    };

    return (
        <div className="agent-thinking-container">
            <div className="thinking-header">
                <div className="thinking-icon-container">
                    <div className="thinking-orb"></div>
                    <span className="thinking-icon">🧠</span>
                </div>
                <div className="thinking-title">
                    <h4>AI Agents Processing</h4>
                    <p>Multiple specialized agents working on your query</p>
                </div>
            </div>

            <div className="agent-pipeline">
                {steps && steps.map((step, index) => {
                    const agent = getAgent(step.agent);
                    const isLatest = index === steps.length - 1;

                    return (
                        <div
                            key={index}
                            className={`agent-step ${isLatest ? 'latest' : ''}`}
                            style={{ '--agent-color': agent.color }}
                        >
                            <div className="step-connector">
                                <div className="connector-line"></div>
                                <div className="connector-dot" style={{ background: agent.color }}></div>
                            </div>

                            <div className="step-card">
                                <div className="agent-avatar" style={{ background: `${agent.color}20`, borderColor: agent.color }}>
                                    <span className="agent-emoji">{agent.emoji}</span>
                                    {isLatest && <div className="avatar-pulse" style={{ borderColor: agent.color }}></div>}
                                </div>

                                <div className="step-details">
                                    <div className="agent-info">
                                        <span className="agent-name" style={{ color: agent.color }}>{agent.name}</span>
                                        <span className="agent-role">{agent.role}</span>
                                    </div>
                                    <div className="step-action">{step.action || step.message || 'Processing...'}</div>
                                    {step.details && (
                                        <div className="step-extra">{step.details}</div>
                                    )}
                                </div>

                                <div className="step-status">
                                    {isLatest ? (
                                        <div className="status-working">
                                            <span className="status-dot"></span>
                                            Working
                                        </div>
                                    ) : (
                                        <div className="status-done">✓</div>
                                    )}
                                </div>
                            </div>
                        </div>
                    );
                })}

                {isLoading && (!steps || steps.length === 0) && (
                    <div className="initial-loading">
                        <div className="loading-agents">
                            {['⚡', '🦉', '☀️', '🧭', '⚖️'].map((emoji, i) => (
                                <div key={i} className="floating-agent" style={{ animationDelay: `${i * 0.2}s` }}>
                                    {emoji}
                                </div>
                            ))}
                        </div>
                        <p>Initializing AI agents...</p>
                    </div>
                )}
            </div>

            {isLoading && (
                <div className="thinking-progress">
                    <div className="progress-bar">
                        <div className="progress-fill"></div>
                    </div>
                    <span className="progress-text">Agents collaborating...</span>
                </div>
            )}
        </div>
    );
};

export default AgentThinking;
