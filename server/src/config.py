"""
Application configuration.
Centralized configuration management.
"""
import os
from typing import Dict, Any
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()


class ServerConfig:
    """Server configuration."""
    port: int = int(os.getenv('PORT', '3001'))
    node_env: str = os.getenv('NODE_ENV', 'development')


class TranscriptionDefaults:
    """Default transcription options."""
    language: str = 'he-IL'
    enable_speaker_diarization: bool = True
    num_speakers: int = 2


class TranscriptionConfig:
    """Transcription configuration."""
    provider: str = os.getenv('TRANSCRIPTION_PROVIDER', 'soniox')
    defaults: TranscriptionDefaults = TranscriptionDefaults()
    
    @property
    def providers(self) -> Dict[str, Dict[str, Any]]:
        """Get provider configurations."""
        return {
            'soniox': {
                'api_key': os.getenv('SONIOX_API_KEY'),
            },
            'google': {
                'project_id': os.getenv('GOOGLE_PROJECT_ID'),
                'credentials': os.getenv('GOOGLE_CREDENTIALS'),
            },
        }


class DriveConfig:
    """Google Drive configuration."""
    client_id: str = os.getenv('GOOGLE_CLIENT_ID', '')
    client_secret: str = os.getenv('GOOGLE_CLIENT_SECRET', '')
    redirect_uri: str = os.getenv('GOOGLE_REDIRECT_URI', 'http://localhost:3001/auth/google/callback')


class AutosaveConfig:
    """Auto-save configuration."""
    interval: int = 60000  # 1 minute in milliseconds
    temp_file_prefix: str = '.temp_'
    temp_file_retention_hours: int = 24


class SMTPConfig:
    """SMTP configuration."""
    host: str = os.getenv('SMTP_HOST', '')
    port: int = int(os.getenv('SMTP_PORT', '587'))
    user: str = os.getenv('SMTP_USER', '')
    password: str = os.getenv('SMTP_PASSWORD', '')


class EmailConfig:
    """Email configuration."""
    provider: str = os.getenv('EMAIL_PROVIDER', 'sendgrid')
    sendgrid_api_key: str = os.getenv('SENDGRID_API_KEY', '')
    smtp: SMTPConfig = SMTPConfig()
    from_email: str = os.getenv('EMAIL_FROM', 'noreply@notetaker.com')
    admin_email: str = os.getenv('ADMIN_EMAIL', '')


class SummarizationConfig:
    """
    Summarization configuration.

    Two-stage pipeline:
    - Stage 1 (Chunking): Cheap model for summarizing transcript segments
    - Stage 2 (Synthesis): Quality model for final summary generation

    Change these settings to modify summarization behavior.
    """

    # ═══════════════════════════════════════════════════════════════════
    # MASTER SWITCH
    # ═══════════════════════════════════════════════════════════════════
    enabled: bool = os.getenv('SUMMARIZATION_ENABLED', 'true').lower() == 'true'

    # ═══════════════════════════════════════════════════════════════════
    # STAGE 1: CHUNKING CONFIGURATION
    # Change these lines to modify chunking behavior
    # ═══════════════════════════════════════════════════════════════════
    stage1_provider: str = os.getenv('SUMMARIZATION_STAGE1_PROVIDER', 'deepseek')
    stage1_model: str = os.getenv('SUMMARIZATION_STAGE1_MODEL', 'deepseek-chat')
    stage1_approach: str = os.getenv('SUMMARIZATION_STAGE1_APPROACH', 'speaker_segments')
    # Options: 'speaker_segments' (breaks at speaker changes, 3-8 min)
    #          'fixed_time' (fixed intervals)
    stage1_chunk_minutes_min: int = int(os.getenv('SUMMARIZATION_CHUNK_MIN_MINUTES', '3'))
    stage1_chunk_minutes_max: int = int(os.getenv('SUMMARIZATION_CHUNK_MAX_MINUTES', '8'))

    # ═══════════════════════════════════════════════════════════════════
    # STAGE 2: SYNTHESIS CONFIGURATION
    # Change these lines to modify synthesis behavior
    # ═══════════════════════════════════════════════════════════════════
    stage2_provider: str = os.getenv('SUMMARIZATION_STAGE2_PROVIDER', 'claude')
    stage2_model: str = os.getenv('SUMMARIZATION_STAGE2_MODEL', 'claude-3-haiku-20240307')
    stage2_styles: list = ['key_topics', 'detailed_notes']  # Generate both styles

    # ═══════════════════════════════════════════════════════════════════
    # PROVIDER API KEYS (from environment)
    # ═══════════════════════════════════════════════════════════════════
    deepseek_api_key: str = os.getenv('DEEPSEEK_API_KEY', '')
    anthropic_api_key: str = os.getenv('ANTHROPIC_API_KEY', '')
    openai_api_key: str = os.getenv('OPENAI_API_KEY', '')

    # ═══════════════════════════════════════════════════════════════════
    # SAFETY LIMITS
    # ═══════════════════════════════════════════════════════════════════
    max_cost_per_session_usd: float = float(os.getenv('SUMMARIZATION_MAX_COST_USD', '0.50'))


class FirestoreConfig:
    """Firestore configuration for session metadata tracking."""
    enabled: bool = os.getenv('FIRESTORE_ENABLED', 'false').lower() == 'true'
    project_id: str = os.getenv('GCP_PROJECT_ID', 'therapistnottaker')
    encryption_key: str = os.getenv('FIRESTORE_ENCRYPTION_KEY', '')
    collection_prefix: str = os.getenv('FIRESTORE_COLLECTION_PREFIX', 'prod')


class Config:
    """Main configuration class."""
    server: ServerConfig = ServerConfig()
    transcription: TranscriptionConfig = TranscriptionConfig()
    drive: DriveConfig = DriveConfig()
    autosave: AutosaveConfig = AutosaveConfig()
    email: EmailConfig = EmailConfig()
    summarization: SummarizationConfig = SummarizationConfig()
    firestore: FirestoreConfig = FirestoreConfig()


# Global config instance
config = Config()




