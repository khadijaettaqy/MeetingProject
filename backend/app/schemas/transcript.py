from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Dict, Any

class TranscriptBase(BaseModel):
    text: str
    speaker: Optional[str] = None
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    confidence: Optional[float] = None
    language: str = "fr"
    is_final: bool = True

class TranscriptCreate(TranscriptBase):
    meeting_id: int

class TranscriptUpdate(BaseModel):
    text: Optional[str] = None
    speaker: Optional[str] = None
    is_final: Optional[bool] = None

class Transcript(TranscriptBase):
    id: int
    meeting_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True