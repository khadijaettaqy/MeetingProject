from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base
import enum

class MeetingStatus(str, enum.Enum):
    """Statuts possibles d'une réunion"""
    SCHEDULED = "scheduled"
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class Meeting(Base):
    __tablename__ = "meetings"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)  # Spécifiez une longueur
    description = Column(Text)
    
    # Dates et heures
    scheduled_start = Column(DateTime(timezone=True))
    scheduled_end = Column(DateTime(timezone=True))
    actual_start = Column(DateTime(timezone=True))
    actual_end = Column(DateTime(timezone=True))
    
    # Statut et métadonnées
    status = Column(Enum(MeetingStatus), default=MeetingStatus.SCHEDULED)
    is_private = Column(Boolean, default=False)
    allow_transcriptions = Column(Boolean, default=True)
    language = Column(String(10), default="fr")  # Spécifiez une longueur
    transcription_active = Column(Boolean, default=False)

    # Audio/Video settings
    record_audio = Column(Boolean, default=True)
    record_video = Column(Boolean, default=False)
    max_participants = Column(Integer, default=10)
    
    # Propriétaire
    owner_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relations
    owner = relationship("User", back_populates="meetings")
    transcripts = relationship("Transcript", back_populates="meeting", cascade="all, delete-orphan")
    participants = relationship(
        "MeetingParticipant",
        back_populates="meeting",
        cascade="all, delete-orphan"
    )
    
    summaries = relationship(
        "MeetingSummary", 
        back_populates="meeting", 
        cascade="all, delete-orphan"
    )
    
    def __repr__(self):
        return f"<Meeting(id={self.id}, title='{self.title}', status='{self.status}')>"