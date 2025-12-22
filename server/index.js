import express from 'express';
import cors from 'cors';
import { WebSocketServer } from 'ws';
import http from 'http';
import { config } from './src/config.js';
import { TranscriptionService } from './src/services/TranscriptionService.js';
import { DriveService } from './src/services/DriveService.js';
import { EmailService } from './src/services/EmailService.js';

const app = express();
const server = http.createServer(app);

// Middleware
app.use(cors());
app.use(express.json());

// Services
const transcriptionService = new TranscriptionService();
const driveService = new DriveService();
const emailService = new EmailService();

// Store active sessions
const activeSessions = new Map();

// WebSocket server for real-time transcription
const wss = new WebSocketServer({ server });

wss.on('connection', (ws, req) => {
  console.log('New WebSocket connection');

  let sessionId = null;
  let transcriptionSession = null;
  let transcriptBuffer = [];
  let driveFileId = null;
  let lastSaveTime = Date.now();
  let autoSaveInterval = null;

  ws.on('message', async (message) => {
    try {
      const data = JSON.parse(message);

      switch (data.type) {
        case 'start_session':
          await handleStartSession(data);
          break;

        case 'audio_chunk':
          await handleAudioChunk(data);
          break;

        case 'stop_session':
          await handleStopSession();
          break;

        default:
          ws.send(JSON.stringify({ type: 'error', message: 'Unknown message type' }));
      }
    } catch (error) {
      console.error('WebSocket error:', error);
      ws.send(JSON.stringify({ type: 'error', message: error.message }));
    }
  });

  async function handleStartSession(data) {
    const { sessionId: newSessionId, patientName, accessToken, refreshToken } = data;

    if (!newSessionId || !patientName || !accessToken) {
      ws.send(JSON.stringify({
        type: 'error',
        message: 'Missing required fields: sessionId, patientName, accessToken',
      }));
      return;
    }

    sessionId = newSessionId;
    
    // Set user's Drive tokens
    driveService.setUserTokens({
      access_token: accessToken,
      refresh_token: refreshToken,
    });

    // Generate file name
    const now = new Date();
    const dateStr = now.toISOString().split('T')[0];
    const timeStr = now.toTimeString().split(' ')[0].slice(0, 5).replace(':', '-');
    const fileName = `${patientName}_${dateStr}_${timeStr}.txt`;

    // Start transcription session
    transcriptionSession = await transcriptionService.startSession(
      {},
      (transcriptChunk) => {
        // Add to buffer
        transcriptBuffer.push(transcriptChunk);

        // Send to client
        ws.send(JSON.stringify({
          type: 'transcript',
          ...transcriptChunk,
        }));

        // Auto-save every 1 minute
        const now = Date.now();
        if (now - lastSaveTime >= config.autosave.interval) {
          autoSaveToDrive(fileName);
          lastSaveTime = now;
        }
      },
      (error) => {
        console.error('Transcription error:', error);
        ws.send(JSON.stringify({
          type: 'error',
          message: 'Transcription error: ' + error.message,
        }));
      }
    );

    // Start auto-save interval
    autoSaveInterval = setInterval(() => {
      autoSaveToDrive(fileName);
    }, config.autosave.interval);

    // Store session
    activeSessions.set(sessionId, {
      ws,
      transcriptionSession,
      transcriptBuffer,
      driveFileId,
      patientName,
      fileName,
      startTime: new Date(),
    });

    ws.send(JSON.stringify({
      type: 'session_started',
      sessionId,
    }));
  }

  async function handleAudioChunk(data) {
    if (!transcriptionSession || !transcriptionSession.isActive()) {
      ws.send(JSON.stringify({
        type: 'error',
        message: 'Session not active',
      }));
      return;
    }

    // Convert base64 audio to buffer
    const audioBuffer = Buffer.from(data.audio, 'base64');
    transcriptionSession.sendAudio(audioBuffer);
  }

  async function autoSaveToDrive(fileName) {
    if (transcriptBuffer.length === 0) return;

    try {
      const content = formatTranscript(transcriptBuffer);
      const tempFileName = `${config.autosave.tempFilePrefix}${fileName}`;

      if (driveFileId) {
        // Update existing temp file
        await driveService.updateFile(driveFileId, content);
      } else {
        // Create new temp file
        const fileInfo = await driveService.saveTranscript(
          content,
          tempFileName,
          'Clinic/Transcripts'
        );
        driveFileId = fileInfo.fileId;
      }
    } catch (error) {
      console.error('Auto-save error:', error);
      // Don't send error to client for auto-save failures
    }
  }

  async function handleStopSession() {
    if (!transcriptionSession) {
      ws.send(JSON.stringify({ type: 'error', message: 'No active session' }));
      return;
    }

    // Stop transcription
    await transcriptionSession.stop();

    // Clear auto-save interval
    if (autoSaveInterval) {
      clearInterval(autoSaveInterval);
    }

    // Final save to Drive
    try {
      const content = formatTranscript(transcriptBuffer);
      const session = activeSessions.get(sessionId);
      const finalFileName = session?.fileName || `session_${sessionId}.txt`;

      let fileInfo;
      if (driveFileId) {
        // Update temp file with final name
        fileInfo = await driveService.updateFile(driveFileId, content);
        // Note: Google Drive doesn't support renaming via update, so we'd need to create new and delete old
        // For MVP, we'll keep the temp name or create a new file
        const newFile = await driveService.saveTranscript(
          content,
          finalFileName,
          'Clinic/Transcripts'
        );
        await driveService.deleteFile(driveFileId);
        fileInfo = newFile;
      } else {
        // Create new file
        fileInfo = await driveService.saveTranscript(
          content,
          finalFileName,
          'Clinic/Transcripts'
        );
      }

      // Send email notification
      const session = activeSessions.get(sessionId);
      if (session) {
        const now = new Date();
        await emailService.sendTranscriptNotification(
          session.userEmail || 'user@example.com', // Get from session or token
          {
            patientName: session.patientName,
            date: now.toLocaleDateString('he-IL'),
            time: now.toLocaleTimeString('he-IL', { hour: '2-digit', minute: '2-digit' }),
          },
          fileInfo.webViewLink
        );
      }

      ws.send(JSON.stringify({
        type: 'session_complete',
        fileInfo,
      }));
    } catch (error) {
      console.error('Final save error:', error);
      ws.send(JSON.stringify({
        type: 'error',
        message: 'Failed to save transcript: ' + error.message,
      }));
    }

    // Clean up
    activeSessions.delete(sessionId);
    transcriptBuffer = [];
    driveFileId = null;
  }

  function formatTranscript(buffer) {
    let output = '';
    let currentSpeaker = null;

    for (const chunk of buffer) {
      if (chunk.speaker && chunk.speaker !== currentSpeaker) {
        if (currentSpeaker !== null) {
          output += '\n\n';
        }
        output += `${chunk.speaker || 'Unknown'}:\n`;
        currentSpeaker = chunk.speaker;
      }
      output += chunk.text + ' ';
    }

    return output.trim();
  }

  ws.on('close', () => {
    console.log('WebSocket connection closed');
    if (sessionId) {
      activeSessions.delete(sessionId);
    }
    if (transcriptionSession) {
      transcriptionSession.stop();
    }
    if (autoSaveInterval) {
      clearInterval(autoSaveInterval);
    }
  });
});

// REST API Routes

// Get Google OAuth URL
app.get('/api/auth/google/url', (req, res) => {
  const authUrl = driveService.getAuthUrl();
  res.json({ authUrl });
});

// OAuth callback endpoint
app.get('/auth/google/callback', async (req, res) => {
  try {
    const { code } = req.query;
    if (!code) {
      return res.status(400).send('Authorization code required');
    }

    const tokens = await driveService.getTokens(code);
    
    // Redirect to frontend with tokens (in production, use secure method)
    const redirectUrl = `${process.env.FRONTEND_URL || 'http://localhost:3000'}/auth/callback?` +
      `access_token=${encodeURIComponent(tokens.access_token)}&` +
      `refresh_token=${encodeURIComponent(tokens.refresh_token || '')}`;
    
    res.redirect(redirectUrl);
  } catch (error) {
    console.error('OAuth callback error:', error);
    res.status(500).send('Authentication failed. Please try again.');
  }
});

// Exchange code for tokens (alternative API endpoint)
app.post('/api/auth/google/tokens', async (req, res) => {
  try {
    const { code } = req.body;
    if (!code) {
      return res.status(400).json({ error: 'Authorization code required' });
    }

    const tokens = await driveService.getTokens(code);
    res.json({ tokens });
  } catch (error) {
    console.error('Token exchange error:', error);
    res.status(500).json({ error: error.message });
  }
});

// Get provider info
app.get('/api/transcription/provider', (req, res) => {
  const info = transcriptionService.getProviderInfo();
  res.json(info);
});

// Cleanup temp files (can be called by cron job)
app.post('/api/admin/cleanup-temp-files', async (req, res) => {
  try {
    const count = await driveService.cleanupTempFiles(
      'Clinic/Transcripts',
      config.autosave.tempFileRetentionHours
    );
    res.json({ deleted: count });
  } catch (error) {
    console.error('Cleanup error:', error);
    res.status(500).json({ error: error.message });
  }
});

// Health check
app.get('/health', (req, res) => {
  res.json({ status: 'ok', provider: transcriptionService.getProviderInfo().name });
});

const PORT = config.server.port;
server.listen(PORT, () => {
  console.log(`Server running on port ${PORT}`);
  console.log(`Transcription provider: ${transcriptionService.getProviderInfo().name}`);
});

