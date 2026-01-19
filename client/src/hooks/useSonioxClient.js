import { useCallback, useEffect, useRef, useState } from 'react';
import { SonioxClient } from '@soniox/speech-to-text-web';
import { getTemporaryAPIKey } from '../services/sonioxService';

/**
 * Custom hook for Soniox SDK integration with automatic reconnection.
 *
 * Features:
 * - Automatic reconnection on WebSocket errors
 * - Exponential backoff (1s, 2s, 4s, 8s, 16s)
 * - Preserves accumulated tokens during reconnection
 * - Mobile-friendly (handles network drops)
 *
 * @param {Object} options
 * @param {Function} options.onError - Callback when errors occur
 * @param {Function} options.onStarted - Callback when transcription starts
 * @param {Function} options.onFinished - Callback when transcription finishes
 * @param {Function} options.onReconnecting - Callback when reconnection starts
 * @param {Function} options.onReconnected - Callback when reconnection succeeds
 * @param {string} options.language - Language code (e.g., 'he' for Hebrew)
 * @param {boolean} options.enableSpeakerDiarization - Enable speaker diarization
 * @param {number} options.maxReconnectAttempts - Max reconnection attempts (default: 5)
 * @returns {Object} Transcription state and controls
 */
export default function useSonioxClient({
  onError,
  onStarted,
  onFinished,
  onReconnecting,
  onReconnected,
  language = 'he',
  enableSpeakerDiarization = true,
  maxReconnectAttempts = 5,
}) {
  const sonioxClient = useRef(null);
  const reconnectTimeoutRef = useRef(null);
  const isManualStop = useRef(false);
  const shouldReconnect = useRef(false);

  if (sonioxClient.current == null) {
    sonioxClient.current = new SonioxClient({
      apiKey: getTemporaryAPIKey,
    });
  }

  const [state, setState] = useState('Init');
  const [finalTokens, setFinalTokens] = useState([]);
  const [nonFinalTokens, setNonFinalTokens] = useState([]);
  const [error, setError] = useState(null);
  const [reconnectAttempt, setReconnectAttempt] = useState(0);
  const [isReconnecting, setIsReconnecting] = useState(false);

  // Calculate backoff delay: 1s, 2s, 4s, 8s, 16s
  const getBackoffDelay = (attempt) => Math.min(1000 * Math.pow(2, attempt), 16000);

  // Errors that should trigger reconnection
  const isRecoverableError = (status, errorCode) => {
    const recoverableStatuses = [
      'websocket_error',
      'api_error',
      'media_recorder_error',
    ];
    // Don't reconnect on user-denied permissions or intentional stops
    const nonRecoverableStatuses = [
      'get_user_media_failed',
      'api_key_fetch_failed',
    ];

    if (nonRecoverableStatuses.includes(status)) {
      return false;
    }

    return recoverableStatuses.includes(status) || errorCode >= 500;
  };

  const startTranscriptionInternal = useCallback(async (isReconnect = false) => {
    console.log(`[SONIOX] ${isReconnect ? 'Reconnecting...' : 'Starting transcription'}`);

    if (!sonioxClient.current) {
      const error = new Error('Soniox client not initialized');
      console.error('[SONIOX] ERROR: Client not initialized!');
      setError(error);
      if (onError) onError(error);
      return false;
    }

    // Only reset tokens on fresh start, not reconnect
    if (!isReconnect) {
      console.log('[SONIOX] Fresh start - resetting tokens');
      setFinalTokens([]);
      setNonFinalTokens([]);
      setReconnectAttempt(0);
    } else {
      console.log('[SONIOX] Reconnect - preserving existing tokens');
    }

    setError(null);
    shouldReconnect.current = true;
    isManualStop.current = false;

    try {
      await sonioxClient.current.start({
        model: 'stt-rt-v3',
        enableLanguageIdentification: true,
        enableSpeakerDiarization: enableSpeakerDiarization,
        enableEndpointDetection: true,

        onStarted: () => {
          console.log('[SONIOX] ✓ Transcription started');
          setState('Recording');
          setIsReconnecting(false);

          if (isReconnect) {
            console.log('[SONIOX] ✓ Reconnection successful');
            setReconnectAttempt(0);
            if (onReconnected) onReconnected();
          } else {
            if (onStarted) onStarted();
          }
        },

        onFinished: () => {
          console.log('[SONIOX] Transcription finished');
          setState('Finished');
          shouldReconnect.current = false;
          if (onFinished) onFinished();
        },

        onError: (status, message, errorCode) => {
          console.error('[SONIOX] Error:', { status, message, errorCode });

          const err = new Error(message || 'Transcription error');
          err.status = status;
          err.errorCode = errorCode;
          setError(err);

          // Check if we should attempt reconnection
          if (!isManualStop.current &&
              shouldReconnect.current &&
              isRecoverableError(status, errorCode) &&
              reconnectAttempt < maxReconnectAttempts) {

            const nextAttempt = reconnectAttempt + 1;
            const delay = getBackoffDelay(nextAttempt);

            console.log(`[SONIOX] ⚠️ Will attempt reconnection ${nextAttempt}/${maxReconnectAttempts} in ${delay}ms`);

            setReconnectAttempt(nextAttempt);
            setIsReconnecting(true);
            setState('Reconnecting');

            if (onReconnecting) onReconnecting(nextAttempt, maxReconnectAttempts);

            // Schedule reconnection
            reconnectTimeoutRef.current = setTimeout(() => {
              startTranscriptionInternal(true);
            }, delay);
          } else {
            // Can't reconnect - final error
            console.error('[SONIOX] ✗ Cannot reconnect:',
              isManualStop.current ? 'manual stop' :
              !shouldReconnect.current ? 'reconnect disabled' :
              !isRecoverableError(status, errorCode) ? 'non-recoverable error' :
              'max attempts reached');

            setState('Error');
            shouldReconnect.current = false;
            if (onError) onError(err);
          }
        },

        onStateChange: ({ newState }) => {
          // Don't override Reconnecting state
          if (state !== 'Reconnecting') {
            setState(newState);
          }
        },

        onPartialResult: (result) => {
          const newFinalTokens = [];
          const newNonFinalTokens = [];

          for (const token of result.tokens) {
            if (token.text === '<end>' || token.text === '</s>' || token.text === '<s>' || token.text === '<unk>') {
              continue;
            }

            const tokenObj = {
              text: token.text || '',
              speaker: token.speaker || null,
              is_final: token.is_final || false,
              timestamp: Date.now(),
            };

            if (token.is_final) {
              newFinalTokens.push(tokenObj);
            } else {
              newNonFinalTokens.push(tokenObj);
            }
          }

          if (newFinalTokens.length > 0) {
            setFinalTokens((previousTokens) => [...previousTokens, ...newFinalTokens]);
          }

          setNonFinalTokens(newNonFinalTokens);
        },
      });

      return true;
    } catch (error) {
      console.error('[SONIOX] Error starting transcription:', error);
      setError(error);
      setState('Error');
      if (onError) onError(error);
      return false;
    }
  }, [onError, onStarted, onFinished, onReconnecting, onReconnected, enableSpeakerDiarization, reconnectAttempt, maxReconnectAttempts, state]);

  const startTranscription = useCallback(() => {
    return startTranscriptionInternal(false);
  }, [startTranscriptionInternal]);

  const stopTranscription = useCallback(() => {
    console.log('[SONIOX] Manual stop requested');
    isManualStop.current = true;
    shouldReconnect.current = false;

    // Clear any pending reconnection
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }

    if (sonioxClient.current) {
      sonioxClient.current.stop();
      setState('Stopped');
    }

    setIsReconnecting(false);
    setReconnectAttempt(0);
  }, []);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      if (sonioxClient.current) {
        sonioxClient.current.cancel();
      }
    };
  }, []);

  return {
    startTranscription,
    stopTranscription,
    state,
    finalTokens,
    nonFinalTokens,
    error,
    isRecording: state === 'Recording',
    isReconnecting,
    reconnectAttempt,
  };
}
