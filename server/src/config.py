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


class SummaryLevelConfig:
    """Configuration for a single summary quality level."""
    def __init__(
        self,
        name: str,
        label_he: str,
        use_chunking: bool,
        use_structured_extraction: bool,
        use_overlap: bool,
        stage2_provider: str,
        stage2_model: str,
        stage2_styles: list,
        use_verification: bool,
        verification_provider: str = '',
        verification_model: str = '',
    ):
        self.name = name
        self.label_he = label_he
        self.use_chunking = use_chunking
        self.use_structured_extraction = use_structured_extraction
        self.use_overlap = use_overlap
        self.stage2_provider = stage2_provider
        self.stage2_model = stage2_model
        self.stage2_styles = stage2_styles
        self.use_verification = use_verification
        self.verification_provider = verification_provider
        self.verification_model = verification_model


# Pre-defined summary levels
SUMMARY_LEVELS: dict[str, SummaryLevelConfig] = {
    'quick': SummaryLevelConfig(
        name='quick',
        label_he='סיכום מהיר',
        use_chunking=False,
        use_structured_extraction=False,
        use_overlap=False,
        stage2_provider=os.getenv('SUMMARIZATION_STAGE1_PROVIDER', 'deepseek'),
        stage2_model=os.getenv('SUMMARIZATION_STAGE1_MODEL', 'deepseek-chat'),
        stage2_styles=['key_topics'],
        use_verification=False,
    ),
    'standard': SummaryLevelConfig(
        name='standard',
        label_he='סיכום סטנדרטי',
        use_chunking=True,
        use_structured_extraction=True,
        use_overlap=True,
        stage2_provider=os.getenv('SUMMARIZATION_STAGE2_PROVIDER', 'claude'),
        stage2_model=os.getenv('SUMMARIZATION_STAGE2_MODEL', 'claude-3-haiku-20240307'),
        stage2_styles=['key_topics', 'detailed_notes'],
        use_verification=False,
    ),
    'clinical': SummaryLevelConfig(
        name='clinical',
        label_he='סיכום קליני מאומת',
        use_chunking=True,
        use_structured_extraction=True,
        use_overlap=True,
        stage2_provider=os.getenv('SUMMARIZATION_STAGE2_PROVIDER', 'claude'),
        stage2_model=os.getenv('SUMMARIZATION_STAGE2_MODEL', 'claude-3-haiku-20240307'),
        stage2_styles=['key_topics', 'detailed_notes'],
        use_verification=True,
        verification_provider=os.getenv('SUMMARIZATION_STAGE3_PROVIDER', 'claude'),
        verification_model=os.getenv('SUMMARIZATION_STAGE3_MODEL', 'claude-3-haiku-20240307'),
    ),
}


class SummarizationConfig:
    """
    Summarization configuration.

    Three-stage pipeline:
    - Stage 1 (Extraction): Structured extraction from transcript chunks
    - Stage 2 (Synthesis): Quality model for final summary generation
    - Stage 3 (Verification): Faithfulness check against extractions (Level 3 only)

    Change these settings to modify summarization behavior.
    """

    # Master switch
    enabled: bool = os.getenv('SUMMARIZATION_ENABLED', 'true').lower() == 'true'

    # Stage 1: Extraction
    stage1_provider: str = os.getenv('SUMMARIZATION_STAGE1_PROVIDER', 'deepseek')
    stage1_model: str = os.getenv('SUMMARIZATION_STAGE1_MODEL', 'deepseek-chat')
    stage1_approach: str = os.getenv('SUMMARIZATION_STAGE1_APPROACH', 'speaker_segments')
    stage1_chunk_minutes_min: int = int(os.getenv('SUMMARIZATION_CHUNK_MIN_MINUTES', '3'))
    stage1_chunk_minutes_max: int = int(os.getenv('SUMMARIZATION_CHUNK_MAX_MINUTES', '8'))

    # Stage 2: Synthesis
    stage2_provider: str = os.getenv('SUMMARIZATION_STAGE2_PROVIDER', 'claude')
    stage2_model: str = os.getenv('SUMMARIZATION_STAGE2_MODEL', 'claude-3-haiku-20240307')
    stage2_styles: list = ['key_topics', 'detailed_notes']

    # Stage 3: Verification
    stage3_provider: str = os.getenv('SUMMARIZATION_STAGE3_PROVIDER', 'claude')
    stage3_model: str = os.getenv('SUMMARIZATION_STAGE3_MODEL', 'claude-3-haiku-20240307')

    # Summary levels to generate (evaluation mode: all three)
    summary_levels: list = os.getenv(
        'SUMMARIZATION_LEVELS', 'quick,standard,clinical'
    ).split(',')

    # Provider API keys
    deepseek_api_key: str = os.getenv('DEEPSEEK_API_KEY', '')
    anthropic_api_key: str = os.getenv('ANTHROPIC_API_KEY', '')
    openai_api_key: str = os.getenv('OPENAI_API_KEY', '')

    # Safety limits
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




