import json, csv
import uuid
from django.shortcuts import render, redirect
from django.views import View
from django.contrib.auth.hashers import make_password, check_password
from django.http import HttpResponseBadRequest, HttpResponse, JsonResponse
from datetime import datetime
import xml.etree.ElementTree as ET


# Pfade zu den JSON-Dateien
registrierte_benutzer = "/var/www/buchungssystem/db/users.json"
arbeitsbericht_erstellen = "/var/www/buchungssystem/db/arbeitsberichte.json"
datenbank_module = "/var/www/buchungssystem/db/module.json"


#Hier die Funktionen für Registrieren, Ein- und Auslogen
#########################################################


def register_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        matrikelnummer = request.POST.get("matrikelnummer")
        password = request.POST.get("password")
        hashed_password = make_password(password)
        status_user = request.POST.get("status")

        # Überprüfen, ob der Status gültig ist
        if status_user != "basis":
            return HttpResponseBadRequest('Ungültiger Status des neuen Users!')

        # Benutzer laden
        try:
            with open(registrierte_benutzer, "r", encoding="utf-8") as file:
                data = json.load(file)
                users = data.get("users", [])
        except FileNotFoundError:
            data = {"users": []}
            users = []

        # Überprüfen, ob Benutzername oder Matrikelnummer bereits existiert
        if any(user["username"] == username or user["matrikelnummer"] == matrikelnummer for user in users):
            return render(request, "meine_app/register.html", {"error": "Benutzername oder Matrikelnummer existiert bereits"})

        # Benutzer hinzufügen
        new_user = {
            "username": username,
            "matrikelnummer": matrikelnummer,
            "password": hashed_password,
            "status": status_user,
            "zugriff": True
        }
        users.append(new_user)
        data["users"] = users

        # Daten in JSON speichern
        with open(registrierte_benutzer, "w", encoding="utf-8") as file:
            json.dump(data, file, indent=4)

        # Benutzer auch in die arbeitsberichte.json hinzufügen
        try:
            with open(arbeitsbericht_erstellen, "r", encoding="utf-8") as file:
                arbeitsberichte = json.load(file)
                if "arbeitsberichte" not in arbeitsberichte:
                    arbeitsberichte["arbeitsberichte"] = []  # Sicherstellen, dass die Liste existiert
        except FileNotFoundError:
            arbeitsberichte = {"arbeitsberichte": []}  # Initialisiere ein korrektes Dictionary

        # Arbeitsberichte für neuen Benutzer initialisieren
        arbeitsberichte["arbeitsberichte"].append({
            "name": username,
            "matrikelnummer": matrikelnummer,
            "berichte": {}
        })

        with open(arbeitsbericht_erstellen, "w", encoding="utf-8") as file:
            json.dump(arbeitsberichte, file, indent=4)

        # Automatisch einloggen und zur Startseite weiterleiten
        request.session["username"] = username
        request.session["matrikelnummer"] = matrikelnummer
        return redirect("home")

    # Für GET-Anfragen wird das Registrierungsformular angezeigt
    return render(request, "meine_app/register.html")


def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        try:
            with open(registrierte_benutzer, "r", encoding="utf-8") as file:
                data = json.load(file)
                users = data.get("users", [])
        except FileNotFoundError:
            return render(request, "meine_app/login.html", {"error": "Keine Benutzer registriert"})

        for user in users:
            if user["username"] == username and check_password(password, user["password"]) and user["zugriff"]:
                request.session["username"] = username
                request.session["matrikelnummer"] = user["matrikelnummer"]
                return redirect("home")

        return render(request, "meine_app/login.html", {"error": "Ungültige Anmeldedaten oder gesperrter Account!"})
    return render(request, "meine_app/login.html")


def home_view(request):
    username = request.session.get("username")
    
    if not username:
        return redirect("login")  # Falls nicht eingeloggt, zur Login-Seite

    try:
        with open(registrierte_benutzer, "r", encoding="utf-8") as file:
            userDB = json.load(file)
            alleUser = userDB.get("users", [])
            for angemeldeterUser in alleUser:
                if angemeldeterUser["username"] == username:
                    statusAngemeldeterUser = angemeldeterUser["status"]
                    matrikelnummerAngemeldeterUser = angemeldeterUser["matrikelnummer"]
                    zugriffAngemeldeterUser = angemeldeterUser["zugriff"]
                    break  # Schleife beenden, wenn der Benutzer gefunden wurde
            else:
                statusAngemeldeterUser = None  # Falls der Benutzer nicht gefunden wurde
    
    except FileNotFoundError:
        return render(request, "meine_app/login.html", {"error": "Keine Benutzer registriert"})
    except json.JSONDecodeError:
        return render(request, "meine_app/login.html", {"error": "Fehler beim Laden der Benutzerdatei"})

    context = {
        "username": username,
        "matrikelnummer": matrikelnummerAngemeldeterUser,
        "statusUser": statusAngemeldeterUser,
        "zugriffUser": zugriffAngemeldeterUser
    }

    return render(request, "meine_app/home.html", context)


def logout_view(request):
    request.session.flush()
    return redirect("login")


####################################################################################

#Hier die Funktionen für die Kachel neuen_Arbeitsbericht_anlegen
####################################################################################


def arbeitsbericht_erstellen_view(request):
    try:
        with open(datenbank_module, 'r', encoding='utf-8') as file:
            module = json.load(file)['module']
    except (FileNotFoundError, json.JSONDecodeError):
        return HttpResponseBadRequest('Fehler beim Laden der Module-Datei.')
    return render(request, 'meine_app/arbeitsbericht_erstellen.html', {'module': module})


def arbeitsbericht_speichern(request):
    neue_uuid = str(uuid.uuid4())  # UUID in String umwandeln
    if request.method == "POST":
        benutzer = request.session.get("username")  # Aktueller Benutzer
        matrikelnummer = request.session.get("matrikelnummer")
        modul = request.POST.get("modul")
        berichtsname = request.POST.get("berichtsname")
        startzeit = request.POST.get("startzeit")
        endzeit = request.POST.get("endzeit")
        breaktime = request.POST.get("breaktime", 0)  # Optional, Standardwert 0
        kommentare = request.POST.get("kommentare", "")

        # Matrikelnummer aus der Benutzerdatei abrufen
        try:
            with open(registrierte_benutzer, "r", encoding="utf-8") as file:
                benutzer_daten = json.load(file)        
            # Suche nach dem Benutzer in den Benutzerdaten
            user_info = None
            for user in benutzer_daten["users"]:
                if user["username"] == benutzer:
                    user_info = user
                    break
            # Hole die Matrikelnummer des Benutzers, falls vorhanden
            if user_info:
                matrikelnummer = user_info["matrikelnummer"]
            else:
                matrikelnummer = None

        
        except (FileNotFoundError, KeyError):
            return HttpResponseBadRequest("Fehler beim Abrufen der Matrikelnummer.")

        if not matrikelnummer:
            return HttpResponseBadRequest("Matrikelnummer nicht gefunden.")

        # Arbeitsberichte aus der Datei laden
        try:
            with open(arbeitsbericht_erstellen, "r", encoding="utf-8") as file:
                daten = json.load(file)  # Vorhandene JSON-Daten laden
        except FileNotFoundError:
            daten = {"arbeitsberichte": []}  # Initiale Struktur, falls Datei nicht existiert
        except json.JSONDecodeError:
            return HttpResponseBadRequest("Fehler beim Laden der Arbeitsberichte-Datei.")

        timeStart = datetime.fromisoformat(startzeit)  # Zeitdifferenz zwischen Start und Endzeit wird direkt hier ausgerechnet und mit in die JSON gespeichert.
        timeEnd = datetime.fromisoformat(endzeit)
        deltaRaw = timeEnd - timeStart
        zeitdauer = int(deltaRaw.total_seconds() / 60)  # Aufruf Methode total_seconds von date-time-Modul
        pausenzeit = int(breaktime)
        netto_arbeitszeit = zeitdauer - pausenzeit

        # Neuen Bericht erstellen
        neuer_bericht = {
            "benutzername": benutzer,
            "matrikelnummer": matrikelnummer,
            "id": neue_uuid,
            "modul": modul,
            "berichtsname": berichtsname,
            "startzeit": startzeit,
            "endzeit": endzeit,
            "pausenzeit": pausenzeit,
            "nettoarbeitszeit": netto_arbeitszeit,
            "kommentare": kommentare            
        }

        # Neuen Bericht hinzufügen
        daten["arbeitsberichte"].append(neuer_bericht)

        # Aktualisierte JSON speichern
        try:
            with open(arbeitsbericht_erstellen, "w", encoding="utf-8") as file:
                json.dump(daten, file, indent=4)
        except OSError:
            return HttpResponseBadRequest("Fehler beim Speichern der Arbeitsberichte-Datei.")

        return redirect("home")  # Nach dem Speichern zur Startseite weiterleiten

    return render(request, "meine_app/Arbeitsbericht_erstellen.html")


###############################################################################################


#Hier die Funktionen für die Kachel alle_Berichte_anzeigen
###############################################################################################


def arbeitsberichte_anzeigen_view(request):
    eingeloggter_user = request.session.get("username")
    if not eingeloggter_user:
        return redirect("login")  # Weiterleitung zur Login-Seite

    eigene_berichte = []

    try:
        with open(arbeitsbericht_erstellen, "r", encoding="utf-8") as file:
            daten = json.load(file)  # JSON-Daten laden
            
            # Lade die Arbeitsberichte (Liste)
            berichte = daten.get("arbeitsberichte", [])
            
            # Filtere Berichte des aktuellen Benutzers und ignoriere Einträge ohne ID
            eigene_berichte = [
                bericht for bericht in berichte
                if (bericht.get("name") == eingeloggter_user or bericht.get("benutzername") == eingeloggter_user)
                and bericht.get("id")  # Nur gültige Berichte mit "id"
            ]
    except (FileNotFoundError, json.JSONDecodeError):
        # Fehlerbehandlung: keine Datei oder ungültige JSON
        eigene_berichte = []

    # Übergabe der Berichte an das Template
    return render(request, "meine_app/arbeitsberichte_anzeigen.html", {"berichte": eigene_berichte})


####################################################################################################


#Hier die Funbktionen für die Kachel Download_&_Drucken
####################################################################################################


def arbeitsberichte_download_drucken_view(request):
    try:
        with open(arbeitsbericht_erstellen, "r", encoding="utf-8") as file:
            daten = json.load(file)
            berichte = daten.get("arbeitsberichte", [])
    except FileNotFoundError:
        berichte = []
    except json.JSONDecodeError:
        return HttpResponseBadRequest("Fehler beim Laden der Arbeitsberichte-Datei.")

    return render(request, "meine_app/arbeitsberichte_download_drucken.html", {"berichte": berichte})


def bericht_herunterladen(request, format, bericht_id):
    try:
        with open(arbeitsbericht_erstellen, "r", encoding="utf-8") as file:
            daten = json.load(file)
            berichte = daten.get("arbeitsberichte", [])
    except (FileNotFoundError, json.JSONDecodeError):
        return HttpResponse("Fehler beim Laden der Arbeitsberichte.", status=500)

    # Bericht mit der passenden ID suchen
    bericht = next((b for b in berichte if str(b.get("id")) == str(bericht_id)), None)
    if not bericht:
        return HttpResponse("Bericht nicht gefunden.", status=404)

    if format == "json":
        # Bericht im JSON-Format zurückgeben
        return JsonResponse(bericht, json_dumps_params={"indent": 4})

    elif format == "csv":
        # Bericht im CSV-Format zurückgeben
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = f'attachment; filename="bericht_{bericht_id}.csv"'

        writer = csv.writer(response)
        writer.writerow(bericht.keys())  # CSV-Kopfzeile
        writer.writerow(bericht.values())  # CSV-Daten

        return response

    elif format == "xml":
        # Bericht im XML-Format zurückgeben
        response = HttpResponse(content_type="application/xml")
        response["Content-Disposition"] = f'attachment; filename="bericht_{bericht_id}.xml"'

        root = ET.Element("Arbeitsbericht")
        for key, value in bericht.items():
            child = ET.SubElement(root, key)
            child.text = str(value)

        tree = ET.ElementTree(root)
        tree.write(response, encoding="unicode")

        return response

    else:
        return HttpResponse("Ungültiges Format.", status=400)


##################################################################################################


#Hier die Funktionen für die Kacheln dein_Profil
##################################################################################################


def profile_page_view(request):
    try:
        with open(registrierte_benutzer, "r", encoding="utf-8") as file:
            benutzer_daten = json.load(file)  # JSON-Daten laden
    except FileNotFoundError:
        benutzer_daten = {"users": []}  # Leere Liste, falls Datei nicht existiert
    except json.JSONDecodeError:
        return HttpResponseBadRequest("Fehler beim Laden der Benutzerdaten-Datei.")

    return render(request, "meine_app/profile_page.html", {"benutzer_daten": benutzer_daten["users"]})
