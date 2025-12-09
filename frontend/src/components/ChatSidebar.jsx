// Updated ChatSidebar with imperative refresh method
import React, { useState, useEffect, useImperativeHandle, forwardRef, useMemo } from 'react';
import './ChatSidebar.css';

const ChatSidebar = forwardRef(({ userId, currentConversationId, onConversationSelect, onNewChat }, ref) => {
    const [conversations, setConversations] = useState({
        today: [],
        yesterday: [],
        this_week: [],
        older: []
    });
    const [loading, setLoading] = useState(true);
    const [searchQuery, setSearchQuery] = useState('');

    useEffect(() => {
        loadConversations();
    }, [userId]);

    const loadConversations = async () => {
        try {
            const response = await fetch(`http://localhost:8000/conversations?user_id=${userId}`);
            const data = await response.json();

            if (data.status === 'success') {
                setConversations(data.conversations);
            }
        } catch (error) {
            console.error('Failed to load conversations:', error);
        } finally {
            setLoading(false);
        }
    };

    // Expose refresh method to parent
    useImperativeHandle(ref, () => ({
        refreshConversations: loadConversations
    }));

    const deleteConversation = async (conversationId, e) => {
        e.stopPropagation();

        if (!confirm('Delete this conversation?')) return;

        try {
            await fetch(`http://localhost:8000/conversations/${conversationId}`, {
                method: 'DELETE'
            });
            loadConversations();
        } catch (error) {
            console.error('Failed to delete conversation:', error);
        }
    };

    const pinConversation = async (conversationId, isPinned, e) => {
        e.stopPropagation();

        try {
            await fetch(`http://localhost:8000/conversations/${conversationId}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ is_pinned: !isPinned })
            });
            loadConversations();
        } catch (error) {
            console.error('Failed to pin conversation:', error);
        }
    };

    const ConversationItem = ({ conv }) => (
        <div
            className={`conversation-item ${conv.id === currentConversationId ? 'active' : ''}`}
            onClick={() => onConversationSelect(conv.id)}
        >
            <div className="conversation-content">
                <div className="conversation-title">
                    {conv.is_pinned && <span className="pin-icon">📌</span>}
                    {conv.title}
                </div>
                <div className="conversation-meta">
                    {conv.message_count} messages • {formatDate(conv.updated_at)}
                </div>
            </div>
            <div className="conversation-actions">
                <button
                    className="icon-btn"
                    onClick={(e) => pinConversation(conv.id, conv.is_pinned, e)}
                    title={conv.is_pinned ? 'Unpin' : 'Pin'}
                >
                    {conv.is_pinned ? '📌' : '📍'}
                </button>
                <button
                    className="icon-btn"
                    onClick={(e) => deleteConversation(conv.id, e)}
                    title="Delete"
                >
                    🗑️
                </button>
            </div>
        </div>
    );

    const ConversationGroup = ({ title, conversations }) => {
        if (!conversations || conversations.length === 0) return null;

        return (
            <div className="conversation-group">
                <div className="group-title">{title}</div>
                {conversations.map(conv => (
                    <ConversationItem key={conv.id} conv={conv} />
                ))}
            </div>
        );
    };

    const formatDate = (dateString) => {
        const date = new Date(dateString);
        const now = new Date();
        const diffHours = (now - date) / (1000 * 60 * 60);

        if (diffHours < 1) return 'Just now';
        if (diffHours < 24) return `${Math.floor(diffHours)}h ago`;
        return date.toLocaleDateString();
    };

    // Memoized filtered conversations to prevent re-filtering on every render
    const filteredConversations = useMemo(() => {
        if (!searchQuery.trim()) return conversations;

        const filterConvs = (convs) => {
            return convs.filter(conv =>
                conv.title.toLowerCase().includes(searchQuery.toLowerCase())
            );
        };

        return {
            today: filterConvs(conversations.today),
            yesterday: filterConvs(conversations.yesterday),
            this_week: filterConvs(conversations.this_week),
            older: filterConvs(conversations.older)
        };
    }, [conversations, searchQuery]);

    if (loading) {
        return <div className="sidebar-loading">Loading conversations...</div>;
    }

    return (
        <div className="chat-sidebar">
            <div className="sidebar-header">
                <h2>Conversations</h2>
                <button className="new-chat-btn" onClick={onNewChat}>
                    ➕ New Chat
                </button>
            </div>

            <div className="sidebar-search">
                <input
                    type="text"
                    placeholder="Search conversations..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                />
            </div>

            <div className="conversations-list">
                <ConversationGroup title="Today" conversations={filteredConversations.today} />
                <ConversationGroup title="Yesterday" conversations={filteredConversations.yesterday} />
                <ConversationGroup title="This Week" conversations={filteredConversations.this_week} />
                <ConversationGroup title="Older" conversations={filteredConversations.older} />
            </div>

            <div className="sidebar-footer">
                <div className="user-info">
                    <span className="user-avatar">👤</span>
                    <span className="user-name">User {userId}</span>
                </div>
            </div>
        </div>
    );
});

export default ChatSidebar;
