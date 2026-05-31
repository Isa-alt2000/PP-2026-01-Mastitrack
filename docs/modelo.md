# Modelo de Inferencia de Riesgo de Mastitis

## Implementacion actual

El modulo `semaforo/inference.py` utiliza un sistema de **inferencia combinada**:

1. **Modelo base**: Red neuronal hardcodeada con 4 neuronas especializadas. Siempre se ejecuta y aporta gradacion (verde → amarillo → rojo).
2. **Modelo entrenado** (.joblib): Modelo scikit-learn cargado desde `/modelos/`. Aporta la senal aprendida del dataset.

Cuando hay modelo entrenado activo, la prediccion final es:

```
probabilidad = modelo_base * 0.6 + modelo_entrenado * 0.4
```

Esto resuelve el problema de que los modelos entrenados con datasets limpios (como el de Kaggle) producen probabilidades extremas (0% o 99.9%) sin zona intermedia. El modelo base aporta la gradacion necesaria para el sistema de semaforo.

### Arquitectura del modelo base

Red neuronal de una capa oculta (feedforward) con 4 neuronas especializadas:

```
Entrada (6 features) -> Capa oculta (4 neuronas, sigmoide) -> Salida (1 neurona, sigmoide)
```

Cada neurona detecta un tipo de anomalia:
- Neurona 0: CCS elevado (indicador principal de infeccion)
- Neurona 1: Conductividad + pH elevados (cambios por infeccion)
- Neurona 2: Temperatura elevada (fiebre/inflamacion)
- Neurona 3: Fallas de protocolo de ordeno (riesgo operativo)

Los biases estan calibrados para que valores normales mantengan las neuronas inactivas.

### Features de entrada (6 features)

Cada feature se normaliza antes de pasar al modelo:

| Feature | Normalizacion | Fuente |
|---------|---------------|--------|
| CCS (cel/mL) | `/ 1,000,000` | SensorLeche |
| Conductividad (mS/cm) | `/ 10.0` | SensorLeche |
| pH | `(pH - 6.0) / 1.0` | SensorLeche |
| Temperatura (C) | `(temp - 37.0) / 3.0` | SensorLeche |
| Cumplimiento (%) | `(100 - %) / 100.0` | BitacoraOrdeno.metricas |
| Fallas criticas | `/ 5.0` | BitacoraOrdeno.metricas |

Cuando no hay bitacora asociada, se usan valores neutros: cumplimiento=100%, fallas=0.

### Umbrales de clasificacion

| Probabilidad | Nivel |
|-------------|-------|
| < 0.30 | Verde |
| 0.30 - 0.69 | Amarillo |
| >= 0.70 | Rojo |

## Flujo de entrenamiento e integracion

### 1. Exportar datos desde la app

Desde el modulo **Entrenamiento** (`/entrenamiento/`), exportar un CSV con los datos recolectados. El CSV contiene:

```
arete, nombre, lote, estado_salud, conteo_celulas_somaticas,
conductividad_electrica, ph, temperatura, porcentaje_cumplimiento,
fallas_criticas, diagnostico_mastitis, fecha_medicion
```

Se puede filtrar por rango de fechas. El campo `diagnostico_mastitis` (1=confirmada, 0=descartada, vacio=sin evaluar) es el label para entrenamiento.

### 2. Entrenar externamente

El entrenamiento se realiza en la carpeta `training/` con su propio entorno virtual:

```bash
cd training
uv sync
uv run python entrenar.py --kaggle      # Dataset publico de Kaggle
uv run python entrenar.py --mastitrack  # Datos exportados de la app
```

El script usa dos clases segun la fuente de datos:
- `EntrenadorKaggle`: usa `class1` como label, valores neutros para cumplimiento/fallas.
- `EntrenadorMastitrack`: usa `diagnostico_mastitis` como label, filtra registros sin diagnostico.

El modelo generado se guarda en `training/output/modelo_mastitis_YYYYMMDD_HHMMSS.joblib`.

Ver [training/funcionamiento.md](../training/funcionamiento.md) para una explicacion detallada del proceso.

### 3. Cargar el modelo en la app

Desde el modulo **Entrenamiento** (`/entrenamiento/`):

1. Seleccionar el archivo `.joblib`
2. Asignarle un nombre descriptivo
3. Hacer clic en "Cargar Modelo" (se valida que el archivo sea un modelo valido con `predict_proba` y 6 features)
4. Hacer clic en "Activar" (se valida nuevamente, y se re-evaluan todas las vacas con datos de sensor)

Si la validacion falla (incompatibilidad de numpy, modelo corrupto, etc.), se muestra un error y el modelo no se guarda/activa.

### 4. Evaluacion automatica

La evaluacion de riesgo se dispara automaticamente en varios puntos:

| Evento | Que pasa |
|--------|----------|
| Registrar sensor | Se evalua la vaca inmediatamente |
| Editar ultimo sensor | Se re-evalua con los valores actualizados |
| Activar modelo | Se re-evaluan todas las vacas con datos de sensor |
| Desactivar/eliminar modelo activo | Se re-evaluan con el modelo base |
| Visitar panel semaforo | Se detectan vacas con datos nuevos o modelo distinto |

Toda la logica esta centralizada en `semaforo/services.py`.

### 5. Versionamiento automatico

- Cada modelo cargado se registra en MongoDB (`modelos_entrenados`)
- Al activar un modelo nuevo, el sistema re-evalua todas las vacas y muestra cuantas fueron actualizadas
- El historial de riesgo conserva la version del modelo usado en cada evaluacion

### 6. Estructura de archivos

```
modelos/                          # Modelos .joblib cargados
    rn_v0.1_20260531_024254.joblib

semaforo/
    inference.py                  # Inferencia combinada (base + entrenado)
    services.py                   # Logica centralizada de evaluacion
    documents.py                  # RiesgoMastitisHistorico, EventoRiesgoOperativo
    views.py                      # Panel y endpoint AJAX (usan services.py)

entrenamiento/
    __init__.py
    documents.py                  # ModeloEntrenado (MongoDB)
    views.py                      # Panel, exportar CSV, cargar/activar/desactivar/eliminar
    urls.py

training/                         # Sub-repo de entrenamiento (venv independiente)
    entrenar.py                   # EntrenadorKaggle / EntrenadorMastitrack
    pyproject.toml
    datasets/                     # CSVs de entrenamiento
    output/                       # Modelos generados
```

## Consideraciones sobre el modelo inicial y estrategia de mejora continua

### Precision del modelo inicial

El modelo entrenado con el dataset publico (`cow_milk_mastitis_dataset.csv`, 800 registros) alcanza una precision del 100% con separacion perfecta entre clases. Esto se debe a que el dataset es de origen controlado/laboratorio, donde los indicadores clinicos (CCS, temperatura, pH, conductividad) presentan rangos claramente diferenciados entre vacas sanas y con mastitis, sin solapamiento entre clases.

| Indicador | Media sano | Media mastitis |
|-----------|-----------|---------------|
| CCS (x10³ cel/mL) | 148 | 598 |
| Temperatura (°C) | 35.5 | 38.0 |
| pH | 6.65 | 7.11 |
| Conductividad (mS/cm) | 4.69 | 6.78 |

Esta separacion tan limpia **no es representativa de condiciones reales de campo**, donde existen:

- **Mastitis subclinica**: CCS elevado sin sintomas visibles, con valores intermedios que no caen claramente en ninguna clase
- **Variabilidad ambiental**: estres calorico, etapa de lactancia, alimentacion y otros factores que alteran los indicadores sin implicar enfermedad
- **Ruido en mediciones**: sensores con calibracion variable, registros manuales con errores de operador
- **Casos de transicion**: vacas que evolucionan de sano a enfermo gradualmente

### Justificacion del enfoque

El modelo inicial con el dataset publico cumple la funcion de **baseline funcional**: demuestra que el flujo completo de inferencia (sensor → normalizacion → modelo → semaforo) opera correctamente de extremo a extremo. No pretende ser el modelo definitivo de produccion.

El sistema esta disenado con un **ciclo de mejora continua**:

1. **Recoleccion**: la app acumula datos reales de campo (sensores de leche, bitacoras de ordeno, estados clinicos registrados por operadores)
2. **Exportacion**: el modulo de entrenamiento permite descargar estos datos como CSV filtrados por fecha
3. **Reentrenamiento externo**: se entrena un nuevo modelo con los datos reales, que contendran la complejidad y ruido del entorno productivo
4. **Recarga**: el modelo reentrenado se sube a la app y se activa, reemplazando al anterior
5. **Trazabilidad**: cada evaluacion queda vinculada a la version del modelo que la genero

A medida que se acumulen datos reales del tambo, la matriz de confusion reflejara la complejidad esperada (falsos positivos, falsos negativos, casos ambiguos), y los umbrales de clasificacion podran recalibrarse segun la distribucion real de probabilidades.

### Features de cumplimiento y fallas criticas

El dataset publico no contiene datos de cumplimiento de protocolo de ordeno ni fallas criticas. Durante el entrenamiento inicial, estas dos features se rellenan con valores neutros (cumplimiento=100%, fallas=0), lo que hace que el modelo no les asigne peso.

Cuando se entrene con datos exportados de la app, estas features contendran valores reales provenientes de la bitacora de ordeno, permitiendo que el modelo aprenda correlaciones entre malas practicas de higiene y riesgo de mastitis — un factor operativo que complementa los indicadores clinicos del sensor.

## Limitaciones conocidas del modelo Kaggle

El dataset de Kaggle tiene rangos de temperatura de leche (34-37°C para sanas, 37-39°C para mastitis) que pueden no coincidir con las condiciones del entorno productivo del usuario. El modelo trata temperaturas >37.5°C como fuertemente indicativas de mastitis.

La inferencia combinada (60% base + 40% entrenado) mitiga este problema, pero la solucion definitiva es reentrenar con datos propios del tambo.

| Escenario | Solo base | Solo Kaggle | Combinada |
|-----------|-----------|-------------|-----------|
| Sana tipica (CCS=150k, T=37.5) | 19.2% verde | 0.9% | 11.9% verde |
| CCS 300k solo | 25.9% verde | 29.5% | 27.3% verde |
| Sospechosa leve | 32.6% amarillo | 100.0% | 59.6% amarillo |
| Mastitis clara | 78.4% rojo | 100.0% | 87.0% rojo |
| Mastitis severa | 89.3% rojo | 100.0% | 93.5% rojo |
