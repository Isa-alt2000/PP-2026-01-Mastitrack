from django.urls import path

from entrenamiento import views

app_name = "entrenamiento"

urlpatterns = [
    path("", views.panel, name="panel"),
    path("exportar/", views.exportar_csv, name="exportar_csv"),
    path("cargar/", views.cargar_modelo, name="cargar_modelo"),
    path("activar/<str:modelo_id>/", views.activar_modelo, name="activar_modelo"),
    path("desactivar/<str:modelo_id>/", views.desactivar_modelo, name="desactivar_modelo"),
    path("eliminar/<str:modelo_id>/", views.eliminar_modelo, name="eliminar_modelo"),
]
