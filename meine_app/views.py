from django.http import JsonResponse
from django.shortcuts import render, redirect
from .db_utils import create_user, authenticate_user

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        if authenticate_user(username, password):
            request.session['username'] = username
            return JsonResponse({"status": "success", "redirect_url": "/home/"})
        return JsonResponse({"status": "error", "message": "Invalid credentials"}, status=401)
    return render(request, 'meine_app/login.html')

def register_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        success, message = create_user(username, password)
        if success:
            request.session['username'] = username
            return JsonResponse({"status": "success", "redirect_url": "/home/"})
        return JsonResponse({"status": "error", "message": message}, status=400)
    return render(request, 'meine_app/register.html')


def home_view(request):
    if 'username' not in request.session:
        return redirect('login')  # Zur Login-Seite weiterleiten, wenn der Benutzer nicht eingeloggt ist
    return render(request, 'meine_app/home.html', {'username': request.session['username']})


def logout_view(request):
    # Session löschen
    request.session.flush()
    # Zur Login-Seite weiterleiten
    return redirect('login')

# Create your views here.
