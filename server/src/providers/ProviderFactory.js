import { SonioxProvider } from './SonioxProvider.js';
import { GoogleProvider } from './GoogleProvider.js';

/**
 * Factory for creating transcription provider instances
 * Add new providers here to make them available
 */
export class ProviderFactory {
  /**
   * Create a transcription provider instance
   * @param {string} providerName - Name of the provider ('soniox', 'google', etc.)
   * @param {Object} config - Provider-specific configuration
   * @returns {TranscriptionProvider} Provider instance
   */
  static createProvider(providerName, config) {
    const normalizedName = providerName.toLowerCase();

    switch (normalizedName) {
      case 'soniox':
        return new SonioxProvider({
          apiKey: config.apiKey || process.env.SONIOX_API_KEY,
        });

      case 'google':
      case 'google-cloud':
      case 'google-speech':
        return new GoogleProvider({
          projectId: config.projectId || process.env.GOOGLE_PROJECT_ID,
          credentials: config.credentials || JSON.parse(process.env.GOOGLE_CREDENTIALS || '{}'),
        });

      default:
        throw new Error(`Unknown transcription provider: ${providerName}. Available providers: soniox, google`);
    }
  }

  /**
   * Get list of available providers
   * @returns {Array<string>} List of provider names
   */
  static getAvailableProviders() {
    return ['soniox', 'google'];
  }

  /**
   * Get provider information
   * @param {string} providerName - Name of the provider
   * @returns {Object} Provider information
   */
  static getProviderInfo(providerName) {
    const normalizedName = providerName.toLowerCase();

    const providers = {
      soniox: {
        name: 'Soniox',
        supportsHebrew: true,
        supportsSpeakerDiarization: true,
        supportsStreaming: true,
        description: 'High accuracy Hebrew transcription with speaker diarization',
      },
      google: {
        name: 'Google Cloud Speech-to-Text',
        supportsHebrew: true,
        supportsSpeakerDiarization: true,
        supportsStreaming: true,
        description: 'Google Cloud Speech-to-Text with Hebrew support',
      },
    };

    return providers[normalizedName] || null;
  }
}




