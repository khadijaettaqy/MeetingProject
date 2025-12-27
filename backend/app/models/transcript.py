from sqlalchemy import Column, Integer, String, Text, DateTime, Float, ForeignKey, JSON, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base

class Transcript(Base):
    __tablename__ = "transcripts"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Référence à la réunion
    meeting_id = Column(Integer, ForeignKey("meetings.id", ondelete="CASCADE"), nullable=False)
    
    # Contenu de la transcription
    text = Column(Text, nullable=False)
    speaker = Column(String(100))  # Spécifiez une longueur
    
    # Métadonnées temporelles
    start_time = Column(Float)  # en secondes depuis le début
    end_time = Column(Float)    # en secondes depuis le début
    duration = Column(Float)    # durée en secondes
    
    # Métadonnées de confiance/qualité
    confidence = Column(Float, default=0.0)
    
    # Métadonnées supplémentaires
    language = Column(String(10), default="fr")  # Spécifiez une longueur
    is_final = Column(Boolean, default=True)
    
    # Données brutes (optionnel)
    raw_data = Column(JSON)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relations
    meeting = relationship("Meeting", back_populates="transcripts")
    
    def __repr__(self):
        return f"<Transcript(id={self.id}, meeting_id={self.meeting_id}, text='{self.text[:50]}...')>"