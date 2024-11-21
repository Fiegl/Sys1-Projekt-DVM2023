import json
from django.shortcuts import render, redirect
from django.contrib.auth.hashers import make_password, check_password
from .db_utils import create_user, authenticate_user

# Pfad zur JSON-Datei
USER_FILE = "/var/www/buchungssystem/db/users.json"

def register_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        hashed_password = make_password(password)

        # Lade bestehende Benutzer
        try:
            with open(USER_FILE, "r") as file:
                users = json.load(file)
        except FileNotFoundError:
            users = []

        # Prüfen, ob der Benutzername schon existiert
        if any(user["username"] == username for user in users):
            return render(request, "meine_app/register.html", {"error": "Benutzername existiert bereits"})

        # Benutzer hinzufügen
        users.append({"username": username, "password": hashed_password})
        with open(USER_FILE, "w") as file:
            json.dump(users, file)

        # Automatisch einloggen oder zur Login-Seite weiterleiten
        request.session["username"] = username
        return redirect("home")
    return render(request, "meine_app/register.html")


def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        # Lade bestehende Benutzer
        try:
            with open(USER_FILE, "r") as file:
                users = json.load(file)
        except FileNotFoundError:
            return render(request, "meine_app/login.html", {"error": "Keine Benutzer registriert"})

        # Benutzer validieren
        for user in users:
            if user["username"] == username and check_password(password, user["password"]):
                request.session["username"] = username  # Session setzen
                return redirect("home")

        return render(request, "meine_app/login.html", {"error": "Ungültige Anmeldedaten"})
    return render(request, "meine_app/login.html")


def home_view(request):
    username = request.session.get("username")
    if not username:
        return redirect("login")  # Falls nicht eingeloggt, zur Login-Seite
    return render(request, "meine_app/home.html", {"username": username})


def logout_view(request):
    # Session löschen
    request.session.flush()
    return redirect("login")
