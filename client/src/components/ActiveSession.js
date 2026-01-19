import React, { useState, useEffect, useRef, useMemo, useCallback } from 'react';
import useSonioxClient from '../hooks/useSonioxClient';
import useSessionTimer from '../hooks/useSessionTimer';
import useAudioVisualizer from '../hooks/useAudioVisualizer';
import { syncTranscript, setupAutoSave } from '../services/transcriptSyncService';
import { saveToLocalStorage } from '../services/recoveryService';
import SessionTimer from './SessionTimer';
import AudioVisualizer from './AudioVisualizer';
import sessionConfig from '../config/sessionConfig';

function ActiveSession({ sessionData, user, onComplete, onStop, onTokenRefresh }) {
  const [error, setError] = useState(null);
  const [audioStream, setAudioStream] = useState(null);
  const [backgroundWarning, setBackgroundWarning] = useState(false);
  const [transcriptStalled, setTranscriptStalled] = useState(false);
  const [stallDuration, setStallDuration] = useState(0);
  const transcriptEndRef = useRef(null);
  const sessionIdRef = useRef(null);
  const autoSaveCleanupRef = useRef(null);
  const stopSessionRef = useRef(null);
  const wakeLockRef = useRef(null);
  const lastTokenTimeRef = useRef(Date.now());
  const stallEventsRef = useRef([]); // Track stall events for diagnostics

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

  // Wake Lock API - Prevent screen from auto-locking during session
  useEffect(() => {
    const requestWakeLock = async () => {
      try {
        if ('wakeLock' in navigator) {
          wakeLockRef.current = await navigator.wakeLock.request('screen');
          console.log('[WAKE LOCK] ✓ Screen will stay on during session');

          wakeLockRef.current.addEventListener('release', () => {
            console.log('[WAKE LOCK] Released');
          });
        } else {
          console.log('[WAKE LOCK] Not supported on this device');
        }
      } catch (err) {
        console.error('[WAKE LOCK] Failed:', err);
      }
    };

    requestWakeLock();

    // Re-request wake lock when page becomes visible again
    const handleVisibilityChange = () => {
      if (wakeLockRef.current !== null && document.visibilityState === 'visible') {
        requestWakeLock();
      }
    };

    document.addEventListener('visibilitychange', handleVisibilityChange);

    return () => {
      wakeLockRef.current?.release();
      wakeLockRef.current = null;
      document.removeEventListener('visibilitychange', handleVisibilityChange);
    };
  }, []);

  // Page Visibility API - Detect when app goes to background
  useEffect(() => {
    const handleVisibilityChange = () => {
      if (document.hidden) {
        console.warn('[VISIBILITY] ⚠️ App went to background - transcription may pause!');
        setBackgroundWarning(true);
      } else {
        console.log('[VISIBILITY] ✓ App returned to foreground');
        setBackgroundWarning(false);
      }
    };

    document.addEventListener('visibilitychange', handleVisibilityChange);

    return () => {
      document.removeEventListener('visibilitychange', handleVisibilityChange);
    };
  }, []);

  // Audio visualization
  const { waveformData, isActive: isAudioActive } = useAudioVisualizer(audioStream);

  // Callbacks for session timer (memoized to prevent recreating on every render)
  const handleTimerWarning = useCallback((level, minutesRemaining) => {
    console.log(`[SESSION] ⚠️ Timer warning callback created/called: ${level}, ${minutesRemaining} minutes remaining`);
  }, []); // No dependencies - callback never changes

  const handleMaxTime = useCallback(() => {
    console.log('[SESSION] ⏱️ Max time callback created/called - auto-stopping session');
    setTimeout(() => {
      if (stopSessionRef.current) {
        stopSessionRef.current();
      }
    }, 2000); // Give user 2 seconds to see the message
  }, []); // No dependencies - callback never changes

  // Session timer with configurable duration
  const {
    elapsed,
    remaining,
    warningLevel,
    start: startTimer,
    stop: stopTimer,
    formatTime,
  } = useSessionTimer({
    maxDuration: sessionConfig.maxDuration,
    onWarning: handleTimerWarning,
    onMaxTime: handleMaxTime,
  });

  // Soniox SDK hook with reconnection support
  const {
    state,
    finalTokens,
    nonFinalTokens,
    error: sonioxError,
    startTranscription,
    stopTranscription,
    isRecording,
    isReconnecting,
    reconnectAttempt,
  } = useSonioxClient({
    enableSpeakerDiarization: true,
    maxReconnectAttempts: 5,
    onError: (err) => {
      console.error('[SONIOX] Transcription error:', err);
      setError(err.message || 'Transcription error');
    },
    onStarted: () => {
      console.log('[SESSION] Transcription started');
      console.log('[SESSION] Calling startTimer()');
      startTimer(); // Start timer when transcription starts
      console.log('[SESSION] startTimer() called');
    },
    onFinished: () => {
      console.log('[SESSION] Transcription finished');
      stopTimer(); // Stop timer when transcription finishes
    },
    onReconnecting: (attempt, maxAttempts) => {
      console.log(`[SESSION] ⚠️ Reconnecting... attempt ${attempt}/${maxAttempts}`);
    },
    onReconnected: () => {
      console.log('[SESSION] ✓ Successfully reconnected!');
      // Clear any previous error when successfully reconnected
      setError(null);
    },
  });

  // Start session on mount
  useEffect(() => {
    console.log('[SESSION] Starting transcription and timer');
    startTranscription();
    startTimer(); // Start timer immediately, not waiting for SDK callback

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
        },
        onTokenRefresh // Pass token refresh callback
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

  // Track last token time for stall detection
  useEffect(() => {
    if (finalTokens.length > 0 || nonFinalTokens.length > 0) {
      lastTokenTimeRef.current = Date.now();
      // If we were stalled and tokens resumed, log recovery
      if (transcriptStalled) {
        const recoveryEvent = {
          type: 'STALL_RECOVERED',
          timestamp: new Date().toISOString(),
          stallDurationSeconds: stallDuration,
          tokenCountAtRecovery: finalTokens.length,
        };
        stallEventsRef.current.push(recoveryEvent);
        console.log('[STALL DETECTOR] ✓ Transcript resumed after', stallDuration, 'seconds');
      }
      setTranscriptStalled(false);
      setStallDuration(0);
    }
  }, [finalTokens, nonFinalTokens, transcriptStalled, stallDuration]);

  // Stall detection - check every 5 seconds if recording but no tokens received
  useEffect(() => {
    if (!isRecording) return;

    const STALL_THRESHOLD_SECONDS = 30; // Consider stalled after 30 seconds of no tokens

    const checkInterval = setInterval(() => {
      const secondsSinceLastToken = Math.floor((Date.now() - lastTokenTimeRef.current) / 1000);

      if (secondsSinceLastToken >= STALL_THRESHOLD_SECONDS) {
        if (!transcriptStalled) {
          // First detection of stall
          const stallEvent = {
            type: 'STALL_DETECTED',
            timestamp: new Date().toISOString(),
            secondsSinceLastToken,
            tokenCountAtStall: finalTokens.length,
            sessionElapsedSeconds: elapsed,
            state: state,
            wasInBackground: document.hidden,
            userAgent: navigator.userAgent,
          };
          stallEventsRef.current.push(stallEvent);
          console.error('[STALL DETECTOR] ⚠️ TRANSCRIPT STALLED!', stallEvent);
        }
        setTranscriptStalled(true);
        setStallDuration(secondsSinceLastToken);
      }
    }, 5000); // Check every 5 seconds

    return () => clearInterval(checkInterval);
  }, [isRecording, transcriptStalled, finalTokens.length, elapsed, state]);

  const stopSession = async () => {
    try {
      console.log('[SESSION] Stopping session...');
      console.log('[SESSION] allTokens.length:', allTokens.length);
      console.log('[SESSION] sessionIdRef.current:', sessionIdRef.current);
      console.log('[SESSION] user?.accessToken:', user?.accessToken ? 'present' : 'missing');

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

          // Include diagnostic info if there were any stall events
          const diagnosticInfo = stallEventsRef.current.length > 0 ? {
            stallEvents: stallEventsRef.current,
            totalStallCount: stallEventsRef.current.filter(e => e.type === 'STALL_DETECTED').length,
            recoveryCount: stallEventsRef.current.filter(e => e.type === 'STALL_RECOVERED').length,
            sessionDurationSeconds: elapsed,
            finalTokenCount: finalTokens.length,
          } : null;

          if (diagnosticInfo) {
            console.log('[SESSION] Including diagnostic info in save:', diagnosticInfo);
          }

          const result = await syncTranscript(
            sessionIdRef.current,
            transcriptChunks,
            true, // isFinal
            {
              accessToken: user.accessToken,
              refreshToken: user.refreshToken,
            },
            sessionData.patientName,
            diagnosticInfo // Pass diagnostic info
          );

          console.log('[SESSION] Final save result:', result);

          // Handle refreshed tokens
          if (result.refreshedTokens && onTokenRefresh) {
            console.log('[SESSION] Tokens were refreshed during final save, updating...');
            onTokenRefresh(result.refreshedTokens);
          }

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

  // Store stopSession in ref so it can be called from handleMaxTime
  stopSessionRef.current = stopSession;

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

      {/* Background Warning Banner */}
      {backgroundWarning && (
        <div style={{
          background: '#ff9800',
          color: 'white',
          padding: '15px',
          borderRadius: '8px',
          marginBottom: '20px',
          fontWeight: '600',
          textAlign: 'center',
          animation: 'pulse 2s infinite'
        }}>
          ⚠️ App is in background - Return to this screen to continue recording!
        </div>
      )}

      {/* Reconnection Banner */}
      {isReconnecting && (
        <div style={{
          background: '#3498db',
          color: 'white',
          padding: '15px',
          borderRadius: '8px',
          marginBottom: '20px',
          fontWeight: '600',
          textAlign: 'center',
          animation: 'pulse 1.5s infinite'
        }}>
          🔄 Reconnecting... (attempt {reconnectAttempt}/5)
          <br />
          <small style={{ fontWeight: 'normal', opacity: 0.9 }}>
            Your transcript is preserved. Please wait...
          </small>
        </div>
      )}

      {/* Transcript Stall Warning Banner */}
      {transcriptStalled && (
        <div style={{
          background: '#e74c3c',
          color: 'white',
          padding: '15px',
          borderRadius: '8px',
          marginBottom: '20px',
          fontWeight: '600',
          textAlign: 'center',
          animation: 'pulse 1s infinite'
        }}>
          ⚠️ TRANSCRIPT STALLED - No new text for {stallDuration}s! Recording may have stopped.
          <br />
          <small style={{ fontWeight: 'normal', opacity: 0.9 }}>
            Try stopping and saving the session. Diagnostic info will be saved.
          </small>
        </div>
      )}

      {/* Audio Visualizer */}
      <AudioVisualizer waveformData={waveformData} isActive={isAudioActive && isRecording} />

      {/* Transcribing Indicator */}
      {(isRecording || isReconnecting) && (
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '10px',
          marginBottom: '20px',
          color: isReconnecting ? '#3498db' : '#E74C3C',
          fontWeight: '600'
        }}>
          <div style={{
            width: '12px',
            height: '12px',
            background: isReconnecting ? '#3498db' : '#E74C3C',
            borderRadius: '50%',
            animation: 'pulse 2s infinite'
          }}></div>
          <span>{isReconnecting ? 'Reconnecting...' : 'Transcribing...'}</span>
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
            {(() => {
              // Create speaker number to letter mapping (1 -> A, 2 -> B, etc.)
              const speakerMap = {};
              let nextLetter = 'A';

              for (const token of allTokens) {
                if (token.speaker && !speakerMap[token.speaker]) {
                  speakerMap[token.speaker] = nextLetter;
                  nextLetter = String.fromCharCode(nextLetter.charCodeAt(0) + 1);
                }
              }

              return allTokens.map((token, idx) => {
                if (token.text === '<end>') {
                  return null;
                }

                const prevToken = idx > 0 ? allTokens[idx - 1] : null;
                const isNewSpeaker = token.speaker && token.speaker !== (prevToken?.speaker || null);

                // Get speaker letter (A, B, C, etc.)
                const speakerLetter = token.speaker ? speakerMap[token.speaker] : null;

                return (
                  <React.Fragment key={`token-${idx}`}>
                    {isNewSpeaker && speakerLetter && (
                      <div
                        style={{
                          color: '#4A90E2',
                          fontWeight: '600',
                          marginTop: idx > 0 ? '15px' : '0',
                          marginBottom: '5px',
                          fontSize: '14px'
                        }}
                      >
                        Speaker {speakerLetter}:
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
              });
            })()}
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
