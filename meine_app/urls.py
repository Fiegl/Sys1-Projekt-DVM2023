from django.urls import path
from . import views

urlpatterns = [
    path('', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('home/', views.home_view, name='home'),
    path('logout/', views.logout_view, name='logout'),
    path('arbeitsbericht_erstellen/', views.arbeitsbericht_erstellen_view, name='arbeitsbericht_erstellen'),
    path('arbeitsbericht_speichern/', views.arbeitsbericht_speichern, name='arbeitsbericht_speichern'),
    path('arbeitsberichte_anzeigen/', views.arbeitsberichte_anzeigen_view, name='arbeitsberichte_anzeigen'),
    path('download_drucken/', views.download_drucken_view, name='download_drucken'),
    path("bericht/<int:bericht_id>/", views.arbeitsberichte_download_drucken_view, name="arbeitsberichte_download_drucken"),
    path("bericht/<int:bericht_id>/json/", views.bericht_download_json_view, name="bericht_download_json"),
    path("bericht/<int:bericht_id>/csv/", views.bericht_download_csv_view, name="bericht_download_csv"),
