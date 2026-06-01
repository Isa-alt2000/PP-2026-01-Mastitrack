import mongoengine as me

from bitacora.documents import BitacoraOrdeno, SensorLeche
from vacas.documents import Vaca

NIVELES_ALERTA = ("verde", "amarillo", "rojo")


class RiesgoMastitisHistorico(me.Document):
    vaca = me.ReferenceField(Vaca, required=True)
    bitacora_ordeno = me.ReferenceField(BitacoraOrdeno)
    sensor_leche = me.ReferenceField(SensorLeche)
    fecha_evaluacion = me.DateTimeField(required=True)
    probabilidad_riesgo_cifrada = me.StringField()
    nivel_alerta_cifrado = me.StringField()
    version_modelo = me.StringField(default="rn_v1")

    _PROPS_CIFRADAS = ("probabilidad_riesgo", "nivel_alerta")

    meta = {
        "collection": "riesgo_mastitis_historico",
        "ordering": ["-fecha_evaluacion"],
    }

    def __init__(self, **kwargs):
        props = {k: kwargs.pop(k) for k in list(kwargs) if k in self._PROPS_CIFRADAS}
        super().__init__(**kwargs)
        for k, v in props.items():
            setattr(self, k, v)

    def __str__(self):
        return f"Riesgo {self.vaca.arete}: {self.nivel_alerta} ({self.probabilidad_riesgo:.2f})"

    @property
    def probabilidad_riesgo(self):
        if not self.probabilidad_riesgo_cifrada:
            return None
        from core.crypto import descifrar
        return float(descifrar(self.probabilidad_riesgo_cifrada))

    @probabilidad_riesgo.setter
    def probabilidad_riesgo(self, valor):
        if valor is None:
            self.probabilidad_riesgo_cifrada = None
            return
        from core.crypto import cifrar
        self.probabilidad_riesgo_cifrada = cifrar(str(float(valor)))

    @property
    def nivel_alerta(self):
        if not self.nivel_alerta_cifrado:
            return None
        from core.crypto import descifrar
        return descifrar(self.nivel_alerta_cifrado)

    @nivel_alerta.setter
    def nivel_alerta(self, valor):
        if valor is None:
            self.nivel_alerta_cifrado = None
            return
        from core.crypto import cifrar
        self.nivel_alerta_cifrado = cifrar(str(valor))


class EventoRiesgoOperativo(me.Document):
    vaca = me.ReferenceField(Vaca, required=True)
    bitacora_ordeno = me.ReferenceField(BitacoraOrdeno)
    sensor_leche = me.ReferenceField(SensorLeche)
    riesgo = me.ReferenceField(RiesgoMastitisHistorico)
    fecha_evento = me.DateTimeField(required=True)
    operador_id_cifrado = me.StringField()
    lote = me.StringField()
    porcentaje_cumplimiento_cifrado = me.StringField()
    fallas_criticas_cifrado = me.StringField()
    conteo_celulas_somaticas_cifrado = me.StringField()
    conductividad_electrica_cifrada = me.StringField()
    probabilidad_riesgo_cifrada = me.StringField()
    nivel_alerta_cifrado = me.StringField()

    _PROPS_CIFRADAS = (
        "operador_id", "porcentaje_cumplimiento", "fallas_criticas",
        "conteo_celulas_somaticas", "conductividad_electrica",
        "probabilidad_riesgo", "nivel_alerta",
    )

    meta = {
        "collection": "eventos_riesgo_operativo",
        "ordering": ["-fecha_evento"],
    }

    def __init__(self, **kwargs):
        props = {k: kwargs.pop(k) for k in list(kwargs) if k in self._PROPS_CIFRADAS}
        super().__init__(**kwargs)
        for k, v in props.items():
            setattr(self, k, v)

    @property
    def operador_id(self):
        if not self.operador_id_cifrado:
            return None
        from core.crypto import descifrar
        return descifrar(self.operador_id_cifrado)

    @operador_id.setter
    def operador_id(self, valor):
        if valor is None:
            self.operador_id_cifrado = None
            return
        from core.crypto import cifrar
        self.operador_id_cifrado = cifrar(str(valor))

    @property
    def porcentaje_cumplimiento(self):
        if not self.porcentaje_cumplimiento_cifrado:
            return None
        from core.crypto import descifrar
        return float(descifrar(self.porcentaje_cumplimiento_cifrado))

    @porcentaje_cumplimiento.setter
    def porcentaje_cumplimiento(self, valor):
        if valor is None:
            self.porcentaje_cumplimiento_cifrado = None
            return
        from core.crypto import cifrar
        self.porcentaje_cumplimiento_cifrado = cifrar(str(float(valor)))

    @property
    def fallas_criticas(self):
        if not self.fallas_criticas_cifrado:
            return None
        from core.crypto import descifrar
        return int(descifrar(self.fallas_criticas_cifrado))

    @fallas_criticas.setter
    def fallas_criticas(self, valor):
        if valor is None:
            self.fallas_criticas_cifrado = None
            return
        from core.crypto import cifrar
        self.fallas_criticas_cifrado = cifrar(str(int(valor)))

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
    def probabilidad_riesgo(self):
        if not self.probabilidad_riesgo_cifrada:
            return None
        from core.crypto import descifrar
        return float(descifrar(self.probabilidad_riesgo_cifrada))

    @probabilidad_riesgo.setter
    def probabilidad_riesgo(self, valor):
        if valor is None:
            self.probabilidad_riesgo_cifrada = None
            return
        from core.crypto import cifrar
        self.probabilidad_riesgo_cifrada = cifrar(str(float(valor)))

    @property
    def nivel_alerta(self):
        if not self.nivel_alerta_cifrado:
            return None
        from core.crypto import descifrar
        return descifrar(self.nivel_alerta_cifrado)

    @nivel_alerta.setter
    def nivel_alerta(self, valor):
        if valor is None:
            self.nivel_alerta_cifrado = None
            return
        from core.crypto import cifrar
        self.nivel_alerta_cifrado = cifrar(str(valor))
