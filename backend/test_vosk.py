# backend/test_vosk.py
import vosk
import json
import wave
import sys

def test_vosk_model():
    # Chemin vers le modèle
    MODEL_PATH = "models/fr"
    
    print(f"🔍 Test du modèle Vosk dans: {MODEL_PATH}")
    
    try:
        # Charger le modèle
        model = vosk.Model(MODEL_PATH)
        print("✅ Modèle Vosk chargé avec succès")
        
        # Créer un recognizer
        sample_rate = 16000
        recognizer = vosk.KaldiRecognizer(model, sample_rate)
        recognizer.SetWords(True)
        
        print("🔊 Test avec un fichier WAV...")
        
        # Créer un fichier WAV de test (silence)
        import tempfile
        import os
        
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            with wave.open(f.name, 'wb') as wav_file:
                wav_file.setnchannels(1)
                wav_file.setsampwidth(2)
                wav_file.setframerate(sample_rate)
                
                # Écrire un peu de silence
                wav_file.writeframes(b'\x00' * 32000)  # 1 seconde
                
            print(f"📁 Fichier de test créé: {f.name}")
            
            # Transcrire
            with wave.open(f.name, 'rb') as wav_file:
                print(f"🎵 Format: {wav_file.getnchannels()} canaux, {wav_file.getframerate()} Hz")
                
                while True:
                    data = wav_file.readframes(4000)
                    if len(data) == 0:
                        break
                    recognizer.AcceptWaveform(data)
                
                result = json.loads(recognizer.FinalResult())
                print(f"📝 Résultat: {result}")
                
                if result.get("text"):
                    print(f"✅ Transcription: '{result['text']}'")
                else:
                    print("ℹ️  Pas de texte transcrit (normal pour du silence)")
            
            os.unlink(f.name)
            
        return True
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

if __name__ == "__main__":
    if test_vosk_model():
        print("\n🎉 Vosk fonctionne correctement !")
        sys.exit(0)
    else:
        print("\n⚠️  Problème avec Vosk")
        sys.exit(1)