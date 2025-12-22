import axios from 'axios';

const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:3001';

export async function getGoogleAuthUrl() {
  const response = await axios.get(`${API_BASE}/api/auth/google/url`);
  return response.data.authUrl;
}

export async function exchangeCodeForTokens(code) {
  const response = await axios.post(`${API_BASE}/api/auth/google/tokens`, { code });
  return response.data.tokens;
}




