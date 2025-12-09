// frontend/components/ConversationExporter.jsx
// Export conversation to file functionality

export const exportConversation = async (conversationId) => {
    try {
        // Fetch conversation details
        const convResponse = await fetch(`http://localhost:8000/conversations/${conversationId}`);
        const convData = await convResponse.json();

        // Fetch messages
        const msgResponse = await fetch(`http://localhost:8000/conversations/${conversationId}/messages`);
        const msgData = await msgResponse.json();

        if (convData.status !== 'success' || msgData.status !== 'success') {
            throw new Error('Failed to fetch conversation data');
        }

        const conversation = convData.conversation;
        const messages = msgData.messages;

        // Format as markdown
        let markdown = `# ${conversation.title}\n\n`;
        markdown += `**Created:** ${new Date(conversation.created_at).toLocaleString()}\n`;
        markdown += `**Updated:** ${new Date(conversation.updated_at).toLocaleString()}\n`;
        markdown += `**Messages:** ${conversation.message_count}\n\n`;
        markdown += `---\n\n`;

        messages.forEach((msg, idx) => {
            const timestamp = new Date(msg.timestamp).toLocaleString();
            const role = msg.role === 'user' ? '👤 User' : '🤖 Assistant';

            markdown += `## ${role} - ${timestamp}\n\n`;
            markdown += `${msg.content}\n\n`;

            if (msg.results && msg.results.length > 0) {
                markdown += `### Results (${msg.results.length})\n\n`;
                msg.results.forEach((result, i) => {
                    markdown += `${i + 1}. **${result.filename}** (${(result.score * 100).toFixed(0)}% match)\n`;
                    markdown += `   ${result.content_summary || result.text?.substring(0, 150)}...\n\n`;
                });
            }

            markdown += `---\n\n`;
        });

        // Create download
        const blob = new Blob([markdown], { type: 'text/markdown' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `conversation_${conversation.title.replace(/[^a-z0-9]/gi, '_')}_${Date.now()}.md`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);

        return true;
    } catch (error) {
        console.error('Export failed:', error);
        return false;
    }
};

// Export as JSON
export const exportConversationJSON = async (conversationId) => {
    try {
        const convResponse = await fetch(`http://localhost:8000/conversations/${conversationId}`);
        const msgResponse = await fetch(`http://localhost:8000/conversations/${conversationId}/messages`);

        const convData = await convResponse.json();
        const msgData = await msgResponse.json();

        const exportData = {
            conversation: convData.conversation,
            messages: msgData.messages,
            exported_at: new Date().toISOString()
        };

        const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `conversation_${conversationId}_${Date.now()}.json`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);

        return true;
    } catch (error) {
        console.error('Export failed:', error);
        return false;
    }
};
