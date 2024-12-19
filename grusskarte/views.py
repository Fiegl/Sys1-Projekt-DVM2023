from django.shortcuts import render
from django.http import HttpResponse

def index(request):
    def anredeGenerator(name, gender, typ, rolle):
        informell = rolle in ["Oma", "Opa"]
        anredeStart = f"Liebe{'r' if gender == 'm' else ''}"
        if informell:
            return f"{anredeStart} {rolle} {name}"
        else:
            anredeStart = f"Sehr geehrte{'r' if gender == 'm' else ''}"
            anredeStart += f" {'Herr' if gender == 'm' else 'Frau'}"
            return f"{anredeStart} {name}"

    # Standardwerte für Parameter
    name = request.GET.get("n", "Gast")
    occasion = request.GET.get("occasion", "Feier")

    adressaten = {
        "Franz": {
            "gender": "m",
            "typ": "family",
            "rolle": "Opa"
        },
        "Maria": {
            "gender": "w",
            "typ": "family",
            "rolle": "Oma"
        }
    }

    # Prüfen, ob der Name bekannt ist
    if name not in adressaten:
        return HttpResponse(f"Unbekannter Name: {name}", status=404)

    # Adressatendaten abrufen
    gender = adressaten[name]["gender"]
    typ = adressaten[name]["typ"]
    rolle = adressaten[name]["rolle"]

    # Parameter für das Template
    params = {
        "occasion": occasion,
        "anrede": anredeGenerator(name, gender, typ, rolle),
    }

    # Template-Wahl
    templates = {
        "Weihnachten": "grusskarte/spezielleWeihnachten.html",
        "Yalda": "grusskarte/spezielleYalda.html",
        "Hanukah": "grusskarte/spezielleHanukah.html"
    }

    template = templates.get(occasion, "grusskarte/generellesDesign.html")

    return render(request, template, params)




#def grusskarte_view(request):
    #return render(request, 'grusskarte/grusskarte.html')
