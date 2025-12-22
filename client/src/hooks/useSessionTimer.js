import { useState, useEffect, useRef, useCallback } from 'react';

/**
 * Hook for managing session time with warnings and auto-stop.
 *
 * @param {Object} options Configuration options
 * @param {number} options.maxDuration Max duration in milliseconds (default: 60 minutes)
 * @param {Function} options.onWarning Callback when warning threshold is reached
 * @param {Function} options.onMaxTime Callback when max time is reached (auto-stop)
 * @returns {Object} Timer state and controls
 */
export default function useSessionTimer({
  maxDuration = 60 * 60 * 1000, // 60 minutes default
  onWarning,
  onMaxTime,
} = {}) {
  const [elapsed, setElapsed] = useState(0);
  const [isRunning, setIsRunning] = useState(false);
  const startTimeRef = useRef(null);
  const intervalRef = useRef(null);
  const warningTriggeredRef = useRef({ warning: false, critical: false });

  // Warning thresholds
  const warningTime = 45 * 60 * 1000; // 45 minutes
  const criticalTime = 55 * 60 * 1000; // 55 minutes

  // Start timer
  const start = useCallback(() => {
    if (!isRunning) {
      startTimeRef.current = Date.now() - elapsed;
      setIsRunning(true);
      warningTriggeredRef.current = { warning: false, critical: false };
    }
  }, [isRunning, elapsed]);

  // Stop timer
  const stop = useCallback(() => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
    }
    setIsRunning(false);
  }, []);

  // Reset timer
  const reset = useCallback(() => {
    stop();
    setElapsed(0);
    startTimeRef.current = null;
    warningTriggeredRef.current = { warning: false, critical: false };
  }, [stop]);

  // Update elapsed time and check thresholds
  useEffect(() => {
    if (isRunning) {
      intervalRef.current = setInterval(() => {
        const now = Date.now();
        const newElapsed = now - startTimeRef.current;
        setElapsed(newElapsed);

        // Check warning threshold (45 minutes)
        if (
          newElapsed >= warningTime &&
          !warningTriggeredRef.current.warning
        ) {
          warningTriggeredRef.current.warning = true;
          if (onWarning) {
            onWarning('warning', 15); // 15 minutes remaining
          }
        }

        // Check critical threshold (55 minutes)
        if (
          newElapsed >= criticalTime &&
          !warningTriggeredRef.current.critical
        ) {
          warningTriggeredRef.current.critical = true;
          if (onWarning) {
            onWarning('critical', 5); // 5 minutes remaining
          }
        }

        // Check max time (60 minutes) - auto-stop
        if (newElapsed >= maxDuration) {
          stop();
          if (onMaxTime) {
            onMaxTime();
          }
        }
      }, 1000); // Update every second

      return () => {
        if (intervalRef.current) {
          clearInterval(intervalRef.current);
        }
      };
    }
  }, [isRunning, maxDuration, warningTime, criticalTime, onWarning, onMaxTime, stop]);

  // Calculate remaining time
  const remaining = Math.max(0, maxDuration - elapsed);

  // Determine warning level
  let warningLevel = 'normal';
  if (elapsed >= criticalTime) {
    warningLevel = 'critical';
  } else if (elapsed >= warningTime) {
    warningLevel = 'warning';
  }

  // Format time as MM:SS
  const formatTime = (ms) => {
    const totalSeconds = Math.floor(ms / 1000);
    const minutes = Math.floor(totalSeconds / 60);
    const seconds = totalSeconds % 60;
    return `${minutes}:${seconds.toString().padStart(2, '0')}`;
  };

  return {
    elapsed,
    remaining,
    isRunning,
    warningLevel,
    start,
    stop,
    reset,
    formatTime,
    elapsedFormatted: formatTime(elapsed),
    remainingFormatted: formatTime(remaining),
  };
}
