from django.urls import path
from . import views
from .views import BerichtDownloadView  # Import der Klassenbasierten View für Downloads

urlpatterns = [
    path('', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('home/', views.home_view, name='home'),
    path('logout/', views.logout_view, name='logout'),

    path('arbeitsbericht_erstellen/', views.arbeitsbericht_erstellen_view, name='arbeitsbericht_erstellen'),
    path('arbeitsbericht_speichern/', views.arbeitsbericht_speichern, name='arbeitsbericht_speichern'),

    path('arbeitsberichte_anzeigen/', views.arbeitsberichte_anzeigen_view, name='arbeitsberichte_anzeigen'),
    path('loeschen/<int:bericht_id>/', views.loesche_bericht, name='bericht_loeschen'),

    path('arbeitsberichte_download_drucken/', views.arbeitsberichte_download_drucken_view, name='arbeitsberichte_download_drucken'),
    path('download/<str:format>/<int:bericht_id>/', BerichtDownloadView.as_view(), name='bericht_herunterladen'),
    path('bericht_hochladen/', views.bericht_hochladen, name='bericht_hochladen'),
    
]
