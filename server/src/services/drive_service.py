"""
Google Drive service for saving transcripts.
"""
import os
from typing import Optional, List
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from ..config import config


class DriveService:
    """Google Drive service for saving transcripts."""
    
    def __init__(self):
        """Initialize Drive service."""
        self.client_id = config.drive.client_id
        self.client_secret = config.drive.client_secret
        self.redirect_uri = config.drive.redirect_uri
        self.oauth2_client = None
        self.drive_service = None
        self._last_refreshed_tokens = None
    
    def get_auth_url(self) -> str:
        """
        Get OAuth URL for user authorization.
        
        Returns:
            Authorization URL
        """
        flow = Flow.from_client_config(
            {
                'web': {
                    'client_id': self.client_id,
                    'client_secret': self.client_secret,
                    'auth_uri': 'https://accounts.google.com/o/oauth2/auth',
                    'token_uri': 'https://oauth2.googleapis.com/token',
                    'redirect_uris': [self.redirect_uri],
                }
            },
            scopes=['https://www.googleapis.com/auth/drive.file'],
        )
        flow.redirect_uri = self.redirect_uri
        
        auth_url, _ = flow.authorization_url(
            access_type='offline',
            prompt='consent',  # Force consent to get refresh token
        )
        
        return auth_url
    
    async def get_tokens(self, code: str) -> dict:
        """
        Exchange authorization code for tokens.
        
        Args:
            code: Authorization code
        
        Returns:
            Dictionary with tokens
        """
        flow = Flow.from_client_config(
            {
                'web': {
                    'client_id': self.client_id,
                    'client_secret': self.client_secret,
                    'auth_uri': 'https://accounts.google.com/o/oauth2/auth',
                    'token_uri': 'https://oauth2.googleapis.com/token',
                    'redirect_uris': [self.redirect_uri],
                }
            },
            scopes=['https://www.googleapis.com/auth/drive.file'],
        )
        flow.redirect_uri = self.redirect_uri
        
        flow.fetch_token(code=code)
        credentials = flow.credentials
        
        return {
            'access_token': credentials.token,
            'refresh_token': credentials.refresh_token,
            'token_uri': credentials.token_uri,
            'client_id': credentials.client_id,
            'client_secret': credentials.client_secret,
            'scopes': credentials.scopes,
        }
    
    def set_user_tokens(self, tokens: dict):
        """
        Set user's access token.

        Args:
            tokens: Access and refresh tokens dictionary
        """
        credentials = Credentials(
            token=tokens.get('access_token'),
            refresh_token=tokens.get('refresh_token'),
            token_uri=tokens.get('token_uri', 'https://oauth2.googleapis.com/token'),
            client_id=tokens.get('client_id') or self.client_id,
            client_secret=tokens.get('client_secret') or self.client_secret,
            scopes=tokens.get('scopes', ['https://www.googleapis.com/auth/drive.file']),
        )

        self.oauth2_client = credentials
        self.drive_service = build('drive', 'v3', credentials=credentials)

    def _refresh_token_if_needed(self):
        """
        Refresh access token if expired.
        Returns updated tokens if refreshed, None otherwise.
        """
        if self.oauth2_client and self.oauth2_client.expired and self.oauth2_client.refresh_token:
            print('[DRIVE] Access token expired, refreshing...')
            try:
                from google.auth.transport.requests import Request
                self.oauth2_client.refresh(Request())
                print('[DRIVE] Token refreshed successfully')

                # Rebuild drive service with refreshed credentials
                self.drive_service = build('drive', 'v3', credentials=self.oauth2_client)
                print('[DRIVE] Drive service rebuilt with refreshed credentials')

                # Return new tokens
                return {
                    'access_token': self.oauth2_client.token,
                    'refresh_token': self.oauth2_client.refresh_token,
                }
            except Exception as e:
                print(f'[DRIVE] Failed to refresh token: {e}')
                raise
        return None

    def get_and_clear_refreshed_tokens(self):
        """
        Get and clear the last refreshed tokens (from retry logic).
        Returns None if no tokens were refreshed since last call.
        """
        tokens = self._last_refreshed_tokens
        self._last_refreshed_tokens = None
        return tokens
    
    async def save_transcript(
        self,
        content: str,
        file_name: str,
        folder_path: str = 'Clinic/Transcripts',
        as_google_doc: bool = True
    ) -> dict:
        """
        Save transcript to Google Drive.

        Args:
            content: Transcript content
            file_name: File name (with or without .txt extension)
            folder_path: Folder path (e.g., 'Clinic/Transcripts')
            as_google_doc: If True, saves as Google Doc; if False, saves as .txt

        Returns:
            File info with webViewLink
        """
        if not self.drive_service:
            raise ValueError("User tokens not set. Call set_user_tokens() first.")

        from io import BytesIO
        from googleapiclient.http import MediaIoBaseUpload
        from googleapiclient.errors import HttpError

        # Try operation, refresh token if needed, and retry once
        max_retries = 1
        for attempt in range(max_retries + 1):
            try:
                # Find or create folder
                folder_id = await self.find_or_create_folder(folder_path)

                # Create file metadata and media based on format
                if as_google_doc:
                    # Save as Google Doc (opens in Google Docs editor)
                    file_metadata = {
                        'name': file_name.replace('.txt', ''),  # Remove .txt extension for Google Docs
                        'parents': [folder_id],
                        'mimeType': 'application/vnd.google-apps.document'  # Google Docs format
                    }
                    # Upload plain text, Google auto-converts to Doc format
                    media = MediaIoBaseUpload(
                        BytesIO(content.encode('utf-8')),
                        mimetype='text/plain',
                        resumable=True
                    )
                else:
                    # Save as plain text file
                    file_metadata = {
                        'name': file_name,
                        'parents': [folder_id],
                    }
                    media = MediaIoBaseUpload(
                        BytesIO(content.encode('utf-8')),
                        mimetype='text/plain',
                        resumable=True
                    )

                file = self.drive_service.files().create(
                    body=file_metadata,
                    media_body=media,
                    fields='id, name, webViewLink, webContentLink'
                ).execute()

                return {
                    'file_id': file.get('id'),
                    'file_name': file.get('name'),
                    'web_view_link': file.get('webViewLink'),
                    'web_content_link': file.get('webContentLink'),
                }

            except HttpError as e:
                if e.resp.status == 401 and attempt < max_retries:
                    # Unauthorized - try refreshing token
                    print(f'[DRIVE] Got 401 error, attempting token refresh (attempt {attempt + 1}/{max_retries + 1})')
                    try:
                        from google.auth.transport.requests import Request
                        self.oauth2_client.refresh(Request())
                        self.drive_service = build('drive', 'v3', credentials=self.oauth2_client)
                        print('[DRIVE] Token refreshed successfully, retrying operation...')

                        # Store refreshed tokens to return to caller
                        self._last_refreshed_tokens = {
                            'access_token': self.oauth2_client.token,
                            'refresh_token': self.oauth2_client.refresh_token,
                        }
                        continue
                    except Exception as refresh_error:
                        print(f'[DRIVE] Token refresh failed: {refresh_error}')
                        # If refresh fails, user needs to re-authenticate
                        raise ValueError(f"OAuth tokens expired. Please log in again. Error: {refresh_error}")
                else:
                    # Other error or max retries reached
                    raise
    
    async def update_file(self, file_id: str, content: str) -> dict:
        """
        Update existing file (for auto-save).

        Args:
            file_id: Google Drive file ID
            content: New content

        Returns:
            Updated file info
        """
        if not self.drive_service:
            raise ValueError("User tokens not set. Call set_user_tokens() first.")

        from io import BytesIO
        from googleapiclient.http import MediaIoBaseUpload
        from googleapiclient.errors import HttpError

        # Try operation, refresh token if needed, and retry once
        max_retries = 1
        for attempt in range(max_retries + 1):
            try:
                media = MediaIoBaseUpload(
                    BytesIO(content.encode('utf-8')),
                    mimetype='text/plain',
                    resumable=True
                )

                self.drive_service.files().update(
                    fileId=file_id,
                    media_body=media
                ).execute()

                file = self.drive_service.files().get(
                    fileId=file_id,
                    fields='id, name, webViewLink'
                ).execute()

                return {
                    'file_id': file.get('id'),
                    'file_name': file.get('name'),
                    'web_view_link': file.get('webViewLink'),
                }

            except HttpError as e:
                if e.resp.status == 401 and attempt < max_retries:
                    # Unauthorized - try refreshing token
                    print(f'[DRIVE] Got 401 error during update, attempting token refresh (attempt {attempt + 1}/{max_retries + 1})')
                    try:
                        from google.auth.transport.requests import Request
                        self.oauth2_client.refresh(Request())
                        self.drive_service = build('drive', 'v3', credentials=self.oauth2_client)
                        print('[DRIVE] Token refreshed successfully, retrying operation...')

                        # Store refreshed tokens to return to caller
                        self._last_refreshed_tokens = {
                            'access_token': self.oauth2_client.token,
                            'refresh_token': self.oauth2_client.refresh_token,
                        }
                        continue
                    except Exception as refresh_error:
                        print(f'[DRIVE] Token refresh failed: {refresh_error}')
                        # If refresh fails, user needs to re-authenticate
                        raise ValueError(f"OAuth tokens expired. Please log in again. Error: {refresh_error}")
                else:
                    # Other error or max retries reached
                    raise
    
    async def delete_file(self, file_id: str):
        """
        Delete a file.
        
        Args:
            file_id: Google Drive file ID
        """
        if not self.drive_service:
            raise ValueError("User tokens not set. Call set_user_tokens() first.")
        
        self.drive_service.files().delete(fileId=file_id).execute()
    
    async def find_or_create_folder(self, folder_path: str) -> str:
        """
        Find or create folder structure.
        
        Args:
            folder_path: Path like 'Clinic/Transcripts'
        
        Returns:
            Folder ID
        """
        if not self.drive_service:
            raise ValueError("User tokens not set. Call set_user_tokens() first.")
        
        parts = [p for p in folder_path.split('/') if p]
        parent_id = 'root'
        
        for folder_name in parts:
            # Check if folder exists
            query = (
                f"name='{folder_name}' and "
                f"mimeType='application/vnd.google-apps.folder' and "
                f"'{parent_id}' in parents and "
                f"trashed=false"
            )
            
            results = self.drive_service.files().list(
                q=query,
                fields='files(id, name)',
                spaces='drive'
            ).execute()
            
            files = results.get('files', [])
            
            if files:
                parent_id = files[0]['id']
            else:
                # Create folder
                folder_metadata = {
                    'name': folder_name,
                    'mimeType': 'application/vnd.google-apps.folder',
                }
                if parent_id != 'root':
                    folder_metadata['parents'] = [parent_id]
                
                folder = self.drive_service.files().create(
                    body=folder_metadata,
                    fields='id'
                ).execute()
                
                parent_id = folder.get('id')
        
        return parent_id
    
    async def find_old_temp_files(
        self,
        folder_path: str,
        retention_hours: int = 24
    ) -> List[str]:
        """
        List temp files older than retention period.
        
        Args:
            folder_path: Folder to search
            retention_hours: Hours to retain
        
        Returns:
            List of file IDs to delete
        """
        if not self.drive_service:
            raise ValueError("User tokens not set. Call set_user_tokens() first.")
        
        from datetime import datetime, timedelta
        
        folder_id = await self.find_or_create_folder(folder_path)
        cutoff_time = datetime.utcnow() - timedelta(hours=retention_hours)
        
        query = (
            f"'{folder_id}' in parents and "
            f"name contains '.temp_' and "
            f"trashed=false"
        )
        
        results = self.drive_service.files().list(
            q=query,
            fields='files(id, name, createdTime)'
        ).execute()
        
        files = results.get('files', [])
        old_files = []
        
        for file in files:
            created_time = datetime.fromisoformat(
                file['createdTime'].replace('Z', '+00:00')
            )
            if created_time < cutoff_time:
                old_files.append(file['id'])
        
        return old_files
    
    async def cleanup_temp_files(
        self,
        folder_path: str,
        retention_hours: int = 24
    ) -> int:
        """
        Clean up old temp files.
        
        Args:
            folder_path: Folder to clean
            retention_hours: Hours to retain
        
        Returns:
            Number of files deleted
        """
        file_ids = await self.find_old_temp_files(folder_path, retention_hours)
        
        for file_id in file_ids:
            await self.delete_file(file_id)
        
        return len(file_ids)




