import { ProviderFactory } from '../providers/ProviderFactory.js';
import { config } from '../config.js';

/**
 * Transcription service that uses the configured provider
 * This is the main interface for transcription operations
 */
export class TranscriptionService {
  constructor() {
    // Get provider from config
    const providerName = config.transcription.provider;
    const providerConfig = config.transcription.providers[providerName] || {};

    // Create provider instance
    this.provider = ProviderFactory.createProvider(providerName, providerConfig);
  }

  /**
   * Get the current provider instance
   * @returns {TranscriptionProvider}
   */
  getProvider() {
    return this.provider;
  }

  /**
   * Start a streaming transcription session
   * @param {Object} options - Session options
   * @param {Function} onTranscript - Callback for transcript chunks
   * @param {Function} onError - Error callback
   * @returns {Promise<Object>} Session control object
   */
  async startSession(options = {}, onTranscript, onError) {
    const sessionOptions = {
      language: options.language || config.transcription.defaults.language,
      enableSpeakerDiarization: options.enableSpeakerDiarization !== false
        ? config.transcription.defaults.enableSpeakerDiarization
        : false,
      ...options,
    };

    return await this.provider.startStreamingSession(
      sessionOptions,
      onTranscript,
      onError
    );
  }

  /**
   * Process a batch audio file
   * @param {Buffer} audioBuffer - Audio file buffer
   * @param {Object} options - Processing options
   * @returns {Promise<Array>} Array of transcript segments
   */
  async processBatch(audioBuffer, options = {}) {
    const processOptions = {
      language: options.language || config.transcription.defaults.language,
      enableSpeakerDiarization: options.enableSpeakerDiarization !== false
        ? config.transcription.defaults.enableSpeakerDiarization
        : false,
      ...options,
    };

    return await this.provider.processBatch(audioBuffer, processOptions);
  }

  /**
   * Get provider information
   * @returns {Object} Provider info
   */
  getProviderInfo() {
    return {
      name: this.provider.getName(),
      supportsHebrew: this.provider.supportsLanguage('he-IL'),
      supportsSpeakerDiarization: this.provider.supportsSpeakerDiarization(),
    };
  }

  /**
   * Switch to a different provider (for testing)
   * @param {string} providerName - Name of the provider
   * @param {Object} providerConfig - Provider configuration
   */
  switchProvider(providerName, providerConfig = {}) {
    const fullConfig = {
      ...config.transcription.providers[providerName],
      ...providerConfig,
    };
    this.provider = ProviderFactory.createProvider(providerName, fullConfig);
  }
}




