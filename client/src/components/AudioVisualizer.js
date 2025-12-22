import React from 'react';

/**
 * Audio Visualizer Component
 * Displays real-time waveform visualization of microphone input.
 *
 * @param {Uint8Array} waveformData - Frequency data from Web Audio API
 * @param {boolean} isActive - Whether audio is currently being captured
 */
function AudioVisualizer({ waveformData, isActive }) {
  const barCount = Math.min(waveformData.length, 32); // Limit to 32 bars

  return (
    <div
      style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        gap: '2px',
        height: '60px',
        padding: '10px',
        background: '#F8F9FA',
        borderRadius: '8px',
        marginBottom: '20px',
        border: `2px solid ${isActive ? '#10B981' : '#E9ECEF'}`,
      }}
    >
      {Array.from({ length: barCount }).map((_, i) => {
        const value = waveformData[i] || 0;
        const height = Math.max(5, (value / 255) * 50); // Scale 0-50px
        const color = isActive ? '#10B981' : '#D1D5DB';

        return (
          <div
            key={i}
            style={{
              width: '4px',
              height: `${height}px`,
              backgroundColor: color,
              borderRadius: '2px',
              transition: 'height 0.1s ease-out',
            }}
          />
        );
      })}
    </div>
  );
}

export default AudioVisualizer;
