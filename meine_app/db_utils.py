from tinydb import TinyDB, Query
from werkzeug.security import generate_password_hash, check_password_hash

# Pfad zur JSON-Datenbankdatei
db = TinyDB('db/users.json')
User = Query()

def create_user(username, password):
    # Überprüfen, ob Benutzername bereits existiert
    if db.search(User.username == username):
        return None, "Username already exists."

    # Passwort hashen und neuen Benutzer hinzufügen
    hashed_password = generate_password_hash(password)
    db.insert({'username': username, 'password': hashed_password})
    return True, "User created successfully."

def authenticate_user(username, password):
    user_data = db.search(User.username == username)
    if user_data:
        user = user_data[0]
        # Passwort überprüfen
        if check_password_hash(user['password'], password):
            return True
    return False
