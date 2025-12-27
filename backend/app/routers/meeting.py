from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime

from app.database import get_db
from app.models.meeting import Meeting, MeetingStatus
from app.models.transcript import Transcript
from app.models.user import User
from app.schemas.transcript import TranscriptCreate, Transcript as TranscriptSchema
from app.auth.auth_handler import get_current_user
from app.models.meeting_participant import MeetingParticipant, ParticipantRole

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


@router.post("/", response_model=dict)
def create_meeting(meeting: dict, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # Simple placeholder: adapte selon votre schema MeetingCreate
    db_meeting = Meeting(
        title=meeting.get("title", "Untitled"),
        description=meeting.get("description"),
        owner_id=current_user.id,
        scheduled_start=meeting.get("scheduled_start"),
        scheduled_end=meeting.get("scheduled_end"),
        allow_transcriptions=meeting.get("allow_transcriptions", True)
    )
    db.add(db_meeting)
    db.commit()
    db.refresh(db_meeting)
    return {"message": "Meeting created", "meeting": db_meeting}


@router.get("/", response_model=List[dict])
def list_meetings(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    meetings = db.query(Meeting).filter(
        (Meeting.owner_id == current_user.id)  # vous pouvez adapter la visibilité
    ).all()
    return meetings


# ---------------- Démarrer/Terminer ----------------
@router.post("/{meeting_id}/start")
def start_meeting(
    meeting_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    meeting = db.query(Meeting).filter(
        Meeting.id == meeting_id,
        Meeting.owner_id == current_user.id
    ).first()
    if not meeting:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Meeting not found")

    meeting.status = MeetingStatus.ACTIVE
    meeting.actual_start = datetime.utcnow()
    meeting.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(meeting)
    return {"message": "Meeting started", "meeting": meeting}


@router.post("/{meeting_id}/end")
def end_meeting(
    meeting_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    meeting = db.query(Meeting).filter(
        Meeting.id == meeting_id,
        Meeting.owner_id == current_user.id
    ).first()
    if not meeting:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Meeting not found")

    meeting.status = MeetingStatus.COMPLETED
    meeting.actual_end = datetime.utcnow()
    meeting.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(meeting)
    return {"message": "Meeting ended", "meeting": meeting}


# ---------------- Ajouter un membre ----------------
class AddMemberRequest(dict):
    pass


@router.post("/{meeting_id}/addMember")
def add_member(
    meeting_id: int,
    data: AddMemberRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    meeting = db.query(Meeting).filter(
        Meeting.id == meeting_id,
        Meeting.owner_id == current_user.id
    ).first()

    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")

    user = db.query(User).filter(User.email == data.member_email).first()

    participant = MeetingParticipant(
        meeting_id=meeting.id,
        user_id=user.id if user else None,
        email=data.member_email,
        display_name=data.display_name or (user.full_name if user else None),
        role=data.role,
        status="invited"
    )

    db.add(participant)
    db.commit()
    db.refresh(participant)

    return {
        "message": f"{data.member_email} ajouté à la réunion",
        "participant": {
            "id": participant.id,
            "email": participant.email,
            "display_name": participant.display_name,
            "role": participant.role,
            "status": participant.status
        }
    }


# ---------------- Vérification permission transcription ----------------
@router.get("/{meeting_id}/check-transcription-permission")
def check_transcription_permission(
    meeting_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    meeting = db.query(Meeting).filter(Meeting.id == meeting_id).first()
    if not meeting:
        raise HTTPException(status_code=404, detail="Réunion non trouvée")

    # Autoriser si propriétaire OU si la réunion autorise les transcriptions ET
    # le participant est présent avec can_transcribe True.
    if meeting.owner_id == current_user.id:
        can_start = True
    else:
        participant = db.query(MeetingParticipant).filter(
            MeetingParticipant.meeting_id == meeting_id,
            MeetingParticipant.user_id == current_user.id,
            MeetingParticipant.can_transcribe == True
        ).first()
        can_start = (participant is not None) and meeting.allow_transcriptions
    return {
        "can_start_transcription": can_start,
        "user_id": current_user.id,
        "meeting_id": meeting_id,
        "meeting_owner_id": meeting.owner_id,
        "is_owner": (meeting.owner_id == current_user.id),
        "message": "Vous pouvez démarrer la transcription" if can_start else "Seul le propriétaire ou un participant autorisé peut démarrer la transcription"
   }