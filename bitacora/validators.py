RANGOS = {
    "conteo_celulas_somaticas": {"min": 0, "max": 5_000_000, "step": 1},
    "ph": {"min": 6.0, "max": 8.0, "step": 0.01},
    "temperatura": {"min": 30.0, "max": 42.0, "step": 0.1},
    "conductividad_electrica": {"min": 3.0, "max": 8.0, "step": 0.1},
}

LABELS = {
    "conteo_celulas_somaticas": "Conteo de celulas somaticas",
    "ph": "pH",
    "temperatura": "Temperatura",
    "conductividad_electrica": "Conductividad electrica",
}


def validar_rango(datos):
    errores = {}
    for campo, limites in RANGOS.items():
        valor = datos.get(campo)
        if valor is None:
            errores[campo] = f"{LABELS[campo]} es requerido."
            continue
        if valor < limites["min"] or valor > limites["max"]:
            errores[campo] = (
                f"{LABELS[campo]} debe estar entre "
                f"{limites['min']} y {limites['max']}."
            )
    return errores


def generar_banderas(datos):
    banderas = []
    ccs = datos.get("conteo_celulas_somaticas")
    ph = datos.get("ph")
    temp = datos.get("temperatura")
    ce = datos.get("conductividad_electrica")

    if ccs is not None:
        if ccs > 400_000:
            banderas.append({"campo": "conteo_celulas_somaticas", "nivel": "alto", "mensaje": f"CCS alto ({ccs} cel/mL)"})
        elif ccs > 200_000:
            banderas.append({"campo": "conteo_celulas_somaticas", "nivel": "sospechoso", "mensaje": f"CCS sospechoso ({ccs} cel/mL)"})

    if ph is not None:
        if ph < 6.4 or ph > 7.0:
            banderas.append({"campo": "ph", "nivel": "alto", "mensaje": f"pH fuera de rango normal ({ph})"})
        elif ph < 6.6 or ph > 6.8:
            banderas.append({"campo": "ph", "nivel": "sospechoso", "mensaje": f"pH ligeramente fuera de lo normal ({ph})"})

    if temp is not None:
        if temp < 32.0 or temp > 39.5:
            banderas.append({"campo": "temperatura", "nivel": "alto", "mensaje": f"Temperatura atipica ({temp} C)"})
        elif temp < 33.0 or temp > 38.5:
            banderas.append({"campo": "temperatura", "nivel": "sospechoso", "mensaje": f"Temperatura ligeramente fuera de lo normal ({temp} C)"})

    if ce is not None:
        if ce > 5.15:
            banderas.append({"campo": "conductividad_electrica", "nivel": "alto", "mensaje": f"Conductividad alta ({ce} mS/cm)"})
        elif ce > 4.9:
            banderas.append({"campo": "conductividad_electrica", "nivel": "sospechoso", "mensaje": f"Conductividad sospechosa ({ce} mS/cm)"})
        elif ce < 4.0:
            banderas.append({"campo": "conductividad_electrica", "nivel": "sospechoso", "mensaje": f"Conductividad baja ({ce} mS/cm)"})

    return banderas


def parsear_datos_sensor(raw):
    datos = {}
    errores_parseo = {}
    campos_int = {"conteo_celulas_somaticas"}
    campos_float = {"ph", "temperatura", "conductividad_electrica"}

    for campo in campos_int:
        val = raw.get(campo)
        if val is None or val == "":
            datos[campo] = None
            continue
        try:
            datos[campo] = int(val)
        except (ValueError, TypeError):
            errores_parseo[campo] = f"{LABELS[campo]}: valor no numerico."

    for campo in campos_float:
        val = raw.get(campo)
        if val is None or val == "":
            datos[campo] = None
            continue
        try:
            datos[campo] = float(val)
        except (ValueError, TypeError):
            errores_parseo[campo] = f"{LABELS[campo]}: valor no numerico."

    return datos, errores_parseo


def evaluar_fiabilidad(datos):
    problemas = []
    for campo, limites in RANGOS.items():
        valor = datos.get(campo)
        if valor is None:
            problemas.append({"campo": campo, "nivel": "no_fiable", "mensaje": f"{LABELS[campo]} ausente."})
            continue
        if valor < limites["min"] or valor > limites["max"]:
            problemas.append({
                "campo": campo,
                "nivel": "no_fiable",
                "mensaje": f"{LABELS[campo]} fuera de rango permitido ({valor}).",
            })
    fiable = len(problemas) == 0
    return fiable, problemas


def validar_sensor_completo(raw):
    datos, errores = parsear_datos_sensor(raw)
    if errores:
        return None, errores, []
    errores_rango = validar_rango(datos)
    if errores_rango:
        return datos, errores_rango, []
    banderas = generar_banderas(datos)
    return datos, {}, banderas


def validar_sensor_api(raw):
    datos, errores_parseo = parsear_datos_sensor(raw)
    if errores_parseo:
        return None, errores_parseo, [], False
    fiable, problemas_fiabilidad = evaluar_fiabilidad(datos)
    campos_no_fiables = {p["campo"] for p in problemas_fiabilidad}
    banderas_clinicas = [b for b in generar_banderas(datos) if b["campo"] not in campos_no_fiables]
    banderas = problemas_fiabilidad + banderas_clinicas
    return datos, {}, banderas, fiable
