import React, { useState, useEffect, useRef, useMemo } from 'react';
import useSonioxClient from '../hooks/useSonioxClient';
import useSessionTimer from '../hooks/useSessionTimer';
import useAudioVisualizer from '../hooks/useAudioVisualizer';
import { syncTranscript, setupAutoSave } from '../services/transcriptSyncService';
import { saveToLocalStorage } from '../services/recoveryService';
import SessionTimer from './SessionTimer';
import AudioVisualizer from './AudioVisualizer';

function ActiveSession({ sessionData, user, onComplete, onStop }) {
  const [error, setError] = useState(null);
  const [audioStream, setAudioStream] = useState(null);
  const transcriptEndRef = useRef(null);
  const sessionIdRef = useRef(null);
  const autoSaveCleanupRef = useRef(null);

  // Generate session ID
  useEffect(() => {
    sessionIdRef.current = `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }, []);

  // Get microphone access for audio visualization
  useEffect(() => {
    async function getMicrophone() {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        setAudioStream(stream);
      } catch (err) {
        console.error('[AUDIO] Failed to get microphone:', err);
        // Don't show error - visualization is optional
      }
    }
    getMicrophone();

    return () => {
      if (audioStream) {
        audioStream.getTracks().forEach(track => track.stop());
      }
    };
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  // Audio visualization
  const { waveformData, isActive: isAudioActive } = useAudioVisualizer(audioStream);

  // Session timer with 60-minute limit
  const {
    elapsed,
    remaining,
    warningLevel,
    start: startTimer,
    stop: stopTimer,
    formatTime,
  } = useSessionTimer({
    maxDuration: 60 * 60 * 1000, // 60 minutes
    onWarning: (level, minutesRemaining) => {
      console.log(`[TIMER] Warning: ${level}, ${minutesRemaining} minutes remaining`);
    },
    onMaxTime: () => {
      console.log('[TIMER] Max time reached - auto-stopping session');
      setTimeout(() => {
        stopSession();
      }, 2000); // Give user 2 seconds to see the message
    },
  });

  // Soniox SDK hook
  const {
    state,
    finalTokens,
    nonFinalTokens,
    error: sonioxError,
    startTranscription,
    stopTranscription,
    isRecording,
  } = useSonioxClient({
    enableSpeakerDiarization: true,
    onError: (err) => {
      console.error('[SONIOX] Transcription error:', err);
      setError(err.message || 'Transcription error');
    },
    onStarted: () => {
      console.log('[SESSION] Transcription started');
      startTimer(); // Start timer when transcription starts
    },
    onFinished: () => {
      console.log('[SESSION] Transcription finished');
      stopTimer(); // Stop timer when transcription finishes
    },
  });

  // Start session on mount
  useEffect(() => {
    startTranscription();

    return () => {
      stopTranscription();
      stopTimer();
      if (autoSaveCleanupRef.current) {
        autoSaveCleanupRef.current();
      }
    };
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  // Combine final and non-final tokens (using useMemo to prevent recreating on every render)
  const allTokens = useMemo(() => {
    return [...finalTokens, ...nonFinalTokens];
  }, [finalTokens, nonFinalTokens]);

  // Auto-scroll to bottom
  useEffect(() => {
    transcriptEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [allTokens]);

  // Save to localStorage every 5 seconds
  useEffect(() => {
    if (allTokens.length > 0) {
      const interval = setInterval(() => {
        const transcriptChunks = allTokens.map(t => ({
          text: t.text,
          speaker: t.speaker,
          is_final: t.is_final,
          timestamp: t.timestamp || Date.now(),
        }));
        saveToLocalStorage({
          transcript: transcriptChunks,
          patientName: sessionData.patientName,
          timestamp: Date.now(),
        });
      }, 5000);

      return () => clearInterval(interval);
    }
  }, [allTokens, sessionData.patientName]);

  // Setup auto-save to server (every 1 minute)
  useEffect(() => {
    if (allTokens.length > 0 && sessionIdRef.current && user?.accessToken) {
      if (autoSaveCleanupRef.current) {
        autoSaveCleanupRef.current();
      }

      autoSaveCleanupRef.current = setupAutoSave(
        sessionIdRef.current,
        () => {
          return allTokens.map(t => ({
            text: t.text,
            speaker: t.speaker,
            is_final: t.is_final,
            timestamp: t.timestamp || Date.now(),
          }));
        },
        {
          accessToken: user.accessToken,
          refreshToken: user.refreshToken,
        },
        sessionData.patientName,
        (error) => {
          console.error('[SYNC] Auto-save error:', error);
        }
      );

      return () => {
        if (autoSaveCleanupRef.current) {
          autoSaveCleanupRef.current();
        }
      };
    }
  }, [allTokens, user, sessionData.patientName]);

  // Handle Soniox errors
  useEffect(() => {
    if (sonioxError) {
      setError(sonioxError.message || 'Transcription error');
    }
  }, [sonioxError]);

  const stopSession = async () => {
    try {
      console.log('[SESSION] Stopping session...');

      // Stop transcription and timer
      stopTranscription();
      stopTimer();

      // Final save to server
      if (allTokens.length > 0 && sessionIdRef.current && user?.accessToken) {
        try {
          const transcriptChunks = allTokens.map(t => ({
            text: t.text,
            speaker: t.speaker,
            is_final: t.is_final,
            timestamp: t.timestamp || Date.now(),
          }));

          const result = await syncTranscript(
            sessionIdRef.current,
            transcriptChunks,
            true, // isFinal
            {
              accessToken: user.accessToken,
              refreshToken: user.refreshToken,
            },
            sessionData.patientName
          );

          console.log('[SESSION] Final save result:', result);

          if (result.fileInfo) {
            const fileInfo = {
              id: result.fileInfo.id,
              name: result.fileInfo.name,
              webViewLink: result.fileInfo.web_view_link || result.fileInfo.webViewLink,
            };
            onComplete(fileInfo);
          } else {
            onComplete({ message: 'Session saved successfully' });
          }
        } catch (error) {
          console.error('[ERROR] Failed to save final transcript:', error);
          setError(`Failed to save: ${error.message}`);
          onComplete({ error: error.message });
        }
      } else {
        onComplete({ message: 'Session ended (no transcript)' });
      }
    } catch (error) {
      console.error('[ERROR] Error stopping session:', error);
      setError(error.message);
    }
  };

  return (
    <div className="container">
      <div className="header">
        <a className="back-link" onClick={stopSession}>← Stop Session</a>
        <h2>Note Taker</h2>
      </div>

      {/* Session Timer */}
      <SessionTimer
        elapsed={elapsed}
        remaining={remaining}
        warningLevel={warningLevel}
        formatTime={formatTime}
      />

      {/* Audio Visualizer */}
      <AudioVisualizer waveformData={waveformData} isActive={isAudioActive && isRecording} />

      {/* Recording Indicator */}
      {isRecording && (
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '10px',
          marginBottom: '20px',
          color: '#E74C3C',
          fontWeight: '600'
        }}>
          <div style={{
            width: '12px',
            height: '12px',
            background: '#E74C3C',
            borderRadius: '50%',
            animation: 'pulse 2s infinite'
          }}></div>
          <span>Recording...</span>
        </div>
      )}

      {/* Session Info */}
      <div style={{
        background: '#ECF0F1',
        padding: '15px',
        borderRadius: '8px',
        marginBottom: '20px',
        fontSize: '14px'
      }}>
        <strong>Patient:</strong> {sessionData.patientName}<br />
        <strong>Started:</strong> {new Date().toLocaleTimeString('he-IL', {
          hour: '2-digit',
          minute: '2-digit'
        })}
        <br />
        <strong>Status:</strong> {state}
      </div>

      {/* Error Display */}
      {error && (
        <div style={{
          background: '#FADBD8',
          color: '#C0392B',
          padding: '15px',
          borderRadius: '8px',
          marginBottom: '20px'
        }}>
          Error: {error}
        </div>
      )}

      {/* Transcript Display */}
      <div style={{
        background: '#F8F9FA',
        border: '2px solid #E9ECEF',
        borderRadius: '8px',
        padding: '20px',
        minHeight: '300px',
        maxHeight: '600px',
        overflowY: 'auto',
        marginBottom: '20px',
        direction: 'rtl',
        textAlign: 'right',
        fontSize: '16px',
        lineHeight: '1.8',
        width: '100%',
        wordWrap: 'break-word'
      }}>
        {allTokens.length === 0 ? (
          <div style={{ color: '#95A5A6', textAlign: 'center', padding: '40px' }}>
            Waiting for speech...
          </div>
        ) : (
          <div>
            {allTokens.map((token, idx) => {
              if (token.text === '<end>') {
                return null;
              }

              const prevToken = idx > 0 ? allTokens[idx - 1] : null;
              const isNewSpeaker = token.speaker && token.speaker !== (prevToken?.speaker || null);

              return (
                <React.Fragment key={`token-${idx}`}>
                  {isNewSpeaker && token.speaker && (
                    <div
                      style={{
                        color: '#4A90E2',
                        fontWeight: '600',
                        marginTop: idx > 0 ? '15px' : '0',
                        marginBottom: '5px',
                        fontSize: '14px'
                      }}
                    >
                      {token.speaker}:
                    </div>
                  )}
                  <span
                    style={{
                      color: token.is_final ? '#2C3E50' : '#7F8C8D',
                      fontStyle: token.is_final ? 'normal' : 'italic',
                      whiteSpace: 'pre-wrap'
                    }}
                  >
                    {token.text}
                  </span>
                </React.Fragment>
              );
            })}
          </div>
        )}
        <div ref={transcriptEndRef} />
      </div>

      <button className="btn-danger" onClick={stopSession}>
        ⏹ Stop & Save
      </button>
    </div>
  );
}

export default ActiveSession;
