from pydantic import BaseModel, Field, EmailStr
from datetime import datetime
from typing import Optional
from enum import Enum
from app.models.meeting_participant import ParticipantRole

# ---------------- Statuts de réunion ----------------
class MeetingStatus(str, Enum):
    SCHEDULED = "scheduled"
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

# ---------------- Base Meeting ----------------
class MeetingBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    scheduled_start: Optional[datetime] = None
    scheduled_end: Optional[datetime] = None
    is_private: bool = False
    allow_transcriptions: bool = True
    language: str = "fr"
    record_audio: bool = True
    record_video: bool = False
    max_participants: int = 10

# ---------------- Création & Mise à jour ----------------
class MeetingCreate(MeetingBase):
    pass

class MeetingUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    status: Optional[MeetingStatus] = None
    is_private: Optional[bool] = None
    scheduled_start: Optional[datetime] = None
    scheduled_end: Optional[datetime] = None
    allow_transcriptions: Optional[bool] = None
    language: Optional[str] = None
    record_audio: Optional[bool] = None
    record_video: Optional[bool] = None
    max_participants: Optional[int] = None

# ---------------- Lecture / Réponse ----------------
class Meeting(MeetingBase):
    id: int
    owner_id: int
    status: MeetingStatus
    actual_start: Optional[datetime] = None
    actual_end: Optional[datetime] = None
    transcription_active: bool = False  # Nouveau champ pour la transcription en cours
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# ---------------- Ajouter un membre ----------------
class AddMemberRequest(BaseModel):
    member_email: EmailStr
    display_name: Optional[str] = None
    role: Optional[ParticipantRole] = ParticipantRole.PARTICIPANT
