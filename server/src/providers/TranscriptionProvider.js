/**
 * Abstract base class for transcription providers
 * All transcription providers must implement this interface
 */
export class TranscriptionProvider {
  /**
   * Initialize the provider with configuration
   * @param {Object} config - Provider-specific configuration
   */
  constructor(config) {
    this.config = config;
    if (this.constructor === TranscriptionProvider) {
      throw new Error('TranscriptionProvider is abstract and cannot be instantiated directly');
    }
  }

  /**
   * Start a real-time transcription session
   * @param {Object} options - Session options
   * @param {string} options.language - Language code (e.g., 'he-IL' for Hebrew)
   * @param {boolean} options.enableSpeakerDiarization - Enable speaker identification
   * @param {Function} onTranscript - Callback for transcript chunks
   * @param {Function} onError - Error callback
   * @returns {Promise<Object>} Session object with methods to control the session
   */
  async startStreamingSession(options, onTranscript, onError) {
    throw new Error('startStreamingSession must be implemented by subclass');
  }

  /**
   * Process a batch audio file (for fallback/recovery)
   * @param {Buffer} audioBuffer - Audio file buffer
   * @param {Object} options - Processing options
   * @returns {Promise<Array>} Array of transcript segments
   */
  async processBatch(audioBuffer, options) {
    throw new Error('processBatch must be implemented by subclass');
  }

  /**
   * Get provider name
   * @returns {string} Provider name
   */
  getName() {
    throw new Error('getName must be implemented by subclass');
  }

  /**
   * Check if provider supports a specific language
   * @param {string} languageCode - Language code
   * @returns {boolean}
   */
  supportsLanguage(languageCode) {
    throw new Error('supportsLanguage must be implemented by subclass');
  }

  /**
   * Check if provider supports speaker diarization
   * @returns {boolean}
   */
  supportsSpeakerDiarization() {
    throw new Error('supportsSpeakerDiarization must be implemented by subclass');
  }
}




