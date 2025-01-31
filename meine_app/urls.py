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
    path('arbeitsberichte_loeschen/<str:bericht_id>/', views.arbeitsbericht_loeschen, name='arbeitsbericht_loeschen'),
    
   
    path('arbeitsberichte_download_drucken/', views.arbeitsberichte_download_drucken_view, name='arbeitsberichte_download_drucken'),
    path('bericht_als_json/json/<str:bericht_id>/', views.bericht_als_json, name='bericht_als_json'),
    path('bericht_als_csv/csv/<str:bericht_id>/', views.bericht_als_csv, name='bericht_als_csv'),
    path('bericht_als_xml/xml/<str:bericht_id>/', views.bericht_als_xml, name='bericht_als_xml'),
    path('bericht_hochladen/', views.bericht_hochladen, name='bericht_hochladen'),


    path('profile_page_admin/', views.profile_page_view, name='profile_page_admin'),
    path('loesche_anfrage/', views.loesche_anfrage, name='loesche_anfrage'),
    path('status_upgrade/', views.status_upgrade, name='status_upgrade'),
    path('status_downgrade/', views.status_downgrade, name='status_downgrade'),
    path('benutzer_sperren/', views.benutzer_sperren, name='benutzer_sperren'),
    path('benutzer_entsperren/', views.benutzer_entsperren, name='benutzer_entsperren'),
    
    path('module_edit/', views.module_edit, name='module_edit'),
    path('neues_modul_abspeichern/', views.neues_modul_abspeichern, name='neues_modul_abspeichern'), 

    path('profile_page_user/', views.profile_page_user_view, name='profile_page_user'),
    path('status_upgrade_anfrage/', views.status_upgrade_anfrage, name='status_upgrade_anfrage'),
    
]
