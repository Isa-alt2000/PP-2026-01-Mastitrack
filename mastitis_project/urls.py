from django.contrib import admin
from django.urls import include, path

from core.views import dashboard

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("django.contrib.auth.urls")),
    path("", dashboard, name="dashboard"),
    path("vacas/", include("vacas.urls")),
    path("semaforo/", include("semaforo.urls")),
    path("bitacora/", include("bitacora.urls")),
    path("calculadora/", include("calculadora.urls")),
    path("usuarios/", include("usuarios.urls")),
    path("api/", include("api.urls")),
    path("entrenamiento/", include("entrenamiento.urls")),
]
