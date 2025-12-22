import axios from 'axios';

const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:3001';
const WS_URL = process.env.REACT_APP_WS_URL || 'ws://localhost:3001/ws';

export async function startTranscriptionSession(sessionData, user, onTranscript, onError) {
  const sessionId = `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  
  // Create WebSocket connection
  console.log('[DEBUG] Connecting to WebSocket:', WS_URL);
  const ws = new WebSocket(WS_URL);

  return new Promise((resolve, reject) => {
    ws.onopen = () => {
      console.log('[DEBUG] WebSocket connected, sending start_session');
      // Start session
      ws.send(JSON.stringify({
        type: 'start_session',
        sessionId,
        patientName: sessionData.patientName,
        accessToken: user.accessToken,
        refreshToken: user.refreshToken,
      }));

      // Set up message handlers
      ws.onmessage = (event) => {
        console.log('[DEBUG] Received WebSocket message:', event.data);
        const data = JSON.parse(event.data);

        switch (data.type) {
          case 'session_started':
            console.log('[DEBUG] Session started, resolving promise');
            resolve({
              sessionId,
              ws,
              sendAudio: (base64Audio) => {
                ws.send(JSON.stringify({
                  type: 'audio_chunk',
                  audio: base64Audio,
                }));
              },
              stop: async () => {
                return new Promise((resolveStop, rejectStop) => {
                  ws.send(JSON.stringify({ type: 'stop_session' }));

                  const messageHandler = (event) => {
                    const data = JSON.parse(event.data);
                    if (data.type === 'session_complete') {
                      ws.removeEventListener('message', messageHandler);
                      ws.close();
                      resolveStop(data.fileInfo);
                    } else if (data.type === 'error') {
                      ws.removeEventListener('message', messageHandler);
                      ws.close();
                      rejectStop(new Error(data.message));
                    }
                  };

                  ws.addEventListener('message', messageHandler);

                  // Timeout after 30 seconds
                  setTimeout(() => {
                    ws.removeEventListener('message', messageHandler);
                    ws.close();
                    rejectStop(new Error('Session stop timeout'));
                  }, 30000);
                });
              },
              isActive: () => ws.readyState === WebSocket.OPEN,
            });
            break;

          case 'transcript':
            onTranscript(data);
            break;

          case 'error':
            onError(new Error(data.message));
            break;

          case 'session_complete':
            // Handled in stop() promise
            break;
        }
      };

      ws.onerror = (error) => {
        console.error('[ERROR] WebSocket error:', error);
        console.error('[ERROR] WebSocket readyState:', ws.readyState);
        onError(error);
        reject(error);
      };

      ws.onclose = (event) => {
        console.log('[DEBUG] WebSocket closed:', event.code, event.reason);
        // Connection closed
      };
    };

    ws.onerror = (error) => {
      reject(error);
    };
  });
}

