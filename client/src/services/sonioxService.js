/**
 * Service for fetching temporary Soniox API keys from the server.
 */

const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:3001';

/**
 * Fetch a temporary API key from the server.
 * The server uses the main API key to generate a temporary key that expires in 60 seconds.
 * 
 * @returns {Promise<string>} Temporary API key
 */
export async function getTemporaryAPIKey() {
  console.log('[DEBUG] Fetching temporary API key from:', `${API_BASE}/v1/auth/temporary-api-key`);

  try {
    const response = await fetch(`${API_BASE}/v1/auth/temporary-api-key`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    console.log('[DEBUG] Temporary API key response status:', response.status);

    if (!response.ok) {
      const error = await response.json();
      console.error('[DEBUG] Temporary API key error response:', error);
      throw new Error(error.detail || error.error || 'Failed to get temporary API key');
    }

    const data = await response.json();
    console.log('[DEBUG] Temporary API key received:', data.apiKey ? 'SUCCESS' : 'MISSING');
    return data.apiKey;
  } catch (error) {
    console.error('[SONIOX] Error fetching temporary API key:', error);
    throw error;
  }
}

