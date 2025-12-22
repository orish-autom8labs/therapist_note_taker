import { useEffect, useRef, useState } from 'react';

/**
 * Hook for audio visualization using Web Audio API.
 * Creates a real-time waveform display based on microphone input.
 *
 * @param {MediaStream} audioStream - The microphone audio stream
 * @returns {Object} Waveform data and visualization state
 */
export default function useAudioVisualizer(audioStream) {
  const [waveformData, setWaveformData] = useState(new Uint8Array(32));
  const [isActive, setIsActive] = useState(false);
  const analyserRef = useRef(null);
  const animationRef = useRef(null);
  const audioContextRef = useRef(null);

  useEffect(() => {
    if (!audioStream) {
      setIsActive(false);
      return;
    }

    // Create Audio Context
    const audioContext = new (window.AudioContext || window.webkitAudioContext)();
    const analyser = audioContext.createAnalyser();
    analyser.fftSize = 64; // Small FFT size for real-time performance
    analyser.smoothingTimeConstant = 0.8; // Smooth out rapid changes

    // Connect audio stream to analyser
    const source = audioContext.createMediaStreamSource(audioStream);
    source.connect(analyser);

    analyserRef.current = analyser;
    audioContextRef.current = audioContext;
    setIsActive(true);

    // Animation loop to update waveform
    const updateWaveform = () => {
      if (!analyserRef.current) return;

      const dataArray = new Uint8Array(analyserRef.current.frequencyBinCount);
      analyserRef.current.getByteFrequencyData(dataArray);
      setWaveformData(dataArray);

      animationRef.current = requestAnimationFrame(updateWaveform);
    };

    updateWaveform();

    // Cleanup
    return () => {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
      if (audioContextRef.current) {
        audioContextRef.current.close();
      }
      setIsActive(false);
    };
  }, [audioStream]);

  return { waveformData, isActive };
}
