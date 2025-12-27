/**
 * Session Configuration
 * Centralized configuration for session timing and limits.
 */

const sessionConfig = {
  // Maximum session duration in milliseconds
  // Production: 60 * 60 * 1000 (60 minutes)
  // Testing: 30 * 1000 (30 seconds)
  maxDuration: 60 * 60 * 1000, // CHANGE THIS VALUE TO SWITCH BETWEEN TEST/PRODUCTION

  // Auto-save interval in milliseconds
  autoSaveInterval: 60 * 1000, // 1 minute

  // Warning thresholds (as fractions of maxDuration)
  warningThreshold: 3/4,  // Warning at 3/4 of max time (45min for 60min)
  criticalThreshold: 11/12, // Critical at 11/12 of max time (55min for 60min)
};

export default sessionConfig;
