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


class Config:
    """Main configuration class."""
    server: ServerConfig = ServerConfig()
    transcription: TranscriptionConfig = TranscriptionConfig()
    drive: DriveConfig = DriveConfig()
    autosave: AutosaveConfig = AutosaveConfig()
    email: EmailConfig = EmailConfig()


# Global config instance
config = Config()




