import { useState, useEffect, useRef, useCallback } from 'react';

const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:3001';

const POLL_INTERVAL_MS = 5000; // 5 seconds
const MAX_POLL_DURATION_MS = 5 * 60 * 1000; // 5 minutes

/**
 * Hook that polls the session status endpoint to track summary generation.
 *
 * @param {string|null} sessionId - Session ID to poll (null to skip)
 * @returns {{ status, summary, error, isPolling }}
 */
export default function useSummaryPolling(sessionId) {
  const [status, setStatus] = useState(null); // transcript_saved | summarizing | completed | summarization_failed
  const [summary, setSummary] = useState(null); // { webViewLink, fileName }
  const [transcript, setTranscript] = useState(null); // { webViewLink, fileName }
  const [error, setError] = useState(null);
  const [isPolling, setIsPolling] = useState(false);
  const intervalRef = useRef(null);
  const startTimeRef = useRef(null);

  const stopPolling = useCallback(() => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
    setIsPolling(false);
  }, []);

  useEffect(() => {
    if (!sessionId) return;

    const poll = async () => {
      // Check timeout
      if (Date.now() - startTimeRef.current > MAX_POLL_DURATION_MS) {
        console.log('[POLL] Timeout reached, stopping polling');
        stopPolling();
        setStatus('timeout');
        return;
      }

      try {
        const response = await fetch(`${API_BASE}/api/sessions/${sessionId}/status`);

        if (!response.ok) {
          // 404 means Firestore might not have the doc yet, keep polling
          if (response.status === 404) return;
          // 503 means Firestore not enabled, stop polling
          if (response.status === 503) {
            stopPolling();
            return;
          }
          return;
        }

        const data = await response.json();
        setStatus(data.status);

        if (data.transcript) {
          setTranscript(data.transcript);
        }

        if (data.status === 'completed' && data.summary) {
          setSummary(data.summary);
          stopPolling();
        } else if (data.status === 'summarization_failed') {
          setError(data.error || 'Summary generation failed');
          stopPolling();
        }
      } catch (err) {
        console.error('[POLL] Error polling status:', err);
        // Don't stop polling on network errors - could be transient
      }
    };

    // Start polling
    startTimeRef.current = Date.now();
    setIsPolling(true);
    poll(); // First poll immediately
    intervalRef.current = setInterval(poll, POLL_INTERVAL_MS);

    return () => stopPolling();
  }, [sessionId, stopPolling]);

  return { status, summary, transcript, error, isPolling };
}
