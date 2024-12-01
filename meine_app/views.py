import json, csv
from django.shortcuts import render, redirect
from django.contrib.auth.hashers import make_password, check_password
from django.http import HttpResponseBadRequest, HttpResponse, JsonResponse
from datetime import datetime #wird für Uhrzeiten benötigt

# Pfade zu JSON-Dateien
registrierte_benutzer = "/var/www/buchungssystem/db/users.json"
arbeitsbericht_erstellen = "/var/www/buchungssystem/db/arbeitsberichte.json" #Pfad zur JSON-Datei mit den abgespeicherten Arbeitsberichten
datenbank_module = "/var/www/buchungssystem/db/module.json"


def register_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        hashed_password = make_password(password)
        status_user = request.POST.get("status")
        if status_user != "basis":                 # Überprüfe den Token-Wert serverseitig auf 'basis', damit kein Hacker sich Admin-Rechte von Anfang sichern kann. 
            return HttpResponseBadRequest('Ungültiger Status des neuen Users!!!')

        # Benutzer laden
        try:
            with open(registrierte_benutzer, "r", encoding="utf-8") as file:
                data = json.load(file)
                users = data.get("users", [])  # Benutzerliste aus JSON holen
        except FileNotFoundError:
            data = {"users": []}  # JSON erstellen, falls sie nicht existiert
            users = []

        # Prüfen, ob der Benutzername schon existiert
        if any(user["username"] == username for user in users):
            return render(request, "meine_app/register.html", {"error": "Benutzername existiert bereits"})

        # Benutzer hinzufügen
        users.append({"username": username, "password": hashed_password, "status": status_user, "zugriff": True})
        data["users"] = users  # Benutzerliste aktualisieren

        # Daten in JSON speichern
        with open(registrierte_benutzer, "w", encoding="utf-8") as file:
            json.dump(data, file, indent=4)  # Schöne JSON-Ausgabe

        # Automatisch einloggen und zur Startseite weiterleiten
        request.session["username"] = username
        return redirect("home")

    # Für GET-Anfragen wird das Registrierungsformular angezeigt
    return render(request, "meine_app/register.html")


def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        # Benutzer laden
        try:
            with open(registrierte_benutzer, "r", encoding="utf-8") as file:
                data = json.load(file)
                users = data.get("users", [])
        except FileNotFoundError:
            return render(request, "meine_app/login.html", {"error": "Keine Benutzer registriert"})

        # Benutzer validieren
        for user in users:
            if user["username"] == username and check_password(password, user["password"]) and user["zugriff"] == True:
                request.session["username"] = username  # Session setzen
                return redirect("home")

        return render(request, "meine_app/login.html", {"error": "Ungültige Anmeldedaten oder dein Account wurde gesperrt!"})
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
    try:
        with open(datenbank_module, 'r', encoding='utf-8') as file:
            module = json.load(file)['module']
    except FileNotFoundError:
        return HttpResponseBadRequest('Module-Datei nicht auf Server gefunden')
    except json.JSONDecodeError:
        return HttpResponseBadRequest('Fehler beim Laden der JSON-Module-Datei')
    return render(request, 'meine_app/arbeitsbericht_erstellen.html', {'module': module})


def arbeitsbericht_speichern(request):
    if request.method == "POST":
        benutzer = request.session.get("username")                                              #hier die einzelnen values in der JSON
        modul = request.POST.get("modul")
        berichtsname = request.POST.get("berichtsname")
        startzeit = request.POST.get("startzeit")
        endzeit = request.POST.get("endzeit")
        breaktime = request.POST.get("breaktime")
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

        timeStart = datetime.fromisoformat(startzeit)                                           #Zeitdifferenz zwischen Start und Endzeit wird direkt hier ausgerechnet und mit in die JSON gespeichert.
        timeEnd = datetime.fromisoformat(endzeit)
        deltaRaw = timeEnd-timeStart
        zeitdauer = int(deltaRaw.total_seconds()/60)                                            #Aufruf Methode total_seconds von date-time-Modul
        pausenzeit = int(breaktime)
        netto_arbeitszeit = zeitdauer - pausenzeit

        berichte[benutzer][neue_id] = [modul, berichtsname, startzeit, endzeit, zeitdauer, pausenzeit, netto_arbeitszeit ,kommentare]     #Später prüfen, ob alte Berichte von neuen überschrieben werden

        
        with open(arbeitsbericht_erstellen, "w", encoding="utf-8") as datei:                    #Deserialisierung
            json.dump(berichte, datei, indent=4)

        return redirect("home")                                                                 #Nach dem Speichern des Arbeitsberichtes zurück auf die home.html

    return render(request, "meine_app/Arbeitsbericht_erstellen.html")                          


def arbeitsberichte_anzeigen_view(request):
    """
    Lädt alle Arbeitsberichte und gibt sie an das Template weiter.
    """
    try:
        with open(arbeitsbericht_erstellen, "r", encoding="utf-8") as file:
            berichte = json.load(file)  # JSON-Daten laden
    except FileNotFoundError:
        berichte = {}  # Falls keine Datei vorhanden, leere Daten zurückgeben

    return render(request, "meine_app/arbeitsberichte_anzeigen.html", {"berichte": berichte})



#hier sind die neuen Funktionen...


def download_drucken_view(request):
    username = request.session.get("username")
    if not username:
        return redirect("login")
    
    try:
        with open(arbeitsbericht_erstellen, "r", encoding="utf-8") as datei:
            berichte = json.load(datei)
    except FileNotFoundError:
        berichte = {}

    eigene_berichte = berichte.get(username, {})

    return render(request, "meine_app/download_drucken.html", {"berichte": eigene_berichte})


def arbeitsberichte_download_drucken_view(request, bericht_id):
    username = request.session.get("username")
    if not username:
        return redirect("login")

    try:
        with open(arbeitsbericht_erstellen, "r", encoding="utf-8") as datei:
            berichte = json.load(datei)
    except FileNotFoundError:
        return render(request, "meine_app/arbeitsberichte_download_drucken.html", {"error": "Keine Berichte gefunden"})

    eigene_berichte = berichte.get(username, {})
    bericht = eigene_berichte.get(str(bericht_id))

    if not bericht:
        return render(request, "meine_app/arbeitsberichte_download_drucken.html", {"error": "Bericht nicht gefunden"})

    return render(request, "meine_app/arbeitsberichte_download_drucken.html", {"bericht_id": bericht_id, "bericht": bericht})



def bericht_download_json_view(request, bericht_id):
    username = request.session.get("username")
    if not username:
        return redirect("login")

    try:
        with open(arbeitsbericht_erstellen, "r", encoding="utf-8") as datei:
            berichte = json.load(datei)
    except FileNotFoundError:
        return HttpResponseBadRequest("Berichte nicht verfügbar")

    bericht = berichte.get(username, {}).get(str(bericht_id))
    if not bericht:
        return HttpResponseBadRequest("Bericht nicht gefunden")

    data = {
        "modul": bericht[0],
        "berichtsname": bericht[1],
        "startzeit": bericht[2],
        "endzeit": bericht[3],
        "zeitdauer": bericht[4],
        "kommentare": bericht[5],
    }

    return JsonResponse(data)


def bericht_download_csv_view(request, bericht_id):
    username = request.session.get("username")
    if not username:
        return redirect("login")

    try:
        with open(arbeitsbericht_erstellen, "r", encoding="utf-8") as datei:
            berichte = json.load(datei)
    except FileNotFoundError:
        return HttpResponseBadRequest("Berichte nicht verfügbar")

    bericht = berichte.get(username, {}).get(str(bericht_id))
    if not bericht:
        return HttpResponseBadRequest("Bericht nicht gefunden")

    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = f'attachment; filename="bericht_{bericht_id}.csv"'

    writer = csv.writer(response)
    writer.writerow(["Modul", "Berichtsname", "Startzeit", "Endzeit", "Zeitdauer", "Kommentare"])
    writer.writerow(bericht)

    return response
