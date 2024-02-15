from django.contrib import admin
from django.urls import path

from . import views
urlpatterns = [
    path('', views.otp , name="otp"),
    path('verify/', views.sendOtp, name='send_otp'),
    path('submit/', views.verify_otp, name='verify_otp'),
    path('api/', views.user_data, name='user_data'),
    path('api-verifyid/', views.verifyid, name='verifyid'),
    path('send_email/',views.send_email_with_pdf,name="send_email"),
    path('passes/',views.passPage,name="passes"),
]
