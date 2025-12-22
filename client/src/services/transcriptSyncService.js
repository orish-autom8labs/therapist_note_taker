/**
 * Service for syncing transcripts to the server.
 * Handles auto-save (every 1 minute) and final save (on session end).
 */

const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:3001';

/**
 * Send transcript chunks to the server for saving.
 * 
 * @param {string} sessionId - Session ID
 * @param {Array} chunks - Array of transcript chunks
 * @param {boolean} isFinal - Whether this is the final save
 * @param {Object} userTokens - User's Google OAuth tokens (for Drive access)
 * @returns {Promise<Object>} Server response with file info
 */
export async function syncTranscript(sessionId, chunks, isFinal = false, userTokens = null, patientName = null) {
  try {
    const body = {
      sessionId,
      chunks: chunks.map(chunk => ({
        text: chunk.text,
        speaker: chunk.speaker,
        is_final: chunk.is_final,
        timestamp: chunk.timestamp,
      })),
      is_final: isFinal,
    };

    // Add user tokens if provided
    if (userTokens) {
      body.accessToken = userTokens.accessToken;
      body.refreshToken = userTokens.refreshToken;
    }

    // Add patient name if provided
    if (patientName) {
      body.patientName = patientName;
    }

    const response = await fetch(`${API_BASE}/api/sessions/${sessionId}/transcript`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(body),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || error.message || 'Failed to save transcript');
    }

    return await response.json();
  } catch (error) {
    console.error('[SYNC] Error syncing transcript:', error);
    throw error;
  }
}

/**
 * Set up auto-save interval.
 * 
 * @param {string} sessionId - Session ID
 * @param {Function} getChunks - Function that returns current transcript chunks
 * @param {Object} userTokens - User's Google OAuth tokens
 * @param {Function} onError - Error callback
 * @returns {Function} Function to clear the interval
 */
export function setupAutoSave(sessionId, getChunks, userTokens, patientName, onError) {
  const interval = setInterval(async () => {
    try {
      const chunks = getChunks();
      if (chunks.length > 0) {
        await syncTranscript(sessionId, chunks, false, userTokens, patientName);
        console.log('[SYNC] Auto-saved transcript');
      }
    } catch (error) {
      console.error('[SYNC] Auto-save failed:', error);
      if (onError) onError(error);
    }
  }, 60000); // Every 1 minute (60000 ms)

  return () => clearInterval(interval);
}

