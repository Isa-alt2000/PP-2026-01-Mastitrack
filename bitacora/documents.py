import mongoengine as me

from vacas.documents import Vaca


class BitacoraOrdeno(me.Document):
    vaca = me.ReferenceField(Vaca, required=True)
    fecha_ordeno = me.DateTimeField(required=True)
    operador_id = me.StringField()
    lote = me.StringField()

    ordeno = me.DictField(default=lambda: {
        "pre_ordeno": {
            "lavado_manos": False,
            "despunte_primeros_chorros": False,
            "sellado_yodo": False,
            "secado_toalla_limpia": False,
            "fecha_pre": None,
        },
        "medicion_ordeno": {
            "colocacion_pezoneras": False,
            "verificar_vacio": False,
            "retirar_pezoneras": False,
            "fecha_med": None,
        },
        "post_ordeno": {
            "sellado_post_ordeno": False,
            "limpieza_cip": False,
            "registro_temp_tanque": False,
            "firma_operador": False,
            "fecha_post": None,
        },
    })

    metricas = me.DictField()

    meta = {"collection": "bitacoras_ordeno", "ordering": ["-fecha_ordeno"]}

    def __str__(self):
        return f"Ordeno {self.vaca.arete} - {self.fecha_ordeno}"

    def calcular_metricas(self):
        pasos_totales = 0
        pasos_cumplidos = 0
        fallas_higiene = False
        fallas_post = False

        pasos_pre = self.ordeno.get("pre_ordeno", {})
        pasos_med = self.ordeno.get("medicion_ordeno", {})
        pasos_post = self.ordeno.get("post_ordeno", {})

        campos_check = [
            "lavado_manos", "despunte_primeros_chorros",
            "sellado_yodo", "secado_toalla_limpia",
        ]
        for campo in campos_check:
            pasos_totales += 1
            if pasos_pre.get(campo):
                pasos_cumplidos += 1
            elif campo in ("lavado_manos", "sellado_yodo"):
                fallas_higiene = True

        for campo in ("colocacion_pezoneras", "verificar_vacio", "retirar_pezoneras"):
            pasos_totales += 1
            if pasos_med.get(campo):
                pasos_cumplidos += 1

        campos_post = [
            "sellado_post_ordeno", "limpieza_cip",
            "registro_temp_tanque", "firma_operador",
        ]
        for campo in campos_post:
            pasos_totales += 1
            if pasos_post.get(campo):
                pasos_cumplidos += 1
            elif campo == "sellado_post_ordeno":
                fallas_post = True

        fallas_criticas = int(fallas_higiene) + int(fallas_post)
        porcentaje = (pasos_cumplidos / pasos_totales * 100) if pasos_totales > 0 else 0

        self.metricas = {
            "pasos_cumplidos": pasos_cumplidos,
            "pasos_totales": pasos_totales,
            "porcentaje_cumplimiento": round(porcentaje, 2),
            "fallas_criticas": fallas_criticas,
            "hubo_falla_higiene": fallas_higiene,
            "hubo_falla_post_ordeno": fallas_post,
            "bitacora_completa": pasos_cumplidos == pasos_totales,
        }
        return self.metricas


class SensorLeche(me.Document):
    vaca = me.ReferenceField(Vaca, required=True)
    bitacora_ordeno = me.ReferenceField(BitacoraOrdeno)
    conteo_celulas_somaticas = me.IntField()
    ph = me.FloatField()
    temperatura = me.FloatField()
    conductividad_electrica = me.FloatField()
    fecha_medicion = me.DateTimeField(required=True)

    meta = {"collection": "sensores_leche", "ordering": ["-fecha_medicion"]}

    def __str__(self):
        return f"Sensor {self.vaca.arete} - {self.fecha_medicion}"
