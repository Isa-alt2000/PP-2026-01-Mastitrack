from django.urls import path

from semaforo import views

app_name = "semaforo"

urlpatterns = [
    path("", views.panel_semaforo, name="panel"),
    path("evaluar/<str:vaca_id>/", views.evaluar_riesgo, name="evaluar"),
    path("historial/<str:vaca_id>/", views.historial_riesgo, name="historial"),
]
