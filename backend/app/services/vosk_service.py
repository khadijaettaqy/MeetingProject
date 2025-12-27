# app/services/vosk_service.py
import vosk
import json
import wave
import logging
import os
from typing import Optional

logger = logging.getLogger(__name__)


class VoskTranscriber:
    def __init__(self, model_path: Optional[str] = None):
        """
        Initialise le transcribeur Vosk avec un modèle.
        Si model_path est None, on cherche dans une liste de chemins possibles.
        Lève FileNotFoundError si aucun modèle trouvé.
        """
        # Déterminez le chemin du modèle
        if model_path is None:
            # Essayez plusieurs chemins possibles
            possible_paths = [
                "models/vosk-model-small-fr-0.22",
                "models/fr",
                "vosk-model-small-fr-0.22",
                "vosk-model-fr-0.22",
                "models"  # fallback vers dossier models
            ]

            for path in possible_paths:
                if os.path.exists(path):
                    model_path = path
                    break

            if model_path is None:
                raise FileNotFoundError(
                    "Aucun modèle Vosk trouvé. Téléchargez un modèle depuis https://alphacephei.com/vosk/models "
                    "ou définissez VOSK_MODEL_PATH."
                )

        logger.info(f"📦 Chargement du modèle Vosk depuis: {model_path}")
        # Initialisation du modèle (peut lever si binaire incompatible)
        self.model = vosk.Model(model_path)
        logger.info("✅ Modèle Vosk chargé avec succès")

    def create_recognizer(self, sample_rate: int = 16000):
        """
        Créer un nouveau recognizer pour une session.
        On protège les appels SetWords / SetPartialWords au cas où la version de vosk ne les expose pas.
        """
        recognizer = vosk.KaldiRecognizer(self.model, sample_rate)
        try:
            # Certaines versions de vosk exposent ces méthodes
            recognizer.SetWords(True)
        except Exception:
            logger.debug("SetWords non disponible pour cette version de vosk", exc_info=True)
        try:
            recognizer.SetPartialWords(True)
        except Exception:
            logger.debug("SetPartialWords non disponible pour cette version de vosk", exc_info=True)
        return recognizer

    def transcribe_wav_file(self, file_path: str) -> dict:
        """
        Transcrire un fichier WAV complet (lecture avec wave).
        Retourne un dict avec text, words, confidence.
        """
        try:
            wf = wave.open(file_path, "rb")
            rec = self.create_recognizer(wf.getframerate())

            full_text = []
            words = []

            while True:
                data = wf.readframes(4000)
                if len(data) == 0:
                    break
                if rec.AcceptWaveform(data):
                    result = json.loads(rec.Result())
                    text = result.get("text", "")
                    if text:
                        full_text.append(text)
                        words.extend(result.get("result", []))

            final_result = json.loads(rec.FinalResult())
            final_text = final_result.get("text", "")
            if final_text:
                full_text.append(final_text)
                words.extend(final_result.get("result", []))

            wf.close()

            return {
                "text": " ".join(full_text).strip(),
                "words": words,
                "confidence": final_result.get("confidence", 0)
            }

        except Exception as e:
            logger.error(f"Erreur transcription fichier: {e}", exc_info=True)
            raise

    def process_audio_chunk(self, recognizer: vosk.KaldiRecognizer, audio_data: bytes):
        """
        Traiter un chunk audio et retourner le résultat
        Retourne: (texte, is_final, result_json)
        """
        try:
            if recognizer.AcceptWaveform(audio_data):
                result = json.loads(recognizer.Result())
                return result.get("text", ""), True, result
            else:
                result = json.loads(recognizer.PartialResult())
                return result.get("partial", ""), False, result
        except Exception as e:
            logger.error(f"Erreur lors du traitement du chunk audio: {e}", exc_info=True)
            raise


# --- Instantiation robuste au démarrage ---
# On permet de fournir le chemin via la variable d'environnement VOSK_MODEL_PATH
# pour les environnements (Docker, CI, VPS).
model_path_env = os.environ.get("VOSK_MODEL_PATH", None)
try:
    vosk_transcriber = VoskTranscriber(model_path=model_path_env)
except Exception as e:
    # Ne pas planter le démarrage du serveur : on expose None et on logge l'erreur.
    logger.error(f"Impossible de charger le modèle Vosk au démarrage: {e}", exc_info=True)
    vosk_transcriber = None


def get_vosk_transcriber():
    """
    Helper pour récupérer l'instance. Lève une RuntimeError si non chargé,
    afin d'obliger les points d'entrée à vérifier l'état avant usage.
    """
    if vosk_transcriber is None:
        raise RuntimeError(
            "Vosk model non chargé. Définissez VOSK_MODEL_PATH ou placez le modèle dans 'models/' et redémarrez."
        )
    return vosk_transcriber