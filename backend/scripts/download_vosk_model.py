# scripts/download_vosk_model.py
import os
import zipfile
import requests

def download_vosk_model():
    """Télécharger le modèle Vosk français"""
    model_url = "https://alphacephei.com/vosk/models/vosk-model-small-fr-0.22.zip"
    model_dir = "models"
    model_path = os.path.join(model_dir, "vosk-model-small-fr-0.22")
    
    if os.path.exists(model_path):
        print(f"✅ Modèle déjà présent: {model_path}")
        return model_path
    
    print("📥 Téléchargement du modèle Vosk...")
    os.makedirs(model_dir, exist_ok=True)
    
    zip_path = os.path.join(model_dir, "vosk-model-small-fr-0.22.zip")
    
    # Télécharger
    response = requests.get(model_url, stream=True)
    with open(zip_path, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
    
    # Extraire
    print("📦 Extraction du modèle...")
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(model_dir)
    
    # Nettoyer
    os.remove(zip_path)
    
    print(f"✅ Modèle téléchargé: {model_path}")
    return model_path

if __name__ == "__main__":
    download_vosk_model()