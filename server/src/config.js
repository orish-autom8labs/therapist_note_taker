import dotenv from 'dotenv';

dotenv.config();

/**
 * Application configuration
 * Centralized configuration management
 */
export const config = {
  // Server configuration
  server: {
    port: process.env.PORT || 3001,
    nodeEnv: process.env.NODE_ENV || 'development',
  },

  // Transcription provider configuration
  transcription: {
    // Provider name: 'soniox', 'google', etc.
    provider: process.env.TRANSCRIPTION_PROVIDER || 'soniox',
    
    // Provider-specific config (can be overridden per request)
    providers: {
      soniox: {
        apiKey: process.env.SONIOX_API_KEY,
      },
      google: {
        projectId: process.env.GOOGLE_PROJECT_ID,
        credentials: process.env.GOOGLE_CREDENTIALS ? JSON.parse(process.env.GOOGLE_CREDENTIALS) : null,
      },
    },

    // Default transcription options
    defaults: {
      language: 'he-IL', // Hebrew (Israel)
      enableSpeakerDiarization: true,
      numSpeakers: 2,
    },
  },

  // Google Drive configuration
  drive: {
    // OAuth will be handled per-user, but we need client ID/secret
    clientId: process.env.GOOGLE_CLIENT_ID,
    clientSecret: process.env.GOOGLE_CLIENT_SECRET,
    redirectUri: process.env.GOOGLE_REDIRECT_URI || 'http://localhost:3001/auth/google/callback',
  },

  // Auto-save configuration
  autosave: {
    interval: 60000, // 1 minute in milliseconds
    tempFilePrefix: '.temp_',
    tempFileRetentionHours: 24,
  },

  // Email configuration
  email: {
    provider: process.env.EMAIL_PROVIDER || 'sendgrid', // 'sendgrid' or 'smtp'
    sendgridApiKey: process.env.SENDGRID_API_KEY,
    smtp: {
      host: process.env.SMTP_HOST,
      port: process.env.SMTP_PORT || 587,
      user: process.env.SMTP_USER,
      password: process.env.SMTP_PASSWORD,
    },
    from: process.env.EMAIL_FROM || 'noreply@notetaker.com',
    adminEmail: process.env.ADMIN_EMAIL, // For debugging during MVP
  },
};




