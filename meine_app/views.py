import json, csv
import uuid
from django.shortcuts import render, redirect
from django.views import View
from django.contrib.auth.hashers import make_password, check_password
from django.contrib.auth import logout
from django.http import HttpResponseBadRequest, HttpResponse, JsonResponse, HttpResponseForbidden, HttpResponseServerError
from datetime import datetime
import xml.etree.ElementTree as ET
from functools import wraps


# Pfade zu den JSON-Dateien
registrierte_benutzer = "/var/www/buchungssystem/db/users.json"
arbeitsbericht_erstellen = "/var/www/buchungssystem/db/arbeitsberichte.json"
datenbank_module = "/var/www/buchungssystem/db/module.json"
anfragen_datei = "/var/www/buchungssystem/db/anfragen.json"
datenbank_module_editable = "/var/www/buchungssystem/db/module_editable.json"


### Zugriff auf URL ohne Berechtigung blocken mit Dekorator ###
def admin_berechtigung_check(view_func):
    @wraps(view_func)                                       # Dekorator aus dem functools-Modul, bewahrt die Metadaten der ursprünglichen Funktion (wichtig fürs Debuggen)
    def _wrapped_view(request, *args, **kwargs):
        eingeloggter_user = request.session.get("username")
        if not eingeloggter_user:
            return HttpResponseForbidden("You are not allowed to access this page without Login.")

        try:
            with open(registrierte_benutzer, 'r', encoding='utf-8') as file:
                benutzer_daten = json.load(file)
        except:
            return HttpResponseServerError('Fehler beim Aufrufen der Userdatenbank innerhalb des Admin-Dekorators!')

        user_status = None
        for user in benutzer_daten['users']:
            if user['username'] == eingeloggter_user:
                user_status = user['status']
                break

        if user_status != 'admin':
            return HttpResponseForbidden("You are not allowed to access this page. Falscher User-Status!")

        return view_func(request, *args, **kwargs)
    return _wrapped_view
########


# Hier die Funktionen für Registrieren, Ein- und Auslogen
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
            return HttpResponseBadRequest("Ungültiger Status des neuen Users!")

        # Benutzer laden
        try:
            with open(registrierte_benutzer, "r", encoding="utf-8") as file:
                data = json.load(file)
                users = data.get("users", [])
        except FileNotFoundError:
            data = {"users": []}
            users = []

        # Überprüfen, ob Benutzername oder Matrikelnummer bereits existiert
        if any(
            user["username"] == username or user["matrikelnummer"] == matrikelnummer
            for user in users
        ):
            return render(
                request,
                "meine_app/register.html",
                {"error": "Benutzername oder Matrikelnummer existiert bereits"},
            )

        # Benutzer hinzufügen
        new_user = {
            "username": username,
            "matrikelnummer": matrikelnummer,
            "password": hashed_password,
            "status": status_user,
            "zugriff": True,
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
                    arbeitsberichte["arbeitsberichte"] = (
                        []
                    )  # Sicherstellen, dass die Liste existiert
        except FileNotFoundError:
            arbeitsberichte = {
                "arbeitsberichte": []
            }  # Initialisiere ein korrektes Dictionary

        # Arbeitsberichte für neuen Benutzer initialisieren
        arbeitsberichte["arbeitsberichte"].append(
            {"name": username, "matrikelnummer": matrikelnummer, "berichte": {}}
        )

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
            return render(
                request, "meine_app/login.html", {"error": "Keine Benutzer registriert"}
            )

        for user in users:
            if (
                user["username"] == username
                and check_password(password, user["password"])
                and user["zugriff"]
            ):
                request.session["username"] = username
                request.session["matrikelnummer"] = user["matrikelnummer"]
                return redirect("home")

        return render(
            request,
            "meine_app/login.html",
            {"error": "Ungültige Anmeldedaten oder gesperrter Account!"},
        )
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
        return render(
            request, "meine_app/login.html", {"error": "Keine Benutzer registriert"}
        )
    except json.JSONDecodeError:
        return render(
            request,
            "meine_app/login.html",
            {"error": "Fehler beim Laden der Benutzerdatei"},
        )

    context = {
        "username": username,
        "matrikelnummer": matrikelnummerAngemeldeterUser,
        "statusUser": statusAngemeldeterUser,
        "zugriffUser": zugriffAngemeldeterUser,
    }

    return render(request, "meine_app/home.html", context)


def logout_view(request):
    logout(request)
    return redirect("login")



####################################################################################

# Hier die Funktionen für die Kachel neuen_Arbeitsbericht_anlegen
####################################################################################


def arbeitsbericht_erstellen_view(request):
    try:
        with open(datenbank_module, "r", encoding="utf-8") as file:
            module = json.load(file)["module"]
    except (FileNotFoundError, json.JSONDecodeError):
        return HttpResponseBadRequest("Fehler beim Laden der Module-Datei.")
    return render(
        request, "meine_app/arbeitsbericht_erstellen.html", {"module": module}
    )


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
            daten = {
                "arbeitsberichte": []
            }  # Initiale Struktur, falls Datei nicht existiert
        except json.JSONDecodeError:
            return HttpResponseBadRequest(
                "Fehler beim Laden der Arbeitsberichte-Datei."
            )

        timeStart = datetime.fromisoformat(
            startzeit
        )  # Zeitdifferenz zwischen Start und Endzeit wird direkt hier ausgerechnet und mit in die JSON gespeichert.
        timeEnd = datetime.fromisoformat(endzeit)
        deltaRaw = timeEnd - timeStart
        zeitdauer = int(
            deltaRaw.total_seconds() / 60
        )  # Aufruf Methode total_seconds von date-time-Modul
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
            "kommentare": kommentare,
        }

        # Neuen Bericht hinzufügen
        daten["arbeitsberichte"].append(neuer_bericht)

        # Aktualisierte JSON speichern
        try:
            with open(arbeitsbericht_erstellen, "w", encoding="utf-8") as file:
                json.dump(daten, file, indent=4)
        except OSError:
            return HttpResponseBadRequest(
                "Fehler beim Speichern der Arbeitsberichte-Datei."
            )

        return redirect("home")  # Nach dem Speichern zur Startseite weiterleiten

    return render(request, "meine_app/Arbeitsbericht_erstellen.html")


###############################################################################################


# Hier die Funktionen für die Kachel alle_Berichte_anzeigen
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
                bericht
                for bericht in berichte
                if (
                    bericht.get("name") == eingeloggter_user
                    or bericht.get("benutzername") == eingeloggter_user
                )
                and bericht.get("id")  # Nur gültige Berichte mit "id"
            ]
    except (FileNotFoundError, json.JSONDecodeError):
        # Fehlerbehandlung: keine Datei oder ungültige JSON
        eigene_berichte = []

    # Übergabe der Berichte an das Template
    return render(
        request,
        "meine_app/arbeitsberichte_anzeigen.html",
        {"berichte": eigene_berichte},
    )
    
    

def arbeitsbericht_loeschen(request, bericht_id):
    if request.method == "POST":
        try:
            with open(arbeitsbericht_erstellen, "r", encoding="utf-8") as file:
                daten = json.load(file)
            berichte = daten.get("arbeitsberichte", [])

            # Filtere den Bericht mit der angegebenen ID heraus
            neue_berichte = [bericht for bericht in berichte if bericht.get("id") != bericht_id]
            daten["arbeitsberichte"] = neue_berichte

            # Speichere die aktualisierte Datei
            with open(arbeitsbericht_erstellen, "w", encoding="utf-8") as file:
                json.dump(daten, file, indent=4)

        except (FileNotFoundError, json.JSONDecodeError, OSError):
            return HttpResponseBadRequest("Fehler beim Löschen des Berichts.")

        return redirect("arbeitsberichte_anzeigen")  # Zurück zur Anzeige-Seite

    return HttpResponseBadRequest("Ungültige Anfrage.")



####################################################################################################


# Hier die Funbktionen für die Kachel Download_&_Drucken
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

    return render(
        request,
        "meine_app/arbeitsberichte_download_drucken.html",
        {"berichte": berichte},
    )


def bericht_herunterladen(request, format, bericht_id):
    with open(arbeitsbericht_erstellen, "r", encoding="utf-8") as file:
        daten = json.load(file).get("arbeitsberichte", [])

    # hier nach den Berichten suchen und iterieren:
    for bericht in daten:
        if bericht.get("id") == bericht_id:
            if format == "json":
                response = HttpResponse(json.dumps(bericht, indent=4), content_type="application/json")
                response["Content-Disposition"] = f"attachment; filename=bericht_{bericht_id}.json"
                return response

            elif format == "csv":
                response = HttpResponse(content_type="text/csv")
                response["Content-Disposition"] = f"attachment; filename=bericht_{bericht_id}.csv"
                writer = csv.writer(response)
                writer.writerow(bericht.keys())
                writer.writerow(bericht.values())
                return response

            elif format == "xml":
                root = ET.Element("Arbeitsbericht")
                for key, value in bericht.items():
                    ET.SubElement(root, key).text = str(value)
                response = HttpResponse(ET.tostring(root, encoding="unicode"), content_type="application/xml")
                response["Content-Disposition"] = f"attachment; filename=bericht_{bericht_id}.xml"
                return response

    return HttpResponse("Bericht nicht gefunden.")

# Quelle zum Nachlesen: https://docs.djangoproject.com/en/3.0/howto/outputting-csv/
#                       https://docs.djangoproject.com/en/5.1/ref/request-response/
#                       https://docs.python.org/3/library/json.html
#                       https://docs.python.org/3/library/csv.html
#                       https://docs.python.org/3/library/xml.etree.elementtree.html

# Dieser Link ist interessant, wenn wir das in eine Klasse umwandeln wollen:
# https://docs.djangoproject.com/en/5.1/topics/serialization/


def bericht_hochladen(request):
    if request.method == "POST":
        hochgeladene_datei = request.FILES.get("upload_file")
        if not hochgeladene_datei:
            return JsonResponse({"error": "Keine Datei hochgeladen."}, status=400)

        try:
            hochgeladene_daten = json.load(hochgeladene_datei)
        except json.JSONDecodeError:
            return JsonResponse({"error": "Ungültige JSON-Datei."}, status=400)

        hochgeladene_id = hochgeladene_daten.get("id")
        if not hochgeladene_id:
            return JsonResponse({"error": "Die Datei enthält keine UUID."}, status=400)

        with open(arbeitsbericht_erstellen, "r", encoding="utf-8") as file:
            daten = json.load(file)

        bericht_gefunden = False
        for index, bericht in enumerate(daten.get("arbeitsberichte", [])):
            if bericht.get("id") == hochgeladene_id:
                daten["arbeitsberichte"][index] = hochgeladene_daten
                bericht_gefunden = True
                break

        if not bericht_gefunden:
            return JsonResponse({"error": f"Kein Bericht mit UUID {hochgeladene_id} gefunden."}, status=404)

        with open(arbeitsbericht_erstellen, "w", encoding="utf-8") as file:
            json.dump(daten, file, indent=4)

        return redirect("arbeitsberichte_download_drucken")

    return JsonResponse({"error": "Ungültige Anfrage."}, status=400)


# Quelle zum Nachlesen: https://docs.djangoproject.com/en/5.1/topics/http/file-uploads/
#                       https://docs.python.org/3/library/functions.html#enumerate
#                       https://docs.djangoproject.com/en/5.1/topics/forms/


##################################################################################################
# Ab hier die Funktionen für die Kacheln dein_Profil_admin, also Admin-Profilseite
##################################################################################################

@admin_berechtigung_check
def profile_page_view(request):
    eingeloggter_user = request.session.get("username")
    user_initiale = eingeloggter_user[0].upper()
    
    try:
        with open(registrierte_benutzer, "r", encoding="utf-8") as file:
            benutzer_daten = json.load(file)  # JSON-Daten laden
    except FileNotFoundError:
        benutzer_daten = {"users": []}  # Leere Liste, falls Datei nicht existiert
    except json.JSONDecodeError:
        return HttpResponseBadRequest("Fehler beim Laden der Benutzerdaten-Datei.")
    
    try:
        with open(anfragen_datei, "r", encoding="utf-8") as file:
            anfrage_daten = json.load(file)  # JSON-Daten laden
    except FileNotFoundError:
        anfrage_daten = {"anfragen": []}  # Leere Liste, falls Datei nicht existiert
    except json.JSONDecodeError:
        return HttpResponseBadRequest("Fehler beim Laden der Anfragen-Datei.")
    

    # JSON-Datei mit Arbeitsberichten laden
    with open(arbeitsbericht_erstellen, 'r') as file:
        daten = json.load(file)

    # Dictionary zur Speicherung der aggregierten Arbeitszeiten
    arbeitszeiten_module = {}

    # Eintraege des eingeloggten Benutzers durchsuchen und aggregieren
    for bericht in daten['arbeitsberichte']:
        if bericht['benutzername'] == eingeloggter_user:
            modul = bericht['modul']
            nettoarbeitszeit = bericht['nettoarbeitszeit']
            if modul in arbeitszeiten_module:
                arbeitszeiten_module[modul] += nettoarbeitszeit
            else:
                arbeitszeiten_module[modul] = nettoarbeitszeit

    # Gesamtsumme der Nettoarbeitszeiten berechnen
    gesamt_nettoarbeitszeit = sum(arbeitszeiten_module.values())

    # Prozentualen Anteil jedes Moduls berechnen und auf ganze Zahlen runden
    prozentualer_anteil = {}
    for modul, zeit in arbeitszeiten_module.items():
        prozentualer_anteil[modul] = round((zeit / gesamt_nettoarbeitszeit) * 100)

    # JSON-Datei mit Modulnamen laden
    with open(datenbank_module, 'r', encoding="utf-8") as file:
        module_daten = json.load(file)

    # Neues Dictionary zur Speicherung aller Werte
    alle_werte = {}
    for modul, zeit in arbeitszeiten_module.items():
        alle_werte[modul] = {
            "modulname": module_daten["module"][modul],
            "nettoarbeitszeit": zeit,
            "prozentualer_anteil": prozentualer_anteil[modul]
        }

    # Dictionary nach Keys sortieren
    alle_werte = dict(sorted(alle_werte.items()))

    allerUebergebenerInhalt = {
        "benutzer_daten": benutzer_daten["users"],
        "anfrage_daten": anfrage_daten["anfragen"],
        "user_initiale": user_initiale,
        "eingeloggter_user": eingeloggter_user,
        "alle_werte": alle_werte,
        "gesamt_nettoarbeitszeit": gesamt_nettoarbeitszeit
    }

    return render(request, "meine_app/profile_page_admin.html", allerUebergebenerInhalt)


def loesche_anfrage(request):
    if request.method == "POST":
        username = request.POST.get("username")
        matrikelnummer = request.POST.get("matrikelnummer")

        try:
            with open(registrierte_benutzer, "r", encoding="utf-8") as file:
                benutzer_daten = json.load(file)
            for user in benutzer_daten["users"]:
                if user["username"] == username:
                    if user["status"] == "basis":
                        user["status"] = "vip"
                    elif user["status"] == "vip":
                        user["status"] = "admin"
                    break
            with open(registrierte_benutzer, "w", encoding="utf-8") as file:
                json.dump(benutzer_daten, file, indent=4)
        except (FileNotFoundError, json.JSONDecodeError):
            return HttpResponseBadRequest(
                "Fehler beim Aktualisieren der Benutzerdaten."
            )

        try:
            with open(anfragen_datei, "r", encoding="utf-8") as file:
                daten = json.load(file)
        except FileNotFoundError:
            daten = {"anfragen": []}
        except json.JSONDecodeError:
            return HttpResponseBadRequest("Fehler beim Laden der Anfragen-Datei.")

        daten["anfragen"] = [
            anfrage
            for anfrage in daten["anfragen"]
            if not (
                anfrage["username"] == username
                and anfrage["matrikelnummer"] == matrikelnummer
            )
        ]

        try:
            with open(anfragen_datei, "w", encoding="utf-8") as file:
                json.dump(daten, file, indent=4)
        except IOError:
            return HttpResponseBadRequest("Fehler beim Speichern der Anfragen-Datei.")

        return redirect("profile_page_admin")
    return HttpResponseBadRequest("Ungültige Anfrage.")


def status_upgrade(request):
    if request.method == "POST":
        benutzername = request.POST.get("benutzername")
        try:
            with open(registrierte_benutzer, "r", encoding="utf-8") as file:
                benutzer_daten = json.load(file)
            for user in benutzer_daten["users"]:
                if user["username"] == benutzername:
                    if user["status"] == "basis":
                        user["status"] = "vip"
                    elif user["status"] == "vip":
                        user["status"] = "admin"
                    break
            with open(registrierte_benutzer, "w", encoding="utf-8") as file:
                json.dump(benutzer_daten, file, indent=4)
        except (FileNotFoundError, json.JSONDecodeError):
            return HttpResponseBadRequest(
                "Fehler beim Aktualisieren der Benutzerdaten."
            )
    return redirect("profile_page_admin")


def status_downgrade(request):
    if request.method == "POST":
        benutzername = request.POST.get("benutzername")
        try:
            with open(registrierte_benutzer, "r", encoding="utf-8") as file:
                benutzer_daten = json.load(file)
            for user in benutzer_daten["users"]:
                if user["username"] == benutzername:
                    if user["status"] == "admin":
                        user["status"] = "vip"
                    elif user["status"] == "vip":
                        user["status"] = "basis"
                    break
            with open(registrierte_benutzer, "w", encoding="utf-8") as file:
                json.dump(benutzer_daten, file, indent=4)
        except (FileNotFoundError, json.JSONDecodeError):
            return HttpResponseBadRequest(
                "Fehler beim Aktualisieren der Benutzerdaten."
            )
    return redirect("profile_page_admin")


def benutzer_sperren(request):
    if request.method == "POST":
        benutzername = request.POST.get("benutzername")
        try:
            with open(registrierte_benutzer, "r", encoding="utf-8") as file:
                benutzer_daten = json.load(file)
            for user in benutzer_daten["users"]:
                if user["username"] == benutzername:
                    user["zugriff"] = False
                    break
            with open(registrierte_benutzer, "w", encoding="utf-8") as file:
                json.dump(benutzer_daten, file, indent=4)
        except (FileNotFoundError, json.JSONDecodeError):
            return HttpResponseBadRequest(
                "Fehler beim Aktualisieren der Benutzerdaten."
            )
    return redirect("profile_page_admin")


def benutzer_entsperren(request):
    if request.method == "POST":
        benutzername = request.POST.get("benutzername")
        try:
            with open(registrierte_benutzer, "r", encoding="utf-8") as file:
                benutzer_daten = json.load(file)
            for user in benutzer_daten["users"]:
                if user["username"] == benutzername:
                    user["zugriff"] = True
                    break
            with open(registrierte_benutzer, "w", encoding="utf-8") as file:
                json.dump(benutzer_daten, file, indent=4)
        except (FileNotFoundError, json.JSONDecodeError):
            return HttpResponseBadRequest(
                "Fehler beim Aktualisieren der Benutzerdaten."
            )
    return redirect("profile_page_admin")


### ab hier: reportbare Module durch Admin festlegen, Modulverwaltung  ###

@admin_berechtigung_check
def module_edit(request):
    try:
        with open(datenbank_module_editable, 'r', encoding='utf-8') as file:
            data = json.load(file)
    except Exception as e1:
        return HttpResponseBadRequest(f'Fehler beim Laden der Datei: {str(e1)}')

    if request.method == 'POST':
        module_on = {}
        module_off = {}

        for key, value in data['module_on'].items():
            if request.POST.get(f'module_on_{key}'):
                module_on[key] = value
            else:
                module_off[key] = value

        for key, value in data['module_off'].items():
            if request.POST.get(f'module_off_{key}'):
                module_on[key] = value
            else:
                module_off[key] = value

        # Sortiere die Dictionaries nach den Modulnummern
        module_on = dict(sorted(module_on.items()))
        module_off = dict(sorted(module_off.items()))

        data['module_on'] = module_on
        data['module_off'] = module_off


        try:
            with open(datenbank_module_editable, 'w', encoding='utf-8') as file:
                json.dump(data, file, indent=4, ensure_ascii=False)
        except Exception as e2:
            return HttpResponseBadRequest(f'Fehler beim Speichern der Datei: {str(e2)}')
        return redirect("module_edit")

    inhalte_json = {
        'module_on': data['module_on'],
        'module_off': data['module_off']
    }
    return render(request, 'meine_app/module_edit.html', inhalte_json)

def neues_modul_abspeichern(request):
    if request.method == 'POST':
        modulnummer = request.POST.get('modulnummer')
        modulname = request.POST.get('modulname')

        try:
            with open(datenbank_module_editable, 'r', encoding='utf-8') as file:
                data_editable = json.load(file)
        except Exception as fehler1:
            return HttpResponseBadRequest(f'Fehler beim Laden der Datei: {str(fehler1)}')

        try:
            with open(datenbank_module, 'r', encoding='utf-8') as file:
                data = json.load(file)
        except Exception as fehler2:
            return HttpResponseBadRequest(f'Fehler beim Laden der Datei: {str(fehler2)}')

        # Neues Modul in module_off von datenbank_module_editable hinzufügen
        data_editable['module_off'][modulnummer] = modulname

        # Neues Modul in module von datenbank_module hinzufügen
        data['module'][modulnummer] = modulname

        try:
            with open(datenbank_module_editable, 'w', encoding='utf-8') as file:
                json.dump(data_editable, file, indent=4, ensure_ascii=False)
        except Exception as fehler3:
            return HttpResponseBadRequest(f'Fehler beim Speichern der Datei: {str(fehler3)}')

        try:
            with open(datenbank_module, 'w', encoding='utf-8') as file:
                json.dump(data, file, indent=4, ensure_ascii=False)
        except Exception as fehler4:
            return HttpResponseBadRequest(f'Fehler beim Speichern der Datei: {str(fehler4)}')

        return redirect("module_edit")

    return HttpResponseBadRequest('Ungültige Anfrage.')


#################################
# Ab hier Profilseite eines Basis-Users bzw. VIP
#################################

def profile_page_user_view(request):
    eingeloggter_user = request.session.get("username")
    user_initiale = eingeloggter_user[0].upper()
    try:
        with open(registrierte_benutzer, "r", encoding="utf-8") as file:
            benutzer_daten = json.load(file)  # JSON-Daten laden
            for user in benutzer_daten["users"]:
                if user["username"] == eingeloggter_user:
                    matrikelnummer = user["matrikelnummer"]
                    status_angemeldeter_user = user["status"]
                    break
            else:
                matrikelnummer = None  # Falls der Benutzer nicht gefunden wurde
    except FileNotFoundError:
        benutzer_daten = {"users": []}  # Leere Liste, falls Datei nicht existiert
    except json.JSONDecodeError:
        return HttpResponseBadRequest("Fehler beim Laden der Benutzerdaten-Datei.")


    ### JSON-Datei mit Arbeitsberichten laden
    with open(arbeitsbericht_erstellen, 'r', encoding="utf-8") as file:
        daten = json.load(file)

    # Dictionary zur Speicherung der aggregierten Arbeitszeiten
    arbeitszeiten_module = {}

    # Eintraege des eingeloggten Benutzers durchsuchen und aggregieren
    for bericht in daten['arbeitsberichte']:
        if bericht['benutzername'] == eingeloggter_user:
            modul = bericht['modul']
            nettoarbeitszeit = bericht['nettoarbeitszeit']
            if modul in arbeitszeiten_module:
                arbeitszeiten_module[modul] += nettoarbeitszeit
            else:
                arbeitszeiten_module[modul] = nettoarbeitszeit

    # Gesamtsumme der Nettoarbeitszeiten berechnen
    gesamt_nettoarbeitszeit = sum(arbeitszeiten_module.values())

    # Prozentualen Anteil jedes Moduls berechnen und auf ganze Zahlen runden
    prozentualer_anteil = {}
    for modul, zeit in arbeitszeiten_module.items():
        prozentualer_anteil[modul] = round((zeit / gesamt_nettoarbeitszeit) * 100)

    # JSON-Datei mit Modulnamen laden
    with open(datenbank_module, 'r', encoding="utf-8") as file:
        module_daten = json.load(file)

    # Neues Dictionary zur Speicherung aller Werte
    alle_werte = {}
    for modul, zeit in arbeitszeiten_module.items():
        alle_werte[modul] = {
            "modulname": module_daten["module"][modul],
            "nettoarbeitszeit": zeit,
            "prozentualer_anteil": prozentualer_anteil[modul]
        }

    # Dictionary nach Keys sortieren
    alle_werte = dict(sorted(alle_werte.items()))

    content= {
        "benutzer_daten": eingeloggter_user,
        "user_initiale": user_initiale,
        "matrikelnummer": matrikelnummer,
        "status_angemeldeter_user": status_angemeldeter_user,
        "alle_werte": alle_werte,
        "gesamt_nettoarbeitszeit": gesamt_nettoarbeitszeit
    }

    return render(request, "meine_app/profile_page_user.html", content)

def status_upgrade_anfrage(request):
    if request.method == "POST":
        username = request.session.get("username")
        matrikelnummer = request.POST.get("matrikelnummer")

        neue_anfrage = {"username": username, "matrikelnummer": matrikelnummer}

        try:
            with open(anfragen_datei, "r", encoding="utf-8") as file:
                daten = json.load(file)
        except FileNotFoundError:
            daten = {"anfragen": []}
        except json.JSONDecodeError:
            return HttpResponseBadRequest("Fehler beim Laden der Anfragen-Datei.")

        daten["anfragen"].append(neue_anfrage)

        try:
            with open(anfragen_datei, "w", encoding="utf-8") as file:
                json.dump(daten, file, indent=4)
        except IOError:
            return HttpResponseBadRequest("Fehler beim Speichern der Anfragen-Datei.")

        return redirect("profile_page_user")
