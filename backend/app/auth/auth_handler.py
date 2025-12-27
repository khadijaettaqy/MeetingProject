from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
import hashlib
import base64
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
# Configuration JWT
SECRET_KEY = "votre_secret_key_très_secure_et_long_ici_changez_cette_valeur"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Configuration OAuth2
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

# Configuration password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def _process_password_for_bcrypt(password: str) -> str:
    """Prépare n'importe quel mot de passe pour bcrypt (SHA256 + base64)"""
    sha256_hash = hashlib.sha256(password.encode('utf-8')).digest()
    return base64.b64encode(sha256_hash).decode('utf-8')

def get_password_hash(password: str) -> str:
    """Hash un mot de passe de n'importe quelle longueur"""
    processed_password = _process_password_for_bcrypt(password)
    return pwd_context.hash(processed_password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Vérifie un mot de passe (prend en charge tous les formats)"""
    # Essayer avec la méthode de traitement d'abord
    processed_password = _process_password_for_bcrypt(plain_password)
    if pwd_context.verify(processed_password, hashed_password):
        return True
    
    # Pour la rétrocompatibilité
    try:
        if pwd_context.verify(plain_password, hashed_password):
            return True
    except:
        pass
    
    return False

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Crée un token JWT"""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """Récupérer l'utilisateur courant à partir du token JWT"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Impossible de valider les identifiants",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = payload.get("user_id")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise credentials_exception
    
    return user
def verify_token(token: str):
    """
    Vérifie un token JWT et retourne le payload
    """
    try:
        # Utilisez la même SECRET_KEY que pour la création des tokens
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expiré")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Token invalide")
def decode_access_token(token: str) -> dict:
    """
    Décode un token JWT et retourne le payload
    (utilisable pour WebSocket)
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expiré")
    except JWTError:
        raise HTTPException(status_code=401, detail="Token invalide")


