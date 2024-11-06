from django.urls import path
from . import views

urlpatterns = [
    path('', views.login_view, name='login'),  # Root-URL auf login_view setzen
    path('register/', views.register_view, name='register'),
    path('home/', views.home_view, name='home'),  # Home-Seite auf '/home/' verschieben
    path('logout/', views.logout_view, name='logout'),
]