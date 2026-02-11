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
 * @param {string} patientName - Patient name
 * @param {Object} diagnosticInfo - Optional diagnostic info (stall events, etc.)
 * @returns {Promise<Object>} Server response with file info
 */
export async function syncTranscript(sessionId, chunks, isFinal = false, userTokens = null, patientName = null, diagnosticInfo = null, includeTimestamps = true) {
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

    // Add timestamp preference
    body.includeTimestamps = includeTimestamps;

    // Add diagnostic info if provided (for debugging stall issues)
    if (diagnosticInfo) {
      body.diagnosticInfo = diagnosticInfo;
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

    const result = await response.json();

    // If server returned refreshed tokens, log it (caller will handle storing them)
    if (result.refreshedTokens) {
      console.log('[SYNC] 🔄 Server refreshed OAuth tokens automatically');
    }

    return result;
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
 * @param {string} patientName - Patient name
 * @param {Function} onError - Error callback
 * @param {Function} onTokenRefresh - Callback when tokens are refreshed
 * @returns {Function} Function to clear the interval
 */
export function setupAutoSave(sessionId, getChunks, userTokens, patientName, onError, onTokenRefresh, includeTimestamps = true) {
  const interval = setInterval(async () => {
    try {
      const chunks = getChunks();
      if (chunks.length > 0) {
        const result = await syncTranscript(sessionId, chunks, false, userTokens, patientName, null, includeTimestamps);
        console.log('[SYNC] Auto-saved transcript');

        // If tokens were refreshed, notify the caller
        if (result.refreshedTokens && onTokenRefresh) {
          console.log('[SYNC] Tokens were refreshed during auto-save, updating...');
          onTokenRefresh(result.refreshedTokens);
        }
      }
    } catch (error) {
      console.error('[SYNC] Auto-save failed:', error);
      if (onError) onError(error);
    }
  }, 60000); // Every 1 minute (60000 ms)

  return () => clearInterval(interval);
}

