import React from 'react';
import sessionConfig from '../config/sessionConfig';

/**
 * Session Timer Display Component
 * Shows elapsed time, remaining time, and warning indicators.
 *
 * @param {number} elapsed - Elapsed time in milliseconds
 * @param {number} remaining - Remaining time in milliseconds
 * @param {string} warningLevel - 'normal', 'warning', or 'critical'
 * @param {Function} formatTime - Function to format time as MM:SS
 */
function SessionTimer({ elapsed, remaining, warningLevel, formatTime }) {
  const maxDuration = sessionConfig.maxDuration;
  const percentage = (elapsed / maxDuration) * 100;

  // Colors based on warning level
  const colors = {
    normal: '#10B981',
    warning: '#F59E0B',
    critical: '#EF4444',
  };

  const color = colors[warningLevel] || colors.normal;

  return (
    <div>
      {/* Timer Display */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: '10px',
          padding: '15px',
          background: '#F8F9FA',
          borderRadius: '8px',
          border: `2px solid ${color}`,
        }}
      >
        <div>
          <div style={{ fontSize: '12px', color: '#6B7280', marginBottom: '4px' }}>
            Elapsed
          </div>
          <div style={{ fontSize: '24px', fontWeight: '600', color }}>
            {formatTime(elapsed)}
          </div>
        </div>

        <div style={{ textAlign: 'right' }}>
          <div style={{ fontSize: '12px', color: '#6B7280', marginBottom: '4px' }}>
            Remaining
          </div>
          <div style={{ fontSize: '24px', fontWeight: '600', color }}>
            {formatTime(remaining)}
          </div>
        </div>
      </div>

      {/* Progress Bar */}
      <div
        style={{
          width: '100%',
          height: '8px',
          background: '#E5E7EB',
          borderRadius: '4px',
          overflow: 'hidden',
          marginBottom: '10px',
        }}
      >
        <div
          style={{
            width: `${percentage}%`,
            height: '100%',
            background: color,
            transition: 'width 1s linear',
          }}
        />
      </div>

      {/* Warning Banners */}
      {warningLevel === 'warning' && (
        <div
          style={{
            padding: '12px',
            background: '#FEF3C7',
            color: '#92400E',
            borderRadius: '8px',
            marginBottom: '10px',
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
          }}
        >
          <span style={{ fontSize: '18px' }}>⚠️</span>
          <span style={{ fontWeight: '500' }}>
            {formatTime(remaining)} remaining - prepare to wrap up
          </span>
        </div>
      )}

      {warningLevel === 'critical' && (
        <div
          style={{
            padding: '12px',
            background: '#FEE2E2',
            color: '#991B1B',
            borderRadius: '8px',
            marginBottom: '10px',
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            animation: 'pulse 2s infinite',
          }}
        >
          <span style={{ fontSize: '18px' }}>🔴</span>
          <span style={{ fontWeight: '600' }}>
            {formatTime(remaining)} remaining - session will auto-stop soon!
          </span>
        </div>
      )}
    </div>
  );
}

export default SessionTimer;
