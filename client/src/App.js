import React, { useState, useEffect } from 'react';
import './App.css';
import LoginScreen from './components/LoginScreen';
import SessionSetup from './components/SessionSetup';
import ActiveSession from './components/ActiveSession';
import SuccessScreen from './components/SuccessScreen';
import RecoveryDialog from './components/RecoveryDialog';
import { checkForRecovery } from './services/recoveryService';

function App() {
  const [screen, setScreen] = useState('login');
  const [user, setUser] = useState(null);
  const [sessionData, setSessionData] = useState(null);
  const [recoveryData, setRecoveryData] = useState(null);

  useEffect(() => {
    // Check for OAuth callback (check both URL search params and hash)
    const urlParams = new URLSearchParams(window.location.search);
    const hashParams = new URLSearchParams(window.location.hash.substring(1));
    const accessToken = urlParams.get('access_token') || hashParams.get('access_token');
    const refreshToken = urlParams.get('refresh_token') || hashParams.get('refresh_token');
    
    if (accessToken) {
      // OAuth callback - extract tokens
      const userData = {
        accessToken: accessToken,
        refreshToken: refreshToken || '',
      };
      
      // Clear URL parameters and redirect to root
      window.history.replaceState({}, document.title, '/');
      
      // Store tokens for persistence
      localStorage.setItem('user_tokens', JSON.stringify(userData));
      
      // Proceed to setup screen
      setUser(userData);
      setScreen('setup');
      return;
    }
    
    // Check for stored tokens (if user already logged in)
    const storedTokens = localStorage.getItem('user_tokens');
    if (storedTokens) {
      try {
        const userData = JSON.parse(storedTokens);
        setUser(userData);
        setScreen('setup');
        return;
      } catch (e) {
        // Invalid stored data, clear it
        localStorage.removeItem('user_tokens');
      }
    }
    
    // Check for recovery data on load
    const recovery = checkForRecovery();
    if (recovery) {
      setRecoveryData(recovery);
    }
  }, []);

  const handleLogin = (userData) => {
    setUser(userData);
    setScreen('setup');
  };

  const handleLogout = () => {
    // Clear tokens from localStorage
    localStorage.removeItem('user_tokens');
    // Clear user state
    setUser(null);
    // Go to login screen
    setScreen('login');
  };

  const handleStartSession = (sessionInfo) => {
    setSessionData(sessionInfo);
    setScreen('recording');
  };

  const handleSessionComplete = (fileInfo) => {
    setSessionData({ ...sessionData, fileInfo });
    setScreen('success');
  };

  // Handle token refresh from server
  const handleTokenRefresh = (newTokens) => {
    console.log('[APP] Updating user tokens after refresh');
    const updatedUser = {
      ...user,
      accessToken: newTokens.access_token,
      refreshToken: newTokens.refresh_token,
    };
    setUser(updatedUser);
    // Persist to localStorage
    localStorage.setItem('user_tokens', JSON.stringify(updatedUser));
  };

  const handleRecovery = (recoveredData) => {
    setRecoveryData(null);
    setSessionData(recoveredData);
    setScreen('recording');
  };

  const handleDiscardRecovery = () => {
    setRecoveryData(null);
  };

  const handleNewSession = () => {
    setSessionData(null);
    setScreen('setup');
  };

  return (
    <div className="App">
      {recoveryData && (
        <RecoveryDialog
          data={recoveryData}
          onRecover={handleRecovery}
          onDiscard={handleDiscardRecovery}
        />
      )}

      {screen === 'login' && <LoginScreen onLogin={handleLogin} />}
      {screen === 'setup' && (
        <SessionSetup
          user={user}
          onStart={handleStartSession}
          onBack={handleLogout}
        />
      )}
      {screen === 'recording' && (
        <ActiveSession
          sessionData={sessionData}
          user={user}
          onComplete={handleSessionComplete}
          onStop={() => setScreen('setup')}
          onTokenRefresh={handleTokenRefresh}
        />
      )}
      {screen === 'success' && (
        <SuccessScreen
          fileInfo={sessionData?.fileInfo}
          onNewSession={handleNewSession}
        />
      )}
    </div>
  );
}

export default App;

