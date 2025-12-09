// frontend/hooks/useKeyboardShortcuts.js
// Keyboard shortcuts hook for chat interface

import { useEffect } from 'react';

export const useKeyboardShortcuts = ({
    onNewChat,
    onSearch,
    onFocusSearch,
    onToggleSidebar,
    onExportConversation
}) => {
    useEffect(() => {
        const handleKeyDown = (e) => {
            // Ctrl/Cmd + K - Focus search
            if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
                e.preventDefault();
                onFocusSearch?.();
            }

            // Ctrl/Cmd + N - New chat
            if ((e.ctrlKey || e.metaKey) && e.key === 'n') {
                e.preventDefault();
                onNewChat?.();
            }

            // Ctrl/Cmd + Enter - Submit search
            if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
                e.preventDefault();
                onSearch?.();
            }

            // Ctrl/Cmd + B - Toggle sidebar
            if ((e.ctrlKey || e.metaKey) && e.key === 'b') {
                e.preventDefault();
                onToggleSidebar?.();
            }

            // Ctrl/Cmd + E - Export conversation
            if ((e.ctrlKey || e.metaKey) && e.key === 'e') {
                e.preventDefault();
                onExportConversation?.();
            }

            // ESC - Clear input or close modals
            if (e.key === 'Escape') {
                // Handler can be customized per component
            }
        };

        window.addEventListener('keydown', handleKeyDown);
        return () => window.removeEventListener('keydown', handleKeyDown);
    }, [onNewChat, onSearch, onFocusSearch, onToggleSidebar, onExportConversation]);
};

// Keyboard shortcuts help component
export const KeyboardShortcutsHelp = () => (
    <div className="keyboard-shortcuts-help">
        <h3>⌨️ Keyboard Shortcuts</h3>
        <div className="shortcut-list">
            <div className="shortcut-item">
                <kbd>Ctrl</kbd> + <kbd>K</kbd>
                <span>Focus search</span>
            </div>
            <div className="shortcut-item">
                <kbd>Ctrl</kbd> + <kbd>N</kbd>
                <span>New chat</span>
            </div>
            <div className="shortcut-item">
                <kbd>Ctrl</kbd> + <kbd>Enter</kbd>
                <span>Submit search</span>
            </div>
            <div className="shortcut-item">
                <kbd>Ctrl</kbd> + <kbd>B</kbd>
                <span>Toggle sidebar</span>
            </div>
            <div className="shortcut-item">
                <kbd>Ctrl</kbd> + <kbd>E</kbd>
                <span>Export conversation</span>
            </div>
            <div className="shortcut-item">
                <kbd>Esc</kbd>
                <span>Close/Cancel</span>
            </div>
        </div>
        <style jsx>{`
      .keyboard-shortcuts-help {
        padding: 20px;
        background: white;
        border-radius: 12px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.1);
      }
      .shortcut-list {
        display: flex;
        flex-direction: column;
        gap: 10px;
        margin-top: 15px;
      }
      .shortcut-item {
        display: flex;
        align-items: center;
        gap: 10px;
      }
      .shortcut-item kbd {
        background: #f5f5f5;
        border: 1px solid #ddd;
        border-radius: 4px;
        padding: 4px 8px;
        font-family: monospace;
        font-size: 12px;
      }
      .shortcut-item span {
        color: #666;
        font-size: 14px;
      }
    `}</style>
    </div>
);
