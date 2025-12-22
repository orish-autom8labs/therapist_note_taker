import React, { useState, useEffect, useRef } from 'react';
import useSonioxClient from '../hooks/useSonioxClient';
import { syncTranscript, setupAutoSave } from '../services/transcriptSyncService';
import { saveToLocalStorage } from '../services/recoveryService';

function ActiveSession({ sessionData, user, onComplete, onStop }) {
  const [error, setError] = useState(null);
  const transcriptEndRef = useRef(null);
  const sessionIdRef = useRef(null);
  const autoSaveCleanupRef = useRef(null);

  // Generate session ID
  useEffect(() => {
    sessionIdRef.current = `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }, []);

  // Soniox SDK hook - EXACTLY like official example
  const {
    state,
    finalTokens,
    nonFinalTokens,
    error: sonioxError,
    startTranscription,
    stopTranscription,
    isRecording,
  } = useSonioxClient({
    language: 'he', // Hebrew
    enableSpeakerDiarization: true,
    onError: (err) => {
      console.error('[SONIOX] Transcription error:', err);
      setError(err.message || 'Transcription error');
    },
    onStarted: () => {
      console.log('[DEBUG] Transcription started');
    },
    onFinished: () => {
      console.log('[DEBUG] Transcription finished');
    },
  });

  // Start session on mount
  useEffect(() => {
    startTranscription();
    
    return () => {
      // Cleanup on unmount
      stopTranscription();
      if (autoSaveCleanupRef.current) {
        autoSaveCleanupRef.current();
      }
    };
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  // Combine final and non-final tokens (like official example)
  const allTokens = [...finalTokens, ...nonFinalTokens];
  
  // Debug logging
  useEffect(() => {
    console.log('[COMPONENT] finalTokens:', finalTokens);
    console.log('[COMPONENT] nonFinalTokens:', nonFinalTokens);
    console.log('[COMPONENT] allTokens:', allTokens);
  }, [finalTokens, nonFinalTokens, allTokens]);

  // Auto-scroll to bottom
  useEffect(() => {
    transcriptEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [allTokens]);

  // Save to localStorage every 5 seconds
  useEffect(() => {
    if (allTokens.length > 0) {
      const interval = setInterval(() => {
        // Convert tokens to chunks for saving
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
      // Clear existing auto-save
      if (autoSaveCleanupRef.current) {
        autoSaveCleanupRef.current();
      }

      // Setup new auto-save
      autoSaveCleanupRef.current = setupAutoSave(
        sessionIdRef.current,
        () => {
          // Convert tokens to chunks for syncing
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
        sessionData.patientName, // Pass patient name
        (error) => {
          console.error('[SYNC] Auto-save error:', error);
          // Don't show error to user, just log it
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
      console.log('[DEBUG] Stopping session...');
      
      // Stop transcription
      stopTranscription();

      // Final save to server
      if (allTokens.length > 0 && sessionIdRef.current && user?.accessToken) {
        try {
          // Convert tokens to chunks for syncing
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
            sessionData.patientName // Pass patient name
          );

          console.log('[DEBUG] Final save result:', result);
          
          // Call onComplete with file info
          if (result.fileInfo) {
            // Map Python naming (web_view_link) to JS naming (webViewLink)
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
          // Still call onComplete to allow user to continue
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

  const formatTranscript = () => {
    let output = '';
    let currentSpeaker = null;

    for (const token of allTokens) {
      if (token.speaker && token.speaker !== currentSpeaker) {
        if (currentSpeaker !== null) {
          output += '\n\n';
        }
        output += `${token.speaker}:\n`;
        currentSpeaker = token.speaker;
      }
      output += token.text + ' ';
    }

    return output.trim();
  };

  return (
    <div className="container">
      <div className="header">
        <a className="back-link" onClick={stopSession}>← Stop Session</a>
        <h2>Note Taker</h2>
      </div>

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
            Waiting for speech... (Debug: finalTokens={finalTokens.length}, nonFinalTokens={nonFinalTokens.length})
          </div>
        ) : (
          <div>
            {allTokens.map((token, idx) => {
              // Skip <end> tokens (they're just markers)
              if (token.text === '<end>') {
                return null;
              }
              
              // Track speaker changes to show speaker labels only when speaker changes
              const prevToken = idx > 0 ? allTokens[idx - 1] : null;
              const isNewSpeaker = token.speaker && token.speaker !== (prevToken?.speaker || null);
              
              return (
                <React.Fragment key={`rendered-token-${idx}`}>
                  {/* Show speaker label if speaker changed or new speaker joined */}
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
                  {/* Display final and non-final tokens with different colors */}
                  <span
                    style={{
                      color: token.is_final ? '#2C3E50' : '#7F8C8D',
                      fontStyle: token.is_final ? 'normal' : 'italic',
                      whiteSpace: 'pre-wrap'
                    }}
                  >
                    {token.text}
                  </span>
                  {/* Add updating indicator for non-final tokens */}
                  {!token.is_final && (
                    <span style={{ fontSize: '12px', color: '#95A5A6' }}>
                      {' '}(updating...)
                    </span>
                  )}
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
