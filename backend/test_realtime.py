# test_realtime.py
import asyncio
import websockets
import json
import wave
import time

async def test_realtime():
    uri = "ws://localhost:8080/ws/transcribe"
    
    async with websockets.connect(uri) as websocket:
        print("✅ Connecté au WebSocket")
        
        # Initialiser
        await websocket.send(json.dumps({
            "command": "init",
            "meeting_id": "test",
            "sample_rate": 16000
        }))
        
        # Attendre la confirmation
        response = await websocket.recv()
        print(f"📩 Réponse: {response}")
        
        # Envoyer 2 secondes d'audio (silence)
        for i in range(2):
            # 1 seconde de silence (16000 échantillons * 2 bytes = 32000 bytes)
            silent_chunk = b'\x00' * 32000
            print(f"🎵 Envoi chunk {i+1}/2...")
            await websocket.send(silent_chunk)
            
            # Attendre une réponse
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                data = json.loads(response)
                if data.get("type") == "transcription":
                    print(f"📝 Transcription: {data.get('text', '')}")
            except asyncio.TimeoutError:
                print("⏱️ Pas de réponse (normal pour du silence)")
            
            time.sleep(0.5)
        
        print("✅ Test terminé")

asyncio.run(test_realtime())