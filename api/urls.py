from django.urls import path

from api import views

app_name = "api"

urlpatterns = [
    path("token/", views.obtener_token, name="token"),
    path("sensores/", views.registrar_lecturas, name="sensores"),
]
