# Training - Modelo de Riesgo de Mastitis

Sub-repositorio de entrenamiento de la red neuronal que utiliza Mastitrack para evaluar el riesgo de mastitis bovina. Tiene su propio entorno virtual y dependencias, separado de la webapp.

## Requisitos

- Python 3.12+
- [uv](https://docs.astral.sh/uv/)

## Instalacion

```bash
cd training
uv sync
```

## Uso

Dos modos de entrenamiento, mutuamente excluyentes:

```bash
# Entrenar con dataset publico de Kaggle (800 registros)
uv run python entrenar.py --kaggle

# Entrenar con datos exportados desde Mastitrack
uv run python entrenar.py --mastitrack
```

Genera `output/modelo_mastitis_YYYYMMDD_HHMMSS.joblib`, listo para cargar en Mastitrack desde `/entrenamiento/`.

## Estructura

```
training/
    entrenar.py              # Script con clases EntrenadorKaggle y EntrenadorMastitrack
    funcionamiento.md        # Documentacion detallada del proceso de entrenamiento
    pyproject.toml           # Dependencias (pandas, numpy, scikit-learn, joblib)
    datasets/
        cow_milk_mastitis_dataset.csv   # Dataset publico de Kaggle (800 registros)
        mastitrack_datos_*.csv          # Datos exportados desde la app
    output/
        modelo_mastitis_*.joblib        # Modelos generados (con timestamp)
```

## Modos de entrenamiento

### `--kaggle` (Dataset publico)

- Usa `datasets/cow_milk_mastitis_dataset.csv` (800 registros, 169 positivos).
- Label: columna `class1` (0=sano, 1=mastitis).
- Features de cumplimiento y fallas se rellenan con valores neutros (100%, 0) porque el dataset no los contiene.
- SCC se multiplica por 1000 (el dataset usa x10^3 cel/mL, la app usa cel/mL).

### `--mastitrack` (Datos propios)

- Usa el archivo `mastitrack_datos_*.csv` mas reciente de `datasets/`.
- Label: columna `diagnostico_mastitis` (debe existir; exportar CSV nuevo desde la app si no aparece).
- Filtra registros sin diagnostico confirmado (solo usa los que tienen 0 o 1).
- Requiere minimo 2 registros por clase para poder dividir en train/test.

## Features del modelo

El modelo recibe 6 features normalizadas, en este orden:

| # | Feature | Normalizacion | Fuente |
|---|---------|---------------|--------|
| 1 | CCS (cel/mL) | `/ 1,000,000` | Sensor de leche |
| 2 | Conductividad (mS/cm) | `/ 10.0` | Sensor de leche |
| 3 | pH | `(pH - 6.0) / 1.0` | Sensor de leche |
| 4 | Temperatura (C) | `(temp - 37.0) / 3.0` | Sensor de leche |
| 5 | Cumplimiento (%) | `(100 - %) / 100.0` | Bitacora de ordeno |
| 6 | Fallas criticas | `/ 5.0` | Bitacora de ordeno |

La normalizacion debe coincidir exactamente con la que aplica `semaforo/inference.py` en la app.

## Inferencia combinada

En la app, la prediccion final no usa solo el modelo entrenado. Se combina:

```
probabilidad = modelo_base * 0.6 + modelo_entrenado * 0.4
```

El modelo base (hardcodeado en `inference.py`) aporta gradacion entre niveles del semaforo. El modelo entrenado aporta la senal aprendida del dataset. Esto evita predicciones extremas (0% o 99.9%) que los modelos entrenados con datos limpios tienden a producir.

## Ciclo de mejora

1. Usar la app: registrar ordenos, sensores y diagnosticos de mastitis
2. Exportar CSV desde `/entrenamiento/` (incluye columna `diagnostico_mastitis`)
3. Colocar el CSV en `datasets/`
4. Ejecutar `uv run python entrenar.py --mastitrack`
5. Subir el modelo generado a la app desde `/entrenamiento/` y activarlo

Ver [funcionamiento.md](funcionamiento.md) para una explicacion detallada del proceso de entrenamiento.
