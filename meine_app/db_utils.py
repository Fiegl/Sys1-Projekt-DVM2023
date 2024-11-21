import json
from pathlib import Path
from django.contrib.auth.hashers import make_password
import logging

# Logger einrichten
logger = logging.getLogger(__name__)

# Pfad zur JSON-Datenbank
DB_PATH = Path(__file__).resolve().parent.parent / 'db' / 'users.json'

def load_users():
    """Lädt alle Benutzer aus der JSON-Datei."""
    try:
        with open(DB_PATH, 'r', encoding='utf-8') as file:
            logger.info(f"Benutzer-Datenbank geladen: {DB_PATH}")
            return json.load(file)
    except FileNotFoundError:
        logger.warning("Benutzer-Datenbank nicht gefunden. Erstelle eine neue.")
        return []
    except json.JSONDecodeError as e:
        logger.error(f"Fehler beim Lesen der JSON-Datei: {str(e)}")
        return []

def save_users(users):
    """Speichert die Benutzer in der JSON-Datei."""
    try:
        with open(DB_PATH, 'w', encoding='utf-8') as file:
            json.dump(users, file, indent=4)  # Verwende 'indent=4' für besser lesbare Ausgabe
    except Exception as e:
        logger.error(f"Fehler beim Speichern der Benutzer: {e}")


def create_user(username, password):
    """Erstellt einen neuen Benutzer."""
    logger.info(f"Registriere Benutzer: {username}")
    
    users = load_users()
    
    # Benutzername überprüfen
    if any(user['username'] == username for user in users):
        logger.warning(f"Benutzername {username} existiert bereits.")
        return False, "Username already exists."

    # Passwort hashen und neuen Benutzer hinzufügen
    hashed_password = make_password(password)  # Django's Passwort-Hashing
    users.append({'username': username, 'password': hashed_password})
    save_users(users)
    logger.info(f"Benutzer {username} erfolgreich registriert.")
    return True, "User created successfully."

def authenticate_user(username, password):
    """Authentifiziert einen Benutzer."""
    users = load_users()
    for user in users:
        if user['username'] == username and check_password(password, user['password']):
            return True
    return False
