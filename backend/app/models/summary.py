from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON, Float, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base

class MeetingSummary(Base):
    __tablename__ = "meeting_summaries"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Référence
    meeting_id = Column(Integer, ForeignKey("meetings.id", ondelete="CASCADE"), nullable=False)
    
    # Contenu du résumé
    summary_text = Column(Text, nullable=False)
    
    # Métadonnées
    language = Column(String(10), default="fr")
    word_count = Column(Integer, default=0)
    duration = Column(Float)  # Durée couverte en secondes
    
    # Points clés (stockés en JSON)
    key_points = Column(JSON)
    
    # Actions/To-dos
    action_items = Column(JSON)
    
    # Statistiques
    total_speakers = Column(Integer, default=0)
    total_words = Column(Integer, default=0)
    
    # Génération automatique
    is_auto_generated = Column(Boolean, default=True)
    model_used = Column(String(50))
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relations
    meeting = relationship("Meeting", back_populates="summaries")
    
    def __repr__(self):
        return f"<MeetingSummary(id={self.id}, meeting_id={self.meeting_id})>"