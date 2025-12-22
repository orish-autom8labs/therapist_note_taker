import { TranscriptionProvider } from './TranscriptionProvider.js';
import { createClient } from 'soniox';

/**
 * Soniox transcription provider implementation
 * High accuracy Hebrew transcription with speaker diarization
 */
export class SonioxProvider extends TranscriptionProvider {
  constructor(config) {
    super(config);
    this.apiKey = config.apiKey;
    this.client = null;
  }

  getName() {
    return 'Soniox';
  }

  supportsLanguage(languageCode) {
    // Soniox supports Hebrew and many other languages
    return ['he', 'he-IL', 'en', 'en-US'].includes(languageCode);
  }

  supportsSpeakerDiarization() {
    return true;
  }

  /**
   * Initialize Soniox client
   */
  async initialize() {
    if (!this.client) {
      this.client = createClient({
        api_key: this.apiKey,
      });
    }
    return this.client;
  }

  /**
   * Start streaming transcription session
   */
  async startStreamingSession(options, onTranscript, onError) {
    await this.initialize();

    const {
      language = 'he-IL',
      enableSpeakerDiarization = true,
    } = options;

    // Create streaming transcription request
    const request = {
      language: language,
      enable_speaker_diarization: enableSpeakerDiarization,
      num_speakers: 2, // Typically therapist and patient
    };

    let stream = null;
    let isActive = true;

    try {
      // Start streaming transcription
      stream = await this.client.transcribeStreamAsync(request);

      // Handle incoming transcript chunks
      stream.on('data', (data) => {
        if (!isActive) return;

        try {
          // Parse Soniox response format
          const transcriptChunk = this.parseSonioxResponse(data);
          
          if (transcriptChunk && transcriptChunk.text) {
            onTranscript({
              text: transcriptChunk.text,
              speaker: transcriptChunk.speaker || null,
              isFinal: transcriptChunk.is_final || false,
              timestamp: Date.now(),
            });
          }
        } catch (err) {
          console.error('Error parsing Soniox response:', err);
          onError(err);
        }
      });

      stream.on('error', (error) => {
        if (isActive) {
          onError(error);
        }
      });

      stream.on('end', () => {
        // Stream ended
      });

      // Return session control object
      return {
        sendAudio: (audioChunk) => {
          if (isActive && stream) {
            stream.write(audioChunk);
          }
        },
        stop: async () => {
          isActive = false;
          if (stream) {
            await stream.end();
            stream = null;
          }
        },
        isActive: () => isActive,
      };
    } catch (error) {
      onError(error);
      throw error;
    }
  }

  /**
   * Process batch audio file
   */
  async processBatch(audioBuffer, options) {
    await this.initialize();

    const {
      language = 'he-IL',
      enableSpeakerDiarization = true,
    } = options;

    try {
      const result = await this.client.transcribeFile(audioBuffer, {
        language: language,
        enable_speaker_diarization: enableSpeakerDiarization,
        num_speakers: 2,
      });

      return this.parseSonioxBatchResponse(result);
    } catch (error) {
      throw new Error(`Soniox batch processing failed: ${error.message}`);
    }
  }

  /**
   * Parse Soniox streaming response
   */
  parseSonioxResponse(data) {
    // Soniox returns structured data with words, speakers, etc.
    // Adjust based on actual Soniox API response format
    if (data.words && data.words.length > 0) {
      const text = data.words.map(w => w.text).join(' ');
      const speaker = data.words[0].speaker || null;
      
      return {
        text: text,
        speaker: speaker ? `Speaker ${speaker}` : null,
        is_final: data.is_final || false,
      };
    }
    
    // Fallback for different response formats
    if (data.text) {
      return {
        text: data.text,
        speaker: data.speaker || null,
        is_final: data.is_final || false,
      };
    }

    return null;
  }

  /**
   * Parse Soniox batch response
   */
  parseSonioxBatchResponse(result) {
    // Convert batch response to array of segments
    const segments = [];
    
    if (result.words) {
      let currentSegment = {
        text: '',
        speaker: null,
        startTime: null,
        endTime: null,
      };

      for (const word of result.words) {
        if (currentSegment.speaker !== word.speaker) {
          if (currentSegment.text) {
            segments.push({
              ...currentSegment,
              speaker: currentSegment.speaker ? `Speaker ${currentSegment.speaker}` : null,
            });
          }
          currentSegment = {
            text: word.text,
            speaker: word.speaker,
            startTime: word.start_time,
            endTime: word.end_time,
          };
        } else {
          currentSegment.text += ' ' + word.text;
          currentSegment.endTime = word.end_time;
        }
      }

      if (currentSegment.text) {
        segments.push({
          ...currentSegment,
          speaker: currentSegment.speaker ? `Speaker ${currentSegment.speaker}` : null,
        });
      }
    }

    return segments;
  }
}




