from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base
import enum
# Au début du fichier MeetingParticipant.py
from app.models.meeting import Meeting  

class ParticipantRole(str, enum.Enum):
    """Rôles des participants"""
    HOST = "host"
    CO_HOST = "co_host"
    PARTICIPANT = "participant"
    VIEWER = "viewer"

class ParticipantStatus(str, enum.Enum):
    """Statuts des participants"""
    INVITED = "invited"
    JOINED = "joined"
    LEFT = "left"
    DECLINED = "declined"

class MeetingParticipant(Base):
    __tablename__ = "meeting_participants"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Références
    meeting_id = Column(Integer, ForeignKey("meetings.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    
    # Informations du participant (si pas d'utilisateur enregistré)
    email = Column(String(255))
    display_name = Column(String(255))
    
    # Statut et rôle
    role = Column(Enum(ParticipantRole), default=ParticipantRole.PARTICIPANT)
    status = Column(Enum(ParticipantStatus), default=ParticipantStatus.INVITED)
    
    # Données de session
    join_time = Column(DateTime(timezone=True))
    leave_time = Column(DateTime(timezone=True))
    duration = Column(Integer, default=0)  # en secondes
    
    # Permissions
    can_speak = Column(Boolean, default=True)
    can_transcribe = Column(Boolean, default=True)
    can_invite = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relations
    meeting = relationship("Meeting", back_populates="participants") 

    user = relationship("User")
    
    def __repr__(self):
        return f"<MeetingParticipant(id={self.id}, meeting_id={self.meeting_id}, email='{self.email}')>"