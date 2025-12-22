import { TranscriptionProvider } from './TranscriptionProvider.js';
import speech from '@google-cloud/speech';

/**
 * Google Cloud Speech-to-Text provider implementation
 * Alternative provider for Hebrew transcription
 */
export class GoogleProvider extends TranscriptionProvider {
  constructor(config) {
    super(config);
    this.projectId = config.projectId;
    this.credentials = config.credentials;
    this.client = null;
  }

  getName() {
    return 'Google Cloud Speech-to-Text';
  }

  supportsLanguage(languageCode) {
    // Google supports Hebrew (he-IL)
    return ['he', 'he-IL', 'en', 'en-US'].includes(languageCode);
  }

  supportsSpeakerDiarization() {
    return true;
  }

  /**
   * Initialize Google Speech client
   */
  async initialize() {
    if (!this.client) {
      this.client = new speech.SpeechClient({
        projectId: this.projectId,
        credentials: this.credentials,
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

    const request = {
      config: {
        encoding: 'WEBM_OPUS', // or 'LINEAR16' depending on audio format
        sampleRateHertz: 16000,
        languageCode: language,
        enableSpeakerDiarization: enableSpeakerDiarization,
        diarizationSpeakerCount: 2,
        model: 'latest_long', // Better for longer sessions
      },
      interimResults: true, // Get partial results
    };

    let recognizeStream = null;
    let isActive = true;

    try {
      recognizeStream = this.client
        .streamingRecognize(request)
        .on('error', (error) => {
          if (isActive) {
            onError(error);
          }
        })
        .on('data', (data) => {
          if (!isActive) return;

          try {
            const transcriptChunk = this.parseGoogleResponse(data);
            
            if (transcriptChunk && transcriptChunk.text) {
              onTranscript({
                text: transcriptChunk.text,
                speaker: transcriptChunk.speaker || null,
                isFinal: transcriptChunk.isFinal,
                timestamp: Date.now(),
              });
            }
          } catch (err) {
            console.error('Error parsing Google response:', err);
            onError(err);
          }
        });

      return {
        sendAudio: (audioChunk) => {
          if (isActive && recognizeStream) {
            recognizeStream.write({ audioContent: audioChunk });
          }
        },
        stop: async () => {
          isActive = false;
          if (recognizeStream) {
            recognizeStream.end();
            recognizeStream = null;
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

    const request = {
      config: {
        encoding: 'WEBM_OPUS',
        sampleRateHertz: 16000,
        languageCode: language,
        enableSpeakerDiarization: enableSpeakerDiarization,
        diarizationSpeakerCount: 2,
      },
      audio: {
        content: audioBuffer.toString('base64'),
      },
    };

    try {
      const [response] = await this.client.recognize(request);
      return this.parseGoogleBatchResponse(response);
    } catch (error) {
      throw new Error(`Google batch processing failed: ${error.message}`);
    }
  }

  /**
   * Parse Google streaming response
   */
  parseGoogleResponse(data) {
    if (data.results && data.results.length > 0) {
      const result = data.results[0];
      const alternative = result.alternatives[0];
      
      if (alternative) {
        return {
          text: alternative.transcript,
          speaker: alternative.words && alternative.words[0]?.speakerTag
            ? `Speaker ${alternative.words[0].speakerTag}`
            : null,
          isFinal: result.isFinalAlternative,
        };
      }
    }

    return null;
  }

  /**
   * Parse Google batch response
   */
  parseGoogleBatchResponse(response) {
    const segments = [];

    if (response.results && response.results.length > 0) {
      for (const result of response.results) {
        if (result.alternatives && result.alternatives.length > 0) {
          const alternative = result.alternatives[0];
          
          if (alternative.words && alternative.words.length > 0) {
            let currentSegment = {
              text: '',
              speaker: null,
              startTime: null,
              endTime: null,
            };

            for (const word of alternative.words) {
              const speakerTag = word.speakerTag;
              
              if (currentSegment.speaker !== speakerTag) {
                if (currentSegment.text) {
                  segments.push({
                    ...currentSegment,
                    speaker: currentSegment.speaker ? `Speaker ${currentSegment.speaker}` : null,
                  });
                }
                currentSegment = {
                  text: word.word,
                  speaker: speakerTag,
                  startTime: word.startTime?.seconds || null,
                  endTime: word.endTime?.seconds || null,
                };
              } else {
                currentSegment.text += ' ' + word.word;
                currentSegment.endTime = word.endTime?.seconds || null;
              }
            }

            if (currentSegment.text) {
              segments.push({
                ...currentSegment,
                speaker: currentSegment.speaker ? `Speaker ${currentSegment.speaker}` : null,
              });
            }
          }
        }
      }
    }

    return segments;
  }
}

