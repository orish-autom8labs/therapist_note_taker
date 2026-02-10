"""Firestore service for session metadata and job tracking."""

import os
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List

from cryptography.fernet import Fernet
from google.cloud.firestore_v1 import AsyncClient
from google.cloud.firestore_v1.base_query import FieldFilter

from src.config import config


class FirestoreService:
    """
    Async Firestore client for session metadata.

    Privacy rules:
    - NO transcript text stored
    - NO audio data
    - Drive file IDs are pointers, not content
    - Refresh tokens encrypted with Fernet (AES-128)
    """

    def __init__(self) -> None:
        project_id = config.firestore.project_id
        self._db = AsyncClient(project=project_id)
        self._prefix = config.firestore.collection_prefix
        self._fernet: Optional[Fernet] = None

        encryption_key = config.firestore.encryption_key
        if encryption_key:
            self._fernet = Fernet(encryption_key.encode())

    @property
    def _collection(self) -> str:
        return f"{self._prefix}_sessions"

    # ─── CRUD ────────────────────────────────────────────────────────────

    async def create_session(
        self,
        session_id: str,
        user_email: str,
        patient_name: str,
        transcript_info: Dict[str, Any],
        refresh_token: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Create a session document after transcript is saved to Drive.

        Args:
            session_id: Unique session identifier
            user_email: Therapist email (for querying)
            patient_name: Patient name
            transcript_info: Drive file info (file_id, file_name, web_view_link)
            refresh_token: OAuth refresh token (will be encrypted)
            metadata: Additional metadata (duration, token_count, language)
        """
        doc = {
            "user_email": user_email,
            "patient_name": patient_name,
            "created_at": datetime.now(timezone.utc),
            "status": "transcript_saved",
            "transcript": {
                "drive_file_id": transcript_info.get("file_id", ""),
                "drive_file_name": transcript_info.get("file_name", ""),
                "web_view_link": transcript_info.get("web_view_link", ""),
            },
            "summaries": {},
            "summarization": {
                "attempts": 0,
                "last_attempt_at": None,
                "last_error": None,
                "total_cost_usd": 0.0,
            },
            "metadata": metadata or {},
        }

        if refresh_token and self._fernet:
            doc["encrypted_refresh_token"] = self._fernet.encrypt(
                refresh_token.encode()
            ).decode()

        ref = self._db.collection(self._collection).document(session_id)
        await ref.set(doc)
        return doc

    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session document by ID."""
        ref = self._db.collection(self._collection).document(session_id)
        snap = await ref.get()
        if snap.exists:
            data = snap.to_dict()
            if data:
                data["id"] = snap.id
            return data
        return None

    async def update_status(
        self,
        session_id: str,
        status: str,
        extra: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Update session status with optional extra fields."""
        ref = self._db.collection(self._collection).document(session_id)
        update: Dict[str, Any] = {"status": status}
        if extra:
            update.update(extra)
        await ref.update(update)

    async def set_summarizing(self, session_id: str) -> None:
        """Mark session as summarizing and increment attempt count."""
        ref = self._db.collection(self._collection).document(session_id)
        snap = await ref.get()
        current = snap.to_dict() or {} if snap.exists else {}
        attempts = current.get("summarization", {}).get("attempts", 0)

        await ref.update({
            "status": "summarizing",
            "summarization.attempts": attempts + 1,
            "summarization.last_attempt_at": datetime.now(timezone.utc),
            "summarization.last_error": None,
        })

    async def set_completed(
        self,
        session_id: str,
        summary_info: Dict[str, Any],
        cost_usd: float = 0.0,
    ) -> None:
        """Mark session as completed with summary info."""
        ref = self._db.collection(self._collection).document(session_id)
        await ref.update({
            "status": "completed",
            "summaries.detailed_notes": {
                "drive_file_id": summary_info.get("file_id", ""),
                "drive_file_name": summary_info.get("file_name", ""),
                "web_view_link": summary_info.get("web_view_link", ""),
                "created_at": datetime.now(timezone.utc),
            },
            "summarization.last_error": None,
            "summarization.total_cost_usd": cost_usd,
        })

    async def set_failed(self, session_id: str, error_message: str) -> None:
        """Mark session as failed with error details."""
        ref = self._db.collection(self._collection).document(session_id)
        await ref.update({
            "status": "summarization_failed",
            "summarization.last_error": error_message,
            "summarization.last_attempt_at": datetime.now(timezone.utc),
        })

    async def get_stale_jobs(
        self, max_age_minutes: int = 30
    ) -> List[Dict[str, Any]]:
        """
        Query for stuck or failed jobs (for future retry worker).

        Returns sessions where status is 'summarizing' for too long
        or 'summarization_failed'.
        """
        collection_ref = self._db.collection(self._collection)

        failed_query = collection_ref.where(
            filter=FieldFilter("status", "==", "summarization_failed")
        )
        failed_docs = await failed_query.get()

        results = []
        for doc in failed_docs:
            data = doc.to_dict()
            if data:
                data["id"] = doc.id
                results.append(data)

        return results

    def decrypt_refresh_token(self, encrypted_token: str) -> Optional[str]:
        """Decrypt a stored refresh token."""
        if not self._fernet or not encrypted_token:
            return None
        try:
            return self._fernet.decrypt(encrypted_token.encode()).decode()
        except Exception:
            return None
