import nodemailer from 'nodemailer';
import { config } from '../config.js';

/**
 * Email service for sending notifications
 */
export class EmailService {
  constructor() {
    this.transporter = this.createTransporter();
  }

  /**
   * Create email transporter based on config
   */
  createTransporter() {
    if (config.email.provider === 'sendgrid') {
      // SendGrid uses SMTP
      return nodemailer.createTransport({
        host: 'smtp.sendgrid.net',
        port: 587,
        auth: {
          user: 'apikey',
          pass: config.email.sendgridApiKey,
        },
      });
    } else {
      // SMTP
      return nodemailer.createTransport({
        host: config.email.smtp.host,
        port: config.email.smtp.port,
        secure: config.email.smtp.port === 465,
        auth: {
          user: config.email.smtp.user,
          pass: config.email.smtp.password,
        },
      });
    }
  }

  /**
   * Send transcript notification email
   * @param {string} to - Recipient email
   * @param {Object} sessionInfo - Session information
   * @param {string} driveLink - Google Drive link to transcript
   */
  async sendTranscriptNotification(to, sessionInfo, driveLink) {
    const { patientName, date, time } = sessionInfo;

    const mailOptions = {
      from: config.email.from,
      to: to,
      subject: `Session Transcript Ready - ${patientName}`,
      html: `
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
          <h2>Session Transcript Ready</h2>
          <p>Your session transcript has been saved.</p>
          
          <div style="background: #f5f5f5; padding: 15px; border-radius: 5px; margin: 20px 0;">
            <p><strong>Patient:</strong> ${patientName}</p>
            <p><strong>Date:</strong> ${date}</p>
            <p><strong>Time:</strong> ${time}</p>
          </div>
          
          <p>
            <a href="${driveLink}" 
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
      `,
      text: `
Session Transcript Ready

Your session transcript has been saved.

Patient: ${patientName}
Date: ${date}
Time: ${time}

View transcript: ${driveLink}

---
Note: This transcript is stored in your Google Drive.
No recordings or transcripts are stored on our servers.
      `,
    };

    try {
      await this.transporter.sendMail(mailOptions);
      return { success: true };
    } catch (error) {
      console.error('Email send error:', error);
      return { success: false, error: error.message };
    }
  }

  /**
   * Send to admin (for debugging during MVP)
   * @param {string} subject - Email subject
   * @param {string} message - Email message
   */
  async sendToAdmin(subject, message) {
    if (!config.email.adminEmail) {
      return { success: false, error: 'Admin email not configured' };
    }

    const mailOptions = {
      from: config.email.from,
      to: config.email.adminEmail,
      subject: `[Note Taker] ${subject}`,
      text: message,
    };

    try {
      await this.transporter.sendMail(mailOptions);
      return { success: true };
    } catch (error) {
      console.error('Admin email error:', error);
      return { success: false, error: error.message };
    }
  }
}




