from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base

class AudioRecording(Base):
    __tablename__ = "audio_recordings"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Référence
    meeting_id = Column(Integer, ForeignKey("meetings.id", ondelete="CASCADE"), nullable=False)
    
    # Informations sur le fichier
    file_path = Column(String(500))
    file_name = Column(String(200))
    file_size = Column(Integer)  # en bytes
    duration = Column(Float)     # en secondes
    
    # Métadonnées audio
    sample_rate = Column(Integer, default=16000)
    channels = Column(Integer, default=1)
    format = Column(String(10), default="wav")
    
    # Statut
    is_processed = Column(Boolean, default=False)
    processing_status = Column(String(20), default="pending")
    
    # Transcription associée
    transcript_id = Column(Integer, ForeignKey("transcripts.id"))
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    processed_at = Column(DateTime(timezone=True))
    
    # Relations
    meeting = relationship("Meeting")
    transcript = relationship("Transcript")
    
    def __repr__(self):
        return f"<AudioRecording(id={self.id}, meeting_id={self.meeting_id}, file_name='{self.file_name}')>"
    