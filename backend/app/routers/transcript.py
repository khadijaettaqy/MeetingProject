from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime

from app.database import get_db
from app.models.meeting import Meeting
from app.models.transcript import Transcript
from app.models.user import User
from app.schemas.transcript import TranscriptCreate, Transcript as TranscriptSchema
from app.auth.auth_handler import get_current_user
from app.models.meeting_participant import MeetingParticipant

router = APIRouter()
def user_has_access_to_meeting(db: Session, meeting_id: int, user: User) -> bool:
    meeting = db.query(Meeting).filter(Meeting.id == meeting_id).first()
    if not meeting:
        return False

    if meeting.owner_id == user.id:
        return True

    participant = db.query(MeetingParticipant).filter(
        MeetingParticipant.meeting_id == meeting_id,
        MeetingParticipant.user_id == user.id
    ).first()

    return participant is not None

@router.post("/meetings/{meeting_id}/transcripts", response_model=TranscriptSchema)
def create_transcript(
    meeting_id: int,
    transcript: TranscriptCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Créer une transcription (owner OU participant)"""

    if not user_has_access_to_meeting(db, meeting_id, current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Vous n'avez pas accès à cette réunion"
        )

    db_transcript = Transcript(
        meeting_id=meeting_id,
        **transcript.dict()
    )

    db.add(db_transcript)
    db.commit()
    db.refresh(db_transcript)

    return db_transcript


@router.get("/meetings/{meeting_id}/transcripts", response_model=List[TranscriptSchema])
def get_meeting_transcripts(
    meeting_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Lire les transcriptions (owner OU participant)"""

    if not user_has_access_to_meeting(db, meeting_id, current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Vous n'avez pas accès à cette réunion"
        )

    transcripts = db.query(Transcript).filter(
        Transcript.meeting_id == meeting_id
    ).order_by(Transcript.start_time).all()

    return transcripts


@router.delete("/transcripts/{transcript_id}")
def delete_transcript(
    transcript_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Supprimer une transcription"""
    transcript = db.query(Transcript).filter(
        Transcript.id == transcript_id
    ).first()
    
    if not transcript:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transcript not found"
        )
    
    # Vérifier que la réunion associée appartient à l'utilisateur
    meeting = db.query(Meeting).filter(
        Meeting.id == transcript.meeting_id,
        Meeting.owner_id == current_user.id
    ).first()
    
    if not meeting:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this transcript"
        )
    
    db.delete(transcript)
    db.commit()
    
    return {"message": "Transcript deleted successfully"}