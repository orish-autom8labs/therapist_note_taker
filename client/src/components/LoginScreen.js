import React from 'react';
import { getGoogleAuthUrl } from '../services/authService';

function LoginScreen({ onLogin }) {
  const handleGoogleLogin = async () => {
    try {
      const authUrl = await getGoogleAuthUrl();
      // Redirect to Google OAuth
      window.location.href = authUrl;
    } catch (error) {
      console.error('Login error:', error);
      alert('Failed to initiate login. Please try again.');
    }
  };

  return (
    <div className="container">
      <h1>📝 Note Taker</h1>
      <p className="subtitle">Secure Session Transcription for Therapists</p>
      
      <ul className="feature-list">
        <li>No recordings stored</li>
        <li>Direct to your Google Drive</li>
        <li>Hebrew transcription</li>
        <li>Speaker identification</li>
      </ul>

      <button className="btn-primary" onClick={handleGoogleLogin}>
        Sign in with Google
      </button>
    </div>
  );
}

export default LoginScreen;




