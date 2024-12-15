import json, csv, uuid
import xml.etree.ElementTree as ET
from django.shortcuts import render, redirect
from django.views import View
from django.contrib.auth.hashers import make_password, check_password
from django.http import HttpResponseBadRequest, HttpResponse, JsonResponse
from datetime import datetime


# Pfade zu den JSON-Dateien
registrierte_benutzer = "/var/www/buchungssystem/db/users.json"
arbeitsbericht_erstellen = "/var/www/buchungssystem/db/arbeitsberichte.json"
datenbank_module = "/var/www/buchungssystem/db/module.json"


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
        except FileNotFoundError:
            arbeitsberichte = []

        # Arbeitsberichte für neuen Benutzer initialisieren
        arbeitsberichte.append({
            "name": username,
            "matrikelnummer": matrikelnummer,
            "berichte": {}
        })

        with open(arbeitsbericht_erstellen, "w", encoding="utf-8") as file:
            json.dump(arbeitsberichte, file, indent=4)

        # Automatisch einloggen und zur Startseite weiterleiten
        request.session["username"] = username
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
                return redirect("home")

        return render(request, "meine_app/login.html", {"error": "Ungültige Anmeldedaten oder gesperrter Account!"})
    return render(request, "meine_app/login.html")


def home_view(request):
    username = request.session.get("username")
    if not username:
        return redirect("login")
    return render(request, "meine_app/home.html", {"username": username})


def logout_view(request):
    request.session.flush()
    return redirect("login")


def arbeitsbericht_erstellen_view(request):
    try:
        with open(datenbank_module, 'r', encoding='utf-8') as file:
            module = json.load(file)['module']
    except (FileNotFoundError, json.JSONDecodeError):
        return HttpResponseBadRequest('Fehler beim Laden der Module-Datei.')
    return render(request, 'meine_app/arbeitsbericht_erstellen.html', {'module': module})


def arbeitsbericht_speichern(request):
    if request.method == "POST":
        benutzer = request.session.get("username")  # Aktueller Benutzer
        modul = request.POST.get("modul")
        berichtsname = request.POST.get("berichtsname")
        startzeit = request.POST.get("startzeit")
        endzeit = request.POST.get("endzeit")
        pausenzeit = request.POST.get("breaktime", "0")  # Optional, Standardwert 0
        kommentare = request.POST.get("kommentare", "")

        # Matrikelnummer aus der Benutzerdatei abrufen
        try:
            with open(registrierte_benutzer, "r", encoding="utf-8") as file:
                benutzer_daten = json.load(file)
            user_info = next((user for user in benutzer_daten["users"] if user["username"] == benutzer), None)
            matrikelnummer = user_info["matrikelnummer"] if user_info else None
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

        # Neue ID für den Bericht berechnen
        neue_id = max((bericht["id"] for bericht in daten["arbeitsberichte"]), default=0) + 1

        # Neuen Bericht erstellen
        neuer_bericht = {
            "name": benutzer,
            "matrikelnummer": matrikelnummer,
            "id": neue_id,
            "modul": modul,
            "berichtsname": berichtsname,
            "startzeit": startzeit,
            "endzeit": endzeit,
            "pausenzeit": pausenzeit,
            "kommentare": kommentare,
        }

        # Neuen Bericht hinzufügen
        daten["arbeitsberichte"].append(neuer_bericht)

        # Aktualisierte JSON speichern
        with open(arbeitsbericht_erstellen, "w", encoding="utf-8") as file:
            json.dump(daten, file, indent=4)

        return redirect("home")  # Nach dem Speichern zur Startseite weiterleiten

    return render(request, "meine_app/Arbeitsbericht_erstellen.html")



def arbeitsberichte_anzeigen_view(request):
    eingeloggter_user = request.session.get("username")
    if not eingeloggter_user:
        return redirect("login")

    try:
        with open(arbeitsbericht_erstellen, "r", encoding="utf-8") as file:
            daten = json.load(file)  # JSON-Daten laden

        # Berichte des eingeloggten Benutzers filtern
        eigene_berichte = [
            bericht for bericht in daten["arbeitsberichte"] if bericht["name"] == eingeloggter_user
        ]
    except FileNotFoundError:
        eigene_berichte = []  # Keine Berichte vorhanden
    except KeyError:
        return HttpResponseBadRequest("Fehler in der JSON-Struktur.")

    return render(request, "meine_app/arbeitsberichte_anzeigen.html", {"berichte": eigene_berichte})


#die Funktion loesche_bericht hat kein eigenes template

def loesche_bericht(request, bericht_id):
    if request.method == "POST":
        try:
            with open(arbeitsbericht_erstellen, "r", encoding="utf-8") as file:
                daten = json.load(file)

            eingeloggter_user = request.session.get("username")
            if not eingeloggter_user:
                return redirect("login")

            for benutzer in daten:
                if benutzer["name"] == eingeloggter_user:
                    berichte = benutzer.get("berichte", {})
                    if str(bericht_id) in berichte:
                        del berichte[str(bericht_id)]
                        break

            with open(arbeitsbericht_erstellen, "w", encoding="utf-8") as file:
                json.dump(daten, file, indent=4)

        except FileNotFoundError:
            return HttpResponseBadRequest("Datei nicht gefunden.")

        return redirect("arbeitsberichte_anzeigen")

    return HttpResponseBadRequest("Ungültige Anfrage.")


def arbeitsberichte_download_drucken_view(request):
    eingeloggter_user = request.session.get("username")
    if not eingeloggter_user:
        return redirect("login")

    try:
        with open(arbeitsbericht_erstellen, "r", encoding="utf-8") as file:
            daten = json.load(file)  # JSON-Daten laden

        # Berichte des eingeloggten Benutzers filtern
        eigene_berichte = [
            bericht for bericht in daten["arbeitsberichte"] if bericht["name"] == eingeloggter_user
        ]
    except FileNotFoundError:
        eigene_berichte = []  # Keine Berichte vorhanden
    except KeyError:
        return HttpResponseBadRequest("Fehler in der JSON-Struktur.")

    return render(request, "meine_app/arbeitsberichte_download_drucken.html", {"berichte": eigene_berichte})




#Klasse BerichtDownloadView

class BerichtDownloadView(View):
    def bericht_herunterladen(self, bericht_id):
        try:
            with open(arbeitsbericht_erstellen, "r", encoding="utf-8") as datei:
                daten = json.load(datei)
            for benutzer in daten:
                bericht = benutzer["berichte"].get(str(bericht_id))
                if bericht:
                    return bericht
        except FileNotFoundError:
            return None
        return None

    def erstelle_json(self, bericht_id):
        bericht = self.bericht_herunterladen(bericht_id)
        if not bericht:
            return HttpResponse("Bericht nicht gefunden", status=404)

        json_daten = {
            "id": bericht_id,
            "modul": bericht[0],
            "berichtsname": bericht[1],
            "startzeit": bericht[2],
            "endzeit": bericht[3],
            "pausenzeit": bericht[4],
            "arbeitszeit": bericht[5],
            "kommentare": bericht[6],
        }

        response = HttpResponse(json.dumps(json_daten, indent=4), content_type="application/json")
        response["Content-Disposition"] = f'attachment; filename="bericht_{bericht_id}.json"'
        return response

    def erstelle_csv(self, bericht_id, bericht):
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = f'attachment; filename="bericht_{bericht_id}.csv"'
        writer = csv.writer(response)
        writer.writerow(["ID", "Modul", "Berichtsname", "Startzeit", "Endzeit", "Kommentare"])
        writer.writerow([bericht_id] + bericht)
        return response

    def erstelle_xml(self, bericht_id, bericht):
        root = ET.Element("Arbeitsbericht")
        ET.SubElement(root, "ID").text = str(bericht_id)
        ET.SubElement(root, "Modul").text = bericht[0]
        ET.SubElement(root, "Berichtsname").text = bericht[1]
        ET.SubElement(root, "Startzeit").text = bericht[2]
        ET.SubElement(root, "Endzeit").text = bericht[3]
        ET.SubElement(root, "Kommentare").text = bericht[6]
        xml_str = ET.tostring(root, encoding="unicode")
        response = HttpResponse(xml_str, content_type="application/xml")
        response["Content-Disposition"] = f'attachment; filename="bericht_{bericht_id}.xml"'
        return response

    def get(self, request, bericht_id, format):
        bericht = self.bericht_herunterladen(bericht_id)
        if not bericht:
            return HttpResponse("Bericht nicht gefunden", status=404)

        if format == "json":
            return self.erstelle_json(bericht_id)
        elif format == "csv":
            return self.erstelle_csv(bericht_id, bericht)
        elif format == "xml":
            return self.erstelle_xml(bericht_id, bericht)
        else:
            return HttpResponse("Ungültiges Format", status=400)


def bericht_hochladen(request):
    if request.method == "POST" and request.FILES.get("upload_file"):
        uploaded_file = request.FILES["upload_file"]

        try:
            hochgeladene_daten = json.load(uploaded_file)

            with open(arbeitsbericht_erstellen, "r", encoding="utf-8") as file:
                bestehende_daten = json.load(file)

            for neuer_benutzer in hochgeladene_daten:
                vorhandener_benutzer = next(
                    (benutzer for benutzer in bestehende_daten if benutzer["name"] == neuer_benutzer["name"]), None
                )
                if vorhandener_benutzer:
                    vorhandener_benutzer["berichte"].update(neuer_benutzer["berichte"])
                else:
                    bestehende_daten.append(neuer_benutzer)

            with open(arbeitsbericht_erstellen, "w", encoding="utf-8") as file:
                json.dump(bestehende_daten, file, indent=4)

        except json.JSONDecodeError:
            return HttpResponseBadRequest("Die hochgeladene Datei ist keine gültige JSON-Datei.")
        except FileNotFoundError:
            return HttpResponseBadRequest("Die Arbeitsberichte-Datei wurde nicht gefunden.")

        return redirect("arbeitsberichte_download_drucken")

    return HttpResponseBadRequest("Ungültige Anfrage.")
