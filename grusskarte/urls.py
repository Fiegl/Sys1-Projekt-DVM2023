from django.urls import path
from . import views

urlpatterns = [
    path('', views.index),
    path('grusskarte/', views.grusskarte_view, name='grusskarte'),

]
