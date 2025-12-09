// Updated OnboardingWizard with Sign Up / Sign In first screen
import React, { useState, useRef } from 'react';
import './LoginSettings.css';
import './OnboardingWizard.css';

const OnboardingWizard = ({ onComplete }) => {
    const [step, setStep] = useState(0); // 0: choice, 1: auth, 2: setup
    const [authMode, setAuthMode] = useState(null); // 'signup' or 'signin'
    const [userId, setUserId] = useState('');
    const [password, setPassword] = useState('');
    const [confirmPassword, setConfirmPassword] = useState('');
    const [selectedFolder, setSelectedFolder] = useState('');
    const [selectedFiles, setSelectedFiles] = useState([]);
    const [indexMethod, setIndexMethod] = useState('path');
    const [enableWatcher, setEnableWatcher] = useState(false);
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);
    const fileInputRef = useRef(null);
    const folderInputRef = useRef(null);

    const handleAuthModeSelect = (mode) => {
        setAuthMode(mode);
        setStep(1);
    };

    const handleLogin = async () => {
        if (!userId.trim() || !password.trim()) {
            setError('Please enter user ID and password');
            return;
        }

        if (authMode === 'signup' && password !== confirmPassword) {
            setError('Passwords do not match');
            return;
        }

        if (authMode === 'signup' && password.length < 6) {
            setError('Password must be at least 6 characters');
            return;
        }

        setLoading(true);
        setError('');

        try {
            const endpoint = authMode === 'signup' ? '/auth/register' : '/auth/login';

            // Use relative path /api which Vite proxies to backend
            const response = await fetch(`/api${endpoint}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ user_id: userId, password })
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.detail || 'Authentication failed');
            }

            if (authMode === 'signup') {
                // Register successful, now login
                const loginResponse = await fetch('/api/auth/login', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ user_id: userId, password })
                });

                const loginData = await loginResponse.json();

                if (loginResponse.ok) {
                    localStorage.setItem('locallens_session_token', loginData.session_token);
                    localStorage.setItem('locallens_user', userId);
                    setStep(2);
                }
            } else {
                localStorage.setItem('locallens_session_token', data.session_token);
                localStorage.setItem('locallens_user', userId);
                setStep(2);
            }
        } catch (error) {
            setError(error.message);
        } finally {
            setLoading(false);
        }
    };

    const generateRandomUserId = () => {
        const randomId = `user_${Math.floor(Math.random() * 10000).toString().padStart(4, '0')}`;
        setUserId(randomId);
    };

    const handleBrowseFiles = () => {
        fileInputRef.current?.click();
    };

    const handleBrowseFolder = () => {
        folderInputRef.current?.click();
    };

    const handleFilesSelected = (e) => {
        const files = Array.from(e.target.files);
        setSelectedFiles(files);
        setIndexMethod('files');
    };

    const handleFolderSelected = (e) => {
        const files = Array.from(e.target.files);
        setSelectedFiles(files);
        setIndexMethod('files');

        if (files.length > 0) {
            const folderName = files[0].webkitRelativePath.split('/')[0];
            setSelectedFolder(folderName);
        }
    };

    const enableFileWatcher = async (directory) => {
        try {
            await fetch('http://localhost:8000/watcher/enable', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ directory_path: directory })
            });
            console.log('[Watcher] Enabled for directory:', directory);
        } catch (error) {
            console.error('[Watcher] Failed to enable:', error);
        }
    };

    const startIndexing = async () => {
        try {
            let taskId = null;
            let watchDirectory = null;

            if (indexMethod === 'path' && selectedFolder) {
                watchDirectory = selectedFolder;

                const response = await fetch('http://localhost:8000/index/directory', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        directory_path: selectedFolder,
                        recursive: true
                    })
                });

                const result = await response.json();
                if (result.status === 'success') {
                    taskId = result.task_id;
                }
            } else if (indexMethod === 'files' && selectedFiles.length > 0) {
                taskId = `upload_${Date.now()}`;

                setTimeout(async () => {
                    const formData = new FormData();
                    selectedFiles.forEach(file => formData.append('files', file));

                    try {
                        await fetch('http://localhost:8000/upload-batch', {
                            method: 'POST',
                            body: formData
                        });
                    } catch (error) {
                        console.error('Upload error:', error);
                    }
                }, 1000);
            }

            if (enableWatcher && watchDirectory) {
                await enableFileWatcher(watchDirectory);
            }

            completeOnboarding(taskId, enableWatcher, watchDirectory);
        } catch (error) {
            console.error('Indexing error:', error);
            completeOnboarding(null, enableWatcher, null);
        }
    };

    const skipIndexing = () => {
        completeOnboarding(null, false, null);
    };

    const completeOnboarding = (taskId, watcherEnabled, watchDirectory) => {
        localStorage.setItem('locallens_onboarding_complete', 'true');
        if (watcherEnabled && watchDirectory) {
            localStorage.setItem('locallens_watcher_enabled', 'true');
            localStorage.setItem('locallens_watch_directory', watchDirectory);
        }
        onComplete(userId, taskId, watcherEnabled);
    };

    // Step 0: Sign Up or Sign In Choice
    if (step === 0) {
        return (
            <div className="login-overlay">
                <div className="login-container">
                    <h1>🔍 LocalLens</h1>
                    <p>AI-Powered Document Search</p>

                    <div className="auth-choice">
                        <h2>Welcome!</h2>
                        <p className="choice-subtitle">Choose an option to get started</p>

                        <div className="choice-buttons">
                            <button
                                className="choice-btn signup"
                                onClick={() => handleAuthModeSelect('signup')}
                            >
                                <div className="choice-icon">✨</div>
                                <div className="choice-title">Sign Up</div>
                                <div className="choice-desc">Create a new account</div>
                            </button>

                            <button
                                className="choice-btn signin"
                                onClick={() => handleAuthModeSelect('signin')}
                            >
                                <div className="choice-icon">🔓</div>
                                <div className="choice-title">Sign In</div>
                                <div className="choice-desc">Access your account</div>
                            </button>
                        </div>
                    </div>

                    <div className="login-footer">
                        <small>LocalLens v2.0 - Secure Document Assistant</small>
                    </div>
                </div>
            </div>
        );
    }

    // Step 1: Authentication (Sign Up or Sign In)
    if (step === 1) {
        return (
            <div className="login-overlay">
                <div className="login-container">
                    <button className="back-btn" onClick={() => setStep(0)}>
                        ← Back
                    </button>

                    <h1>🔍 LocalLens</h1>
                    <p>{authMode === 'signup' ? 'Create Your Account' : 'Welcome Back'}</p>

                    <div className="wizard-steps">
                        <div className="wizard-step active">1. {authMode === 'signup' ? 'Sign Up' : 'Sign In'}</div>
                        <div className="wizard-step">2. Setup</div>
                    </div>

                    <div className="login-form">
                        <div className="input-group">
                            <input
                                type="text"
                                placeholder="Enter user ID"
                                value={userId}
                                onChange={(e) => setUserId(e.target.value)}
                                className="login-input"
                                autoFocus
                            />
                            {authMode === 'signup' && (
                                <button
                                    className="random-btn"
                                    onClick={generateRandomUserId}
                                    title="Generate random user ID"
                                >
                                    🎲
                                </button>
                            )}
                        </div>

                        <input
                            type="password"
                            placeholder={authMode === 'signup' ? "Create password (min 6 chars)" : "Enter password"}
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            onKeyPress={(e) => e.key === 'Enter' && authMode === 'signin' && handleLogin()}
                            className="login-input"
                        />

                        {authMode === 'signup' && (
                            <input
                                type="password"
                                placeholder="Confirm password"
                                value={confirmPassword}
                                onChange={(e) => setConfirmPassword(e.target.value)}
                                onKeyPress={(e) => e.key === 'Enter' && handleLogin()}
                                className="login-input"
                            />
                        )}

                        {error && <div className="error-message">❌ {error}</div>}

                        <div className="info-box">
                            <strong>🔒 {authMode === 'signup' ? 'Secure Registration' : 'Secure Login'}</strong>
                            <p>{authMode === 'signup'
                                ? 'Create a secure password (min 6 characters) to protect your account'
                                : 'Enter your credentials to access your documents'
                            }</p>
                        </div>

                        <button
                            onClick={handleLogin}
                            disabled={loading || !userId.trim() || !password.trim()}
                            className="login-btn"
                        >
                            {loading ? '⏳ Processing...' : authMode === 'signup' ? '✨ Create Account' : '🔓 Sign In'}
                        </button>
                    </div>

                    <div className="login-footer">
                        <small>LocalLens v2.0</small>
                    </div>
                </div>
            </div>
        );
    }

    // Step 2: Indexing Setup
    return (
        <div className="login-overlay">
            <div className="login-container large">
                <h1>📁 Set Up Document Indexing</h1>
                <p>Index your documents (optional)</p>

                <div className="wizard-steps">
                    <div className="wizard-step completed">✓ {authMode === 'signup' ? 'Registered' : 'Logged In'}</div>
                    <div className="wizard-step active">2. Setup</div>
                </div>

                <div className="login-form">
                    <div className="method-selector">
                        <button
                            className={`method-btn ${indexMethod === 'path' ? 'active' : ''}`}
                            onClick={() => setIndexMethod('path')}
                        >
                            📂 Folder Path
                        </button>
                        <button
                            className={`method-btn ${indexMethod === 'files' ? 'active' : ''}`}
                            onClick={() => setIndexMethod('files')}
                        >
                            📤 Upload Files
                        </button>
                    </div>

                    {indexMethod === 'path' && (
                        <div className="setup-section">
                            <label>Folder Path</label>
                            <input
                                type="text"
                                value={selectedFolder}
                                onChange={(e) => setSelectedFolder(e.target.value)}
                                placeholder="C:\Users\YourName\Documents"
                                className="login-input"
                            />
                            <div className="hint-text">
                                💡 Enter full path to your documents folder
                            </div>
                        </div>
                    )}

                    {indexMethod === 'files' && (
                        <div className="setup-section">
                            <label>Select Files/Folder</label>
                            <div className="file-buttons">
                                <button onClick={handleBrowseFiles} className="browse-btn-secondary">
                                    📄 Files
                                </button>
                                <button onClick={handleBrowseFolder} className="browse-btn-secondary">
                                    📁 Folder
                                </button>
                            </div>

                            <input
                                ref={fileInputRef}
                                type="file"
                                multiple
                                onChange={handleFilesSelected}
                                style={{ display: 'none' }}
                                accept=".pdf,.txt,.docx,.xlsx,.csv,.jpg,.jpeg,.png,.gif"
                            />

                            <input
                                ref={folderInputRef}
                                type="file"
                                webkitdirectory=""
                                multiple
                                onChange={handleFolderSelected}
                                style={{ display: 'none' }}
                            />

                            {selectedFiles.length > 0 && (
                                <div className="selected-files-compact">
                                    ✅ {selectedFiles.length} files selected
                                </div>
                            )}
                        </div>
                    )}

                    {indexMethod === 'path' && (
                        <div className="watcher-option">
                            <label className="checkbox-label">
                                <input
                                    type="checkbox"
                                    checked={enableWatcher}
                                    onChange={(e) => setEnableWatcher(e.target.checked)}
                                />
                                <span>📂 Enable Auto-Index (watch for new files)</span>
                            </label>
                            <div className="hint-text">
                                ✨ Automatically detects and indexes new files
                            </div>
                        </div>
                    )}

                    <div className="button-group">
                        <button
                            onClick={startIndexing}
                            disabled={(indexMethod === 'path' && !selectedFolder) || (indexMethod === 'files' && selectedFiles.length === 0)}
                            className="login-btn"
                        >
                            🚀 Start & Continue
                        </button>

                        <button onClick={skipIndexing} className="skip-btn">
                            Skip for Now →
                        </button>
                    </div>

                    <div className="info-box">
                        <small>💡 Indexing happens in background. Progress shown in bottom-right.</small>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default OnboardingWizard;
