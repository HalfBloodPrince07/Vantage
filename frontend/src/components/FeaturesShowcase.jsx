import React, { useState, useEffect, useRef } from 'react';
import './FeaturesShowcase.css';

// AI Agents data for the orbit
const AGENTS = [
    { icon: '⚡', name: 'Zeus', role: 'Master Orchestrator', position: 'primary' },
    { icon: '🧠', name: 'Athena', role: 'Query Classifier', position: 'primary' },
    { icon: '🔮', name: 'Proteus', role: 'Adaptive Retriever', position: 'primary' },
    { icon: '☀️', name: 'Apollo', role: 'Graph Expander', position: 'primary' },
    { icon: '🚀', name: 'Odysseus', role: 'Multi-hop Reasoning', position: 'secondary' },
    { icon: '✍️', name: 'Hermes', role: 'Result Explainer', position: 'secondary' },
    { icon: '🔍', name: 'Diogenes', role: 'Quality Critic', position: 'secondary' },
    { icon: '⚖️', name: 'Themis', role: 'Confidence Scorer', position: 'secondary' },
];

// Features data
const FEATURES = [
    {
        icon: '🤖',
        title: 'AI Agents',
        shortDesc: '11 specialized agents',
        fullDesc: 'A symphony of 11 AI agents work together - Zeus orchestrates, Athena classifies, Proteus retrieves, and more. Each agent has a unique role in understanding your queries.'
    },
    {
        icon: '🔍',
        title: 'Hybrid Search',
        shortDesc: 'Semantic + Keywords',
        fullDesc: 'Combines the power of semantic vector search with traditional BM25 keyword matching for precise, context-aware document retrieval.'
    },
    {
        icon: '📊',
        title: 'Knowledge Graph',
        shortDesc: 'Visual connections',
        fullDesc: 'Automatically extracts entities, keywords, and topics from your documents, visualizing them as an interactive knowledge graph.'
    },
    {
        icon: '📁',
        title: 'Doc Intelligence',
        shortDesc: 'PDF, DOCX, Images...',
        fullDesc: 'Process any document type - PDFs, Word docs, spreadsheets, and even images. AI-powered summarization and entity extraction included.'
    },
    {
        icon: '🧬',
        title: 'A-Mem',
        shortDesc: 'Agentic Memory',
        fullDesc: 'Self-evolving Agentic Memory (A-Mem) creates structured notes, evolves knowledge over time, and learns from every interaction for truly intelligent personalization.'
    },
    {
        icon: '⚡',
        title: 'Neural Ranking',
        shortDesc: 'Cross-encoder precision',
        fullDesc: 'Uses a cross-encoder neural reranker for maximum precision, ensuring the most relevant documents always appear first.'
    }
];

const FeaturesShowcase = () => {
    const [activeFeature, setActiveFeature] = useState(0);
    const [isAnimated, setIsAnimated] = useState(false);
    const carouselRef = useRef(null);

    // Trigger entrance animation on mount
    useEffect(() => {
        const timer = setTimeout(() => setIsAnimated(true), 100);
        return () => clearTimeout(timer);
    }, []);

    // Auto-rotate features
    useEffect(() => {
        const interval = setInterval(() => {
            setActiveFeature(prev => (prev + 1) % FEATURES.length);
        }, 4000);
        return () => clearInterval(interval);
    }, []);

    // Scroll carousel to active feature
    useEffect(() => {
        if (carouselRef.current) {
            const track = carouselRef.current;
            const cards = track.children;
            if (cards[activeFeature]) {
                const card = cards[activeFeature];
                const scrollLeft = card.offsetLeft - (track.clientWidth / 2) + (card.clientWidth / 2);
                track.scrollTo({ left: scrollLeft, behavior: 'smooth' });
            }
        }
    }, [activeFeature]);

    const handleFeatureClick = (index) => {
        setActiveFeature(index);
    };

    const primaryAgents = AGENTS.filter(a => a.position === 'primary');
    const secondaryAgents = AGENTS.filter(a => a.position === 'secondary');

    return (
        <div className={`features-showcase ${isAnimated ? 'animate-in' : ''}`}>
            <div className="features-showcase-inner">
                {/* Agent Orbit */}
                <div className="agent-orbit-container">
                    <div className="orbit-center">🔍</div>

                    {/* Primary orbit ring with agents */}
                    <div className="orbit-ring primary">
                        {primaryAgents.map((agent, idx) => (
                            <div key={agent.name} className="orbit-agent">
                                {agent.icon}
                                <div className="agent-tooltip">
                                    <div className="agent-name">{agent.name}</div>
                                    <div className="agent-role">{agent.role}</div>
                                </div>
                            </div>
                        ))}
                    </div>

                    {/* Secondary orbit ring with agents */}
                    <div className="orbit-ring secondary">
                        {secondaryAgents.map((agent, idx) => (
                            <div key={agent.name} className="orbit-agent">
                                {agent.icon}
                                <div className="agent-tooltip">
                                    <div className="agent-name">{agent.name}</div>
                                    <div className="agent-role">{agent.role}</div>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>

                {/* Feature Cards Carousel */}
                <div className="features-carousel">
                    <div className="features-carousel-track" ref={carouselRef}>
                        {FEATURES.map((feature, idx) => (
                            <div
                                key={feature.title}
                                className={`feature-card ${activeFeature === idx ? 'active' : ''}`}
                                onClick={() => handleFeatureClick(idx)}
                            >
                                <span className="feature-icon">{feature.icon}</span>
                                <div className="feature-title">{feature.title}</div>
                                <div className="feature-desc">{feature.shortDesc}</div>
                            </div>
                        ))}
                    </div>

                    {/* Navigation dots */}
                    <div className="carousel-dots">
                        {FEATURES.map((_, idx) => (
                            <button
                                key={idx}
                                className={`carousel-dot ${activeFeature === idx ? 'active' : ''}`}
                                onClick={() => handleFeatureClick(idx)}
                                aria-label={`Go to feature ${idx + 1}`}
                            />
                        ))}
                    </div>
                </div>

                {/* Active Feature Detail */}
                <div className="feature-detail" key={activeFeature}>
                    <div className="feature-detail-title">
                        {FEATURES[activeFeature].icon} {FEATURES[activeFeature].title}
                    </div>
                    <div className="feature-detail-desc">
                        {FEATURES[activeFeature].fullDesc}
                    </div>
                </div>

                {/* Stats Bar */}
                <div className="stats-bar">
                    <div className="stat-item">
                        <div className="stat-value">11</div>
                        <div className="stat-label">AI Agents</div>
                    </div>
                    <div className="stat-item">
                        <div className="stat-value">∞</div>
                        <div className="stat-label">Documents</div>
                    </div>
                    <div className="stat-item">
                        <div className="stat-value">100%</div>
                        <div className="stat-label">Local</div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default FeaturesShowcase;
