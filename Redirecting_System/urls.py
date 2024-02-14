from django.contrib import admin
from django.urls import path

from . import views
urlpatterns = [
    path("", views.automation, name="automation"),
    path('api/', views.user_data, name='user_data'),
    path('api-verifyid/', views.verifyid, name='verifyid'),
]
