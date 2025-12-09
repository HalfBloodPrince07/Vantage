// frontend/hooks/useDarkMode.js
// Dark mode hook with localStorage persistence

import { useState, useEffect } from 'react';

export const useDarkMode = () => {
    const [isDark, setIsDark] = useState(() => {
        // Check localStorage first
        const saved = localStorage.getItem('darkMode');
        if (saved !== null) {
            return saved === 'true';
        }
        // Otherwise check system preference
        return window.matchMedia('(prefers-color-scheme: dark)').matches;
    });

    useEffect(() => {
        // Update document root
        document.documentElement.setAttribute('data-theme', isDark ? 'dark' : 'light');
        // Save to localStorage
        localStorage.setItem('darkMode', isDark.toString());
    }, [isDark]);

    const toggleDarkMode = () => setIsDark(prev => !prev);

    return [isDark, toggleDarkMode];
};

// Dark mode toggle button component
export const DarkModeToggle = ({ isDark, toggle }) => (
    <button
        className="dark-mode-toggle"
        onClick={toggle}
        title={isDark ? 'Switch to light mode' : 'Switch to dark mode'}
        aria-label="Toggle dark mode"
    >
        {isDark ? '☀️' : '🌙'}
    </button>
);
