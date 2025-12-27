import { useState, useEffect, useRef, useCallback } from 'react';
import sessionConfig from '../config/sessionConfig';

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
  const intervalCounterRef = useRef(0); // Track how many intervals created
  const cleanupCounterRef = useRef(0); // Track how many times cleanup runs

  // Warning thresholds from config
  const warningTime = maxDuration * sessionConfig.warningThreshold;
  const criticalTime = maxDuration * sessionConfig.criticalThreshold;

  // Start timer
  const start = useCallback(() => {
    console.log('[TIMER] start() called, isRunning:', isRunning);
    setIsRunning((currentIsRunning) => {
      if (!currentIsRunning) {
        startTimeRef.current = Date.now() - elapsed;
        warningTriggeredRef.current = { warning: false, critical: false };
        console.log('[TIMER] Timer will start, startTime:', startTimeRef.current);
        return true;
      } else {
        console.log('[TIMER] Timer already running, ignoring start()');
        return currentIsRunning;
      }
    });
  }, [elapsed]);

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
    intervalCounterRef.current += 1;
    console.log('[TIMER] 🔄 useEffect RUN #' + intervalCounterRef.current + ', isRunning:', isRunning);
    console.log('[TIMER] 📊 Dependencies changed - checking which ones...');
    console.log('[TIMER]   - isRunning:', isRunning);
    console.log('[TIMER]   - onWarning function ID:', onWarning?.toString().substring(0, 50));
    console.log('[TIMER]   - onMaxTime function ID:', onMaxTime?.toString().substring(0, 50));
    console.log('[TIMER]   - stop function ID:', stop?.toString().substring(0, 50));

    if (isRunning) {
      console.log('[TIMER] ✅ Setting up interval, startTimeRef.current:', startTimeRef.current);
      console.log('[TIMER] ✅ Interval will tick every 1000ms');

      intervalRef.current = setInterval(() => {
        console.log('[TIMER] 🔔 TICK START - Inside setInterval callback');
        const now = Date.now();
        console.log('[TIMER]   - now:', now);
        console.log('[TIMER]   - startTimeRef.current:', startTimeRef.current);
        const newElapsed = now - startTimeRef.current;
        console.log('[TIMER]   - calculated newElapsed:', newElapsed, '(' + Math.floor(newElapsed / 1000) + ' seconds)');
        setElapsed(newElapsed);
        console.log('[TIMER] 🔔 TICK END - setElapsed called');

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

      console.log('[TIMER] ✅ Interval created with ID:', intervalRef.current);

      return () => {
        cleanupCounterRef.current += 1;
        console.log('[TIMER] 🧹 CLEANUP #' + cleanupCounterRef.current + ' - Clearing interval:', intervalRef.current);
        if (intervalRef.current) {
          clearInterval(intervalRef.current);
          console.log('[TIMER] 🧹 Interval cleared');
        }
      };
    } else {
      console.log('[TIMER] ❌ Not setting up interval (isRunning is false)');
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
