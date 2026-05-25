from django.urls import path

from calculadora import views

app_name = "calculadora"

urlpatterns = [
    path("", views.panel_calculadora, name="panel"),
    path("api/perdida/", views.api_perdida_proyectada, name="api_perdida"),
    path("api/roi/", views.api_roi, name="api_roi"),
    path("api/proyeccion/", views.api_proyeccion_contagios, name="api_proyeccion"),
    path("api/prevencion-vs-reaccion/", views.api_prevencion_vs_reaccion, name="api_pvr"),
    path("parametros/", views.admin_parametros, name="admin_parametros"),
]
