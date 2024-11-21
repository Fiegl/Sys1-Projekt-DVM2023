import json
from django.shortcuts import render, redirect
from django.contrib.auth.hashers import make_password, check_password
from .db_utils import create_user, authenticate_user

# Pfade zu JSON-Dateien
USER_FILE = "/var/www/buchungssystem/db/users.json"
arbeitsbericht_erstellen = "/var/www/buchungssystem/db/arbeitsberichte.json" #Pfad zur JSON-Datei mit den abgespeicherten Arbeitsberichten

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

def arbeitsbericht_erstellen_view(request):
    return render(request, "meine_app/Arbeitsbericht_erstellen.html")

def arbeitsbericht_speichern(request):
    if request.method == "POST":
        benutzer = request.session.get("username")                                              #hier die einzelnen values in der JSON
        modul = request.POST.get("modul")
        berichtsname = request.POST.get("berichtsname")
        startzeit = request.POST.get("startzeit")
        endzeit = request.POST.get("endzeit")
        kommentare = request.POST.get("kommentare")

        try:
            with open(arbeitsbericht_erstellen, "r", encoding="utf-8") as datei:                #Daten werden aus JSON als String geladen (Serialisierung)
                berichte = json.load(datei)
        except FileNotFoundError:
            berichte = {}

        if benutzer not in berichte:                                                            #hier werden für den benutzer (Key in der JSON) die jeweiligen Berichte gespeichert
            berichte[benutzer] = {}


        neue_id = max(map(int, berichte[benutzer].keys()), default=0) + 1                       #in der JSON ist benutzer der KEY, bekommt eine ID zugeordnet,
                                                                                                #jeder Arbeitsbericht bekommt eine fortlaufende Nr. zugeordnet

        berichte[benutzer][neue_id] = [modul, berichtsname, startzeit, endzeit, kommentare]     #Später prüfen, ob alte Berichte von neuen überschrieben werden


        with open(arbeitsbericht_erstellen, "w", encoding="utf-8") as datei:                    #Deserialisierung
            json.dump(berichte, datei, indent=4)

        return redirect("home")                                                                 #Nach dem Speichern des Arbeitsberichtes zurück auf die home.html

    return render(request, "meine_app/Arbeitsbericht_erstellen.html")  
