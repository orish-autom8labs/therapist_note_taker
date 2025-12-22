import { google } from 'googleapis';
import { config } from '../config.js';

/**
 * Google Drive service for saving transcripts
 */
export class DriveService {
  constructor() {
    this.oauth2Client = new google.auth.OAuth2(
      config.drive.clientId,
      config.drive.clientSecret,
      config.drive.redirectUri
    );
  }

  /**
   * Get OAuth URL for user authorization
   * @returns {string} Authorization URL
   */
  getAuthUrl() {
    const scopes = [
      'https://www.googleapis.com/auth/drive.file', // Create files only
    ];

    return this.oauth2Client.generateAuthUrl({
      access_type: 'offline',
      scope: scopes,
      prompt: 'consent', // Force consent to get refresh token
    });
  }

  /**
   * Exchange authorization code for tokens
   * @param {string} code - Authorization code
   * @returns {Promise<Object>} Tokens
   */
  async getTokens(code) {
    const { tokens } = await this.oauth2Client.getToken(code);
    return tokens;
  }

  /**
   * Set user's access token
   * @param {Object} tokens - Access and refresh tokens
   */
  setUserTokens(tokens) {
    this.oauth2Client.setCredentials(tokens);
  }

  /**
   * Save transcript to Google Drive
   * @param {string} content - Transcript content
   * @param {string} fileName - File name
   * @param {string} folderPath - Folder path (e.g., 'Clinic/Transcripts')
   * @returns {Promise<Object>} File info with webViewLink
   */
  async saveTranscript(content, fileName, folderPath = 'Clinic/Transcripts') {
    const drive = google.drive({ version: 'v3', auth: this.oauth2Client });

    // Find or create folder
    const folderId = await this.findOrCreateFolder(folderPath);

    // Create file
    const fileMetadata = {
      name: fileName,
      parents: [folderId],
    };

    const media = {
      mimeType: 'text/plain',
      body: content,
    };

    const file = await drive.files.create({
      requestBody: fileMetadata,
      media: media,
      fields: 'id, name, webViewLink, webContentLink',
    });

    return {
      fileId: file.data.id,
      fileName: file.data.name,
      webViewLink: file.data.webViewLink,
      webContentLink: file.data.webContentLink,
    };
  }

  /**
   * Update existing file (for auto-save)
   * @param {string} fileId - Google Drive file ID
   * @param {string} content - New content
   * @returns {Promise<Object>} Updated file info
   */
  async updateFile(fileId, content) {
    const drive = google.drive({ version: 'v3', auth: this.oauth2Client });

    const media = {
      mimeType: 'text/plain',
      body: content,
    };

    await drive.files.update({
      fileId: fileId,
      media: media,
    });

    const file = await drive.files.get({
      fileId: fileId,
      fields: 'id, name, webViewLink',
    });

    return {
      fileId: file.data.id,
      fileName: file.data.name,
      webViewLink: file.data.webViewLink,
    };
  }

  /**
   * Delete a file
   * @param {string} fileId - Google Drive file ID
   */
  async deleteFile(fileId) {
    const drive = google.drive({ version: 'v3', auth: this.oauth2Client });
    await drive.files.delete({ fileId });
  }

  /**
   * Find or create folder structure
   * @param {string} folderPath - Path like 'Clinic/Transcripts'
   * @returns {Promise<string>} Folder ID
   */
  async findOrCreateFolder(folderPath) {
    const drive = google.drive({ version: 'v3', auth: this.oauth2Client });
    const parts = folderPath.split('/').filter(p => p);

    let parentId = 'root';

    for (const folderName of parts) {
      // Check if folder exists
      const response = await drive.files.list({
        q: `name='${folderName}' and mimeType='application/vnd.google-apps.folder' and '${parentId}' in parents and trashed=false`,
        fields: 'files(id, name)',
        spaces: 'drive',
      });

      if (response.data.files.length > 0) {
        parentId = response.data.files[0].id;
      } else {
        // Create folder
        const folderMetadata = {
          name: folderName,
          mimeType: 'application/vnd.google-apps.folder',
          parents: parentId !== 'root' ? [parentId] : undefined,
        };

        const folder = await drive.files.create({
          requestBody: folderMetadata,
          fields: 'id',
        });

        parentId = folder.data.id;
      }
    }

    return parentId;
  }

  /**
   * List temp files older than retention period
   * @param {string} folderPath - Folder to search
   * @param {number} retentionHours - Hours to retain
   * @returns {Promise<Array>} List of file IDs to delete
   */
  async findOldTempFiles(folderPath, retentionHours = 24) {
    const drive = google.drive({ version: 'v3', auth: this.oauth2Client });
    const folderId = await this.findOrCreateFolder(folderPath);

    const cutoffTime = new Date();
    cutoffTime.setHours(cutoffTime.getHours() - retentionHours);

    const response = await drive.files.list({
      q: `'${folderId}' in parents and name contains '.temp_' and trashed=false`,
      fields: 'files(id, name, createdTime)',
    });

    const oldFiles = response.data.files.filter(file => {
      const createdTime = new Date(file.createdTime);
      return createdTime < cutoffTime;
    });

    return oldFiles.map(file => file.id);
  }

  /**
   * Clean up old temp files
   * @param {string} folderPath - Folder to clean
   * @param {number} retentionHours - Hours to retain
   * @returns {Promise<number>} Number of files deleted
   */
  async cleanupTempFiles(folderPath, retentionHours = 24) {
    const fileIds = await this.findOldTempFiles(folderPath, retentionHours);
    
    for (const fileId of fileIds) {
      await this.deleteFile(fileId);
    }

    return fileIds.length;
  }
}




