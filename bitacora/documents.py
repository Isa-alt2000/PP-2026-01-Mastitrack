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


ORIGENES_SENSOR = ("manual", "api")


class SensorLeche(me.Document):
    vaca = me.ReferenceField(Vaca, required=True)
    bitacora_ordeno = me.ReferenceField(BitacoraOrdeno)
    conteo_celulas_somaticas_cifrado = me.StringField()
    ph_cifrado = me.StringField()
    temperatura_cifrada = me.StringField()
    conductividad_electrica_cifrada = me.StringField()
    diagnostico_mastitis_cifrado = me.StringField()
    fecha_medicion = me.DateTimeField(required=True)
    origen = me.StringField(choices=ORIGENES_SENSOR, default="manual")
    fiable = me.BooleanField(default=True)
    banderas_calidad = me.ListField(me.DictField())

    _PROPS_CIFRADAS = (
        "conteo_celulas_somaticas", "ph", "temperatura",
        "conductividad_electrica", "diagnostico_mastitis",
    )

    meta = {"collection": "sensores_leche", "ordering": ["-fecha_medicion"]}

    def __init__(self, **kwargs):
        props = {k: kwargs.pop(k) for k in list(kwargs) if k in self._PROPS_CIFRADAS}
        super().__init__(**kwargs)
        for k, v in props.items():
            setattr(self, k, v)

    def __str__(self):
        return f"Sensor {self.vaca.arete} - {self.fecha_medicion}"

    @property
    def conteo_celulas_somaticas(self):
        if not self.conteo_celulas_somaticas_cifrado:
            return None
        from core.crypto import descifrar
        return int(descifrar(self.conteo_celulas_somaticas_cifrado))

    @conteo_celulas_somaticas.setter
    def conteo_celulas_somaticas(self, valor):
        if valor is None:
            self.conteo_celulas_somaticas_cifrado = None
            return
        from core.crypto import cifrar
        self.conteo_celulas_somaticas_cifrado = cifrar(str(int(valor)))

    @property
    def ph(self):
        if not self.ph_cifrado:
            return None
        from core.crypto import descifrar
        return float(descifrar(self.ph_cifrado))

    @ph.setter
    def ph(self, valor):
        if valor is None:
            self.ph_cifrado = None
            return
        from core.crypto import cifrar
        self.ph_cifrado = cifrar(str(float(valor)))

    @property
    def temperatura(self):
        if not self.temperatura_cifrada:
            return None
        from core.crypto import descifrar
        return float(descifrar(self.temperatura_cifrada))

    @temperatura.setter
    def temperatura(self, valor):
        if valor is None:
            self.temperatura_cifrada = None
            return
        from core.crypto import cifrar
        self.temperatura_cifrada = cifrar(str(float(valor)))

    @property
    def conductividad_electrica(self):
        if not self.conductividad_electrica_cifrada:
            return None
        from core.crypto import descifrar
        return float(descifrar(self.conductividad_electrica_cifrada))

    @conductividad_electrica.setter
    def conductividad_electrica(self, valor):
        if valor is None:
            self.conductividad_electrica_cifrada = None
            return
        from core.crypto import cifrar
        self.conductividad_electrica_cifrada = cifrar(str(float(valor)))

    @property
    def diagnostico_mastitis(self):
        if not self.diagnostico_mastitis_cifrado:
            return None
        from core.crypto import descifrar
        val = descifrar(self.diagnostico_mastitis_cifrado)
        if val == "True":
            return True
        elif val == "False":
            return False
        return None

    @diagnostico_mastitis.setter
    def diagnostico_mastitis(self, valor):
        if valor is None:
            self.diagnostico_mastitis_cifrado = None
            return
        from core.crypto import cifrar
        self.diagnostico_mastitis_cifrado = cifrar(str(bool(valor)))
