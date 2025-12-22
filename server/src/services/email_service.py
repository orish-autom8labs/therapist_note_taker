"""
Email service for sending notifications.
"""
import os
from typing import Dict, Any
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from ..config import config


class EmailService:
    """Email service for sending notifications."""
    
    def __init__(self):
        """Initialize email service."""
        self.provider = config.email.provider
        self.sendgrid_api_key = config.email.sendgrid_api_key
        self.smtp_config = config.email.smtp
        self.from_email = config.email.from_email
        self.admin_email = config.email.admin_email
    
    async def send_transcript_notification(
        self,
        to: str,
        session_info: Dict[str, Any],
        drive_link: str
    ) -> Dict[str, Any]:
        """
        Send transcript notification email.
        
        Args:
            to: Recipient email
            session_info: Session information (patient_name, date, time)
            drive_link: Google Drive link to transcript
        
        Returns:
            Dictionary with success status
        """
        patient_name = session_info.get('patient_name', 'Unknown')
        date = session_info.get('date', '')
        time = session_info.get('time', '')
        
        subject = f'Session Transcript Ready - {patient_name}'
        
        html_content = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h2>Session Transcript Ready</h2>
            <p>Your session transcript has been saved.</p>
            
            <div style="background: #f5f5f5; padding: 15px; border-radius: 5px; margin: 20px 0;">
                <p><strong>Patient:</strong> {patient_name}</p>
                <p><strong>Date:</strong> {date}</p>
                <p><strong>Time:</strong> {time}</p>
            </div>
            
            <p>
                <a href="{drive_link}" 
                   style="background: #4A90E2; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; display: inline-block;">
                    View Transcript in Google Drive
                </a>
            </p>
            
            <hr style="margin: 30px 0; border: none; border-top: 1px solid #eee;">
            <p style="color: #666; font-size: 12px;">
                Note: This transcript is stored in your Google Drive.<br>
                No recordings or transcripts are stored on our servers.
            </p>
        </div>
        """
        
        text_content = f"""
Session Transcript Ready

Your session transcript has been saved.

Patient: {patient_name}
Date: {date}
Time: {time}

View transcript: {drive_link}

---
Note: This transcript is stored in your Google Drive.
No recordings or transcripts are stored on our servers.
        """
        
        try:
            if self.provider == 'sendgrid':
                return await self._send_via_sendgrid(to, subject, html_content, text_content)
            else:
                return await self._send_via_smtp(to, subject, html_content, text_content)
        except Exception as e:
            print(f'Email send error: {e}')
            return {'success': False, 'error': str(e)}
    
    async def _send_via_sendgrid(
        self,
        to: str,
        subject: str,
        html_content: str,
        text_content: str
    ) -> Dict[str, Any]:
        """Send email via SendGrid."""
        if not self.sendgrid_api_key:
            raise ValueError("SendGrid API key not configured")
        
        message = Mail(
            from_email=self.from_email,
            to_emails=to,
            subject=subject,
            html_content=html_content,
            plain_text_content=text_content
        )
        
        sg = SendGridAPIClient(self.sendgrid_api_key)
        response = sg.send(message)
        
        return {'success': response.status_code in [200, 201, 202]}
    
    async def _send_via_smtp(
        self,
        to: str,
        subject: str,
        html_content: str,
        text_content: str
    ) -> Dict[str, Any]:
        """Send email via SMTP."""
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = self.from_email
        msg['To'] = to
        
        part1 = MIMEText(text_content, 'plain')
        part2 = MIMEText(html_content, 'html')
        
        msg.attach(part1)
        msg.attach(part2)
        
        with smtplib.SMTP(self.smtp_config.host, self.smtp_config.port) as server:
            if self.smtp_config.port == 587:
                server.starttls()
            server.login(self.smtp_config.user, self.smtp_config.password)
            server.send_message(msg)
        
        return {'success': True}
    
    async def send_to_admin(self, subject: str, message: str) -> Dict[str, Any]:
        """
        Send to admin (for debugging during MVP).
        
        Args:
            subject: Email subject
            message: Email message
        
        Returns:
            Dictionary with success status
        """
        if not self.admin_email:
            return {'success': False, 'error': 'Admin email not configured'}
        
        try:
            if self.provider == 'sendgrid':
                return await self._send_via_sendgrid(
                    self.admin_email,
                    f'[Note Taker] {subject}',
                    f'<pre>{message}</pre>',
                    message
                )
            else:
                return await self._send_via_smtp(
                    self.admin_email,
                    f'[Note Taker] {subject}',
                    f'<pre>{message}</pre>',
                    message
                )
        except Exception as e:
            print(f'Admin email error: {e}')
            return {'success': False, 'error': str(e)}




