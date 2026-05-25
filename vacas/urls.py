from django.urls import path

from vacas import views

app_name = "vacas"

urlpatterns = [
    path("", views.lista_vacas, name="lista"),
    path("crear/", views.crear_vaca, name="crear"),
    path("<str:vaca_id>/", views.detalle_vaca, name="detalle"),
    path("<str:vaca_id>/visita/", views.crear_visita, name="crear_visita"),
    path("api/por-lote/", views.api_vacas_lote, name="api_por_lote"),
]
