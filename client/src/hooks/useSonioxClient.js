import { useCallback, useEffect, useRef, useState } from 'react';
import { SonioxClient } from '@soniox/speech-to-text-web';
import { getTemporaryAPIKey } from '../services/sonioxService';

/**
 * Custom hook for Soniox SDK integration.
 * EXACTLY matches the official Soniox example pattern.
 * 
 * @param {Object} options
 * @param {Function} options.onError - Callback when errors occur
 * @param {Function} options.onStarted - Callback when transcription starts
 * @param {Function} options.onFinished - Callback when transcription finishes
 * @param {string} options.language - Language code (e.g., 'he' for Hebrew)
 * @param {boolean} options.enableSpeakerDiarization - Enable speaker diarization
 * @returns {Object} Transcription state and controls
 */
export default function useSonioxClient({
  onError,
  onStarted,
  onFinished,
  language = 'he', // Hebrew by default
  enableSpeakerDiarization = true,
}) {
  const sonioxClient = useRef(null);

  if (sonioxClient.current == null) {
    sonioxClient.current = new SonioxClient({
      apiKey: getTemporaryAPIKey, // Function that returns temporary key
    });
  }

  const [state, setState] = useState('Init');
  const [finalTokens, setFinalTokens] = useState([]);
  const [nonFinalTokens, setNonFinalTokens] = useState([]);
  const [error, setError] = useState(null);

  const startTranscription = useCallback(async () => {
    if (!sonioxClient.current) {
      const error = new Error('Soniox client not initialized');
      setError(error);
      if (onError) onError(error);
      return;
    }

    // Reset tokens (like official example)
    setFinalTokens([]);
    setNonFinalTokens([]);
    setError(null);

    try {
      await sonioxClient.current.start({
        model: 'stt-rt-v3',
        enableLanguageIdentification: true, // Let Soniox detect language automatically
        enableSpeakerDiarization: enableSpeakerDiarization,
        enableEndpointDetection: true,

        onStarted: () => {
          setState('Recording');
          if (onStarted) onStarted();
        },

        onFinished: () => {
          setState('Finished');
          if (onFinished) onFinished();
        },

        onError: (status, message, errorCode) => {
          const error = new Error(message || 'Transcription error');
          error.status = status;
          error.errorCode = errorCode;
          setError(error);
          setState('Error');
          if (onError) onError(error);
        },

        onStateChange: ({ newState }) => {
          setState(newState);
        },

        // EXACTLY like official example: sort tokens by final/non-final
        onPartialResult: (result) => {
          console.log('[HOOK] Received result:', result);
          const newFinalTokens = [];
          const newNonFinalTokens = [];

          for (const token of result.tokens) {
            const tokenObj = {
              text: token.text || '',
              speaker: token.speaker_label ? `Speaker ${token.speaker_label}` : null,
              is_final: token.is_final || false,
              timestamp: Date.now(),
            };

            if (token.is_final) {
              newFinalTokens.push(tokenObj);
            } else {
              newNonFinalTokens.push(tokenObj);
            }
          }

          console.log('[HOOK] New final tokens:', newFinalTokens);
          console.log('[HOOK] New non-final tokens:', newNonFinalTokens);

          // Append new final tokens (like official example: [...previousTokens, ...newFinalTokens])
          if (newFinalTokens.length > 0) {
            setFinalTokens((previousTokens) => {
              const updated = [...previousTokens, ...newFinalTokens];
              console.log('[HOOK] Updated finalTokens:', updated);
              return updated;
            });
          }

          // Replace non-final tokens entirely (like official example: setNonFinalTokens(newNonFinalTokens))
          // This is the key: ALWAYS REPLACE, even if empty - prevents accumulation/degradation
          // The official example always calls setNonFinalTokens, not conditionally
          console.log('[HOOK] Setting nonFinalTokens:', newNonFinalTokens);
          setNonFinalTokens(newNonFinalTokens);
        },
      });
    } catch (error) {
      console.error('[SONIOX] Error starting transcription:', error);
      setError(error);
      setState('Error');
      if (onError) onError(error);
    }
  }, [onError, onStarted, onFinished, language, enableSpeakerDiarization]);

  const stopTranscription = useCallback(() => {
    if (sonioxClient.current) {
      sonioxClient.current.stop();
      setState('Stopped');
    }
  }, []);

  useEffect(() => {
    return () => {
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
  };
}
