// AIAgentAvatar.jsx - Animated AI agent representations
import React from 'react';
import './AIAgentAvatar.css';

const AIAgentAvatar = ({
    name = 'Agent',
    icon = '🤖',
    status = 'idle', // idle, thinking, responding, success
    size = 'medium', // small, medium, large
    showLabel = true,
    onClick,
    className = ''
}) => {
    const sizeClasses = {
        small: 'agent-avatar-sm',
        medium: 'agent-avatar-md',
        large: 'agent-avatar-lg'
    };

    return (
        <div
            className={`ai-agent-wrapper ${className}`}
            onClick={onClick}
        >
            <div className={`ai-agent-avatar-container ${sizeClasses[size]} ${status}`}>
                {/* Orbital rings for thinking state */}
                <div className="orbit-ring orbit-1"></div>
                <div className="orbit-ring orbit-2"></div>

                {/* Main avatar */}
                <div className="agent-core">
                    <span className="agent-icon">{icon}</span>
                </div>

                {/* Pulse waves for responding state */}
                <div className="pulse-wave pulse-1"></div>
                <div className="pulse-wave pulse-2"></div>
                <div className="pulse-wave pulse-3"></div>

                {/* Success indicator */}
                <div className="success-ring"></div>
            </div>

            {showLabel && (
                <span className={`agent-label ${status}`}>{name}</span>
            )}
        </div>
    );
};

// Agent communication line component
export const AgentConnectionLine = ({
    active = false,
    direction = 'right' // left, right, up, down
}) => {
    return (
        <div className={`agent-connection-line ${direction} ${active ? 'active' : ''}`}>
            <div className="connection-path">
                <div className="data-packet"></div>
                <div className="data-packet delay-1"></div>
                <div className="data-packet delay-2"></div>
            </div>
        </div>
    );
};

export default AIAgentAvatar;
