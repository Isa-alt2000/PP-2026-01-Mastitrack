import mongoengine as me

from bitacora.documents import BitacoraOrdeno, SensorLeche
from vacas.documents import Vaca

NIVELES_ALERTA = ("verde", "amarillo", "rojo")


class RiesgoMastitisHistorico(me.Document):
    vaca = me.ReferenceField(Vaca, required=True)
    bitacora_ordeno = me.ReferenceField(BitacoraOrdeno)
    sensor_leche = me.ReferenceField(SensorLeche)
    fecha_evaluacion = me.DateTimeField(required=True)
    probabilidad_riesgo = me.FloatField(min_value=0.0, max_value=1.0)
    nivel_alerta = me.StringField(choices=NIVELES_ALERTA)
    version_modelo = me.StringField(default="rn_v1")

    meta = {
        "collection": "riesgo_mastitis_historico",
        "ordering": ["-fecha_evaluacion"],
    }

    def __str__(self):
        return f"Riesgo {self.vaca.arete}: {self.nivel_alerta} ({self.probabilidad_riesgo:.2f})"


class EventoRiesgoOperativo(me.Document):
    vaca = me.ReferenceField(Vaca, required=True)
    bitacora_ordeno = me.ReferenceField(BitacoraOrdeno)
    sensor_leche = me.ReferenceField(SensorLeche)
    riesgo = me.ReferenceField(RiesgoMastitisHistorico)
    fecha_evento = me.DateTimeField(required=True)
    operador_id = me.StringField()
    lote = me.StringField()
    porcentaje_cumplimiento = me.FloatField()
    fallas_criticas = me.IntField(default=0)
    conteo_celulas_somaticas = me.IntField()
    conductividad_electrica = me.FloatField()
    probabilidad_riesgo = me.FloatField()
    nivel_alerta = me.StringField(choices=NIVELES_ALERTA)

    meta = {
        "collection": "eventos_riesgo_operativo",
        "ordering": ["-fecha_evento"],
    }
