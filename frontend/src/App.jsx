import React, { useState } from 'react';
import ChatInterface from './components/ChatInterface';
import OnboardingWizard from './components/OnboardingWizard';
import IndexingProgress from './components/IndexingProgress';
import CreatorBadge from './components/CreatorBadge';
import AmbientParticles from './components/AmbientParticles';
import { useDarkMode, DarkModeToggle } from './hooks/useDarkMode.jsx';
import './styles/dark-mode.css';
import './styles/ai-dashboard.css';
import './components/OnboardingWizard.css';
import './components/IndexingProgress.css';

function App() {
    const [isDark, toggleDarkMode] = useDarkMode();
    const [isLoggedIn, setIsLoggedIn] = useState(false);
    const [userId, setUserId] = useState('');
    const [indexingTaskId, setIndexingTaskId] = useState(null);

    const handleOnboardingComplete = (user, taskId, watcherEnabled) => {
        setUserId(user);
        setIsLoggedIn(true);
        if (taskId) {
            setIndexingTaskId(taskId);
        }

        // Enable watcher if requested
        if (watcherEnabled) {
            enableFileWatcher();
        }
    };

    const handleLogout = () => {
        setUserId('');
        setIsLoggedIn(false);
        setIndexingTaskId(null);
        localStorage.removeItem('locallens_user');
        localStorage.removeItem('locallens_onboarding_complete');
    };

    const enableFileWatcher = async () => {
        try {
            // Call backend to enable watcher
            await fetch('http://localhost:8000/watcher/enable', {
                method: 'POST'
            });
        } catch (error) {
            console.error('Failed to enable watcher:', error);
        }
    };

    const handleIndexingComplete = () => {
        setIndexingTaskId(null);
    };

    const handleIndexingStart = (taskId) => {
        console.log('[App] Indexing started with task:', taskId);
        setIndexingTaskId(taskId);
    };

    // Check for existing session on mount
    React.useEffect(() => {
        const savedUser = localStorage.getItem('locallens_user');
        const onboardingComplete = localStorage.getItem('locallens_onboarding_complete');

        if (savedUser && onboardingComplete) {
            setUserId(savedUser);
            setIsLoggedIn(true);
        }
    }, []);

    if (!isLoggedIn) {
        return <OnboardingWizard onComplete={handleOnboardingComplete} />;
    }

    return (
        <>
            {/* Subtle ambient particles in background */}
            <AmbientParticles particleCount={20} />

            <ChatInterface
                userId={userId}
                onLogout={handleLogout}
                onIndexingStart={handleIndexingStart}
                key={userId}
            />
            <DarkModeToggle isDark={isDark} toggle={toggleDarkMode} />

            {/* Show indexing progress in bottom-right */}
            {indexingTaskId && (
                <IndexingProgress
                    taskId={indexingTaskId}
                    onComplete={handleIndexingComplete}
                />
            )}
        </>
    );
}

export default App;
