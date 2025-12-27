# backend/app/main.py
import os
import json
from datetime import datetime
import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth.auth_handler import get_current_user
from app.models import meeting as meeting_model
from app.models.meeting_participant import MeetingParticipant
from app.models.transcript import Transcript
from app.services.vosk_service import vosk_transcriber, get_vosk_transcriber

# Import routers
from app.routers import meeting as meeting_router
from app.routers import transcript as transcript_router

app = FastAPI(title="Meeting Transcription API")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
# Include with both /meetings and /api/meetings to be forgiving for front-ends
app.include_router(meeting_router.router, prefix="/meetings", tags=["meetings"])
app.include_router(meeting_router.router, prefix="/api/meetings", tags=["meetings"])
# Transcripts under /api to match earlier usage (/api/meetings/{id}/transcripts)
app.include_router(transcript_router.router, prefix="/api", tags=["transcripts"])

# Websocket connection storage
meeting_connections = {}  # meeting_id -> list[WebSocket]
active_sessions = {}  # session_id -> metadata (recognizer, meeting_id, ...)


async def broadcast_transcription(meeting_id: int, payload: dict):
    conns = meeting_connections.get(meeting_id, []).copy()
    for ws in conns:
        try:
            await ws.send_json(payload)
        except Exception:
            # ignore broken connections
            pass


@app.websocket("/ws/transcribe")
async def websocket_transcribe(websocket: WebSocket):
    """
    WebSocket endpoint for realtime transcription.
    Protocol (from client):
      - Send an "init" JSON message with { command: "init", meeting_id, sample_rate, user_id (opt) }
      - Then send binary PCM chunks (s16le) matching sample_rate and channels=1
    """
    await websocket.accept()
    db: Session = None
    meeting_id = None
    session_id = None
    user_id = None
    recognizer = None

    try:
        # receive init
        init_msg = await websocket.receive_text()
        try:
            init = json.loads(init_msg)
        except Exception:
            await websocket.send_json({"type": "error", "message": "Init invalide"})
            await websocket.close()
            return

        meeting_id = init.get("meeting_id")
        sample_rate = int(init.get("sample_rate", 16000))
        user_id = init.get("user_id")

        # Vérifier si la transcription est active pour cette réunion
        try:
            db = next(get_db())
            meeting = db.query(meeting_model.Meeting).filter(meeting_model.Meeting.id == meeting_id).first()
            if not meeting:
                await websocket.send_json({
                    "action": "transcription_inactive",
                    "type": "status",
                    "message": "Réunion non trouvée",
                    "meeting_id": meeting_id,
                    "requires_microphone": False,
                    "timestamp": datetime.utcnow().isoformat()
                })
                return

            if not meeting.transcription_active:
                # Inform client: don't send audio, wait for owner to start transcription
                await websocket.send_json({
                    "action": "transcription_inactive",
                    "type": "status",
                    "message": "En attente du démarrage de la transcription par l'organisateur",
                    "meeting_id": meeting_id,
                    "requires_microphone": False,
                    "timestamp": datetime.utcnow().isoformat()
                })
                # keep socket open so client can get notification when transcription starts
                meeting_connections.setdefault(meeting_id, []).append(websocket)
                # Wait for messages but ignore binary until transcription starts
                while True:
                    msg = await websocket.receive()
                    if msg is None:
                        break
                    if msg.get("type") == "websocket.disconnect":
                        break
                return

            # If transcription is active: initialize recognizer
            try:
                vt = get_vosk_transcriber()
                recognizer = vt.create_recognizer(sample_rate)
            except Exception as e:
                await websocket.send_json({"type": "error", "message": f"Vosk non disponible: {str(e)}"})
                return

            # Register connection
            meeting_connections.setdefault(meeting_id, []).append(websocket)

            # Prepare session id
            session_id = f"{meeting_id}_{user_id or 'anonymous'}_{int(datetime.utcnow().timestamp()*1000)}"
            active_sessions[session_id] = {
                "recognizer": recognizer,
                "meeting_id": meeting_id,
                "user_id": user_id,
                "ws": websocket,
                "start_time": datetime.utcnow()
            }

            await websocket.send_json({
                "type": "status",
                "status": "ready",
                "message": "Vosk prêt",
                "session_id": session_id
            })

            # Loop to receive binary audio chunks
            while True:
                msg = await websocket.receive()
                if msg["type"] == "websocket.disconnect":
                    break
                if msg["type"] == "websocket.receive":
                    # binary payload (websocket.receive returns bytes in 'bytes' field when binary)
                    if "bytes" in msg:
                        audio_data = msg["bytes"]
                    elif "text" in msg:
                        # client may send control messages
                        try:
                            ctrl = json.loads(msg["text"])
                            # ignore or handle control messages
                            continue
                        except Exception:
                            continue
                    else:
                        continue

                    if not recognizer:
                        await websocket.send_json({"type": "error", "message": "Reconnaisseur non initialisé"})
                        continue

                    try:
                        if recognizer.AcceptWaveform(audio_data):
                            result = json.loads(recognizer.Result())
                            text = result.get("text", "")
                            payload = {
                                "type": "transcription",
                                "text": text,
                                "final": True,
                                "timestamp": datetime.utcnow().isoformat(),
                                "user_id": user_id,
                                "meeting_id": meeting_id,
                                "words": result.get("result", [])
                            }
                            await broadcast_transcription(meeting_id, payload)
                        else:
                            partial_result = json.loads(recognizer.PartialResult())
                            partial_text = partial_result.get("partial", "")
                            if partial_text:
                                payload = {
                                    "type": "transcription",
                                    "text": partial_text,
                                    "final": False,
                                    "timestamp": datetime.utcnow().isoformat(),
                                    "user_id": user_id,
                                    "meeting_id": meeting_id,
                                    "is_partial": True
                                }
                                await broadcast_transcription(meeting_id, payload)
                    except Exception as e:
                        await websocket.send_json({"type": "error", "message": f"Erreur transcription: {str(e)}"})
                        # continue processing further chunks

        except WebSocketDisconnect:
            pass
    except Exception as e:
        print(f"❌ Erreur WebSocket: {e}")
    finally:
        # Cleanup
        if meeting_id is not None and websocket in meeting_connections.get(meeting_id, []):
            try:
                meeting_connections[meeting_id].remove(websocket)
                if not meeting_connections[meeting_id]:
                    del meeting_connections[meeting_id]
            except Exception:
                pass

        if session_id and session_id in active_sessions:
            try:
                del active_sessions[session_id]
            except Exception:
                pass

        try:
            if db is not None:
                db.close()
        except Exception:
            pass


# ----------------- Test Vosk -----------------
@app.post("/api/transcribe/test")
async def transcribe_test():
    # Use get_vosk_transcriber to check model presence
    try:
        vt = get_vosk_transcriber()
    except Exception as e:
        return {"error": f"Modèle Vosk non chargé: {str(e)}"}

    try:
        import wave, tempfile, os
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            with wave.open(f.name, 'wb') as wav_file:
                wav_file.setnchannels(1)
                wav_file.setsampwidth(2)
                wav_file.setframerate(16000)
                wav_file.writeframes(b'\x00' * 32000)
            recognizer = vt.create_recognizer(16000)
            with wave.open(f.name, 'rb') as wav_file:
                while True:
                    data = wav_file.readframes(4000)
                    if len(data) == 0: break
                    recognizer.AcceptWaveform(data)
                result = json.loads(recognizer.FinalResult())
                text = result.get("text", "Aucune transcription")
            os.unlink(f.name)
            return {"success": True, "text": text, "confidence": result.get("confidence", 0), "test": "Fichier de silence transcrit"}
    except Exception as e:
        return {"error": f"Erreur test: {str(e)}"}


# ----------------- Root -----------------
@app.get("/")
def read_root():
    status = "Vosk chargé" if vosk_transcriber else "Vosk non chargé"
    return {
        "message": "Meeting Transcription API",
        "status": status,
        "endpoints": {
            "websocket": "/ws/transcribe",
            "test_vosk": "/api/transcribe/test",
            "check_transcription_permission": "/api/meetings/{meeting_id}/check-transcription-permission"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))