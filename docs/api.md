# API de Sensores de Leche

API REST con autenticacion JWT para recibir lecturas automaticas de sensores de leche. Simula la integracion con dispositivos fisicos que los operadores introducen en la leche despues del ordeno.

## Autenticacion

Todos los endpoints de datos requieren un token JWT en el header `Authorization`.

### Obtener token

```
POST /api/token/
Content-Type: application/json
```

**Request:**

```json
{
    "username": "usuario",
    "password": "contraseña"
}
```

**Response (200):**

```json
{
    "token": "eyJhbGciOiJIUzI1NiIs...",
    "username": "usuario"
}
```

**Response (401):**

```json
{
    "error": "Credenciales invalidas."
}
```

El token expira a las 8 horas. Se firma con `SECRET_KEY` de Django usando HS256.

## Registrar lecturas de sensor

```
POST /api/sensores/
Content-Type: application/json
Authorization: Bearer <token>
```

**Request:**

```json
{
    "lecturas": [
        {
            "arete": "ID-ARETE",
            "conteo_celulas_somaticas": 150000,
            "ph": 6.7,
            "temperatura": 38.2,
            "conductividad_electrica": 5.1
        },
        {
            "arete": "ID_ARETE",
            "conteo_celulas_somaticas": 320000,
            "ph": 6.4,
            "temperatura": 39.1,
            "conductividad_electrica": 6.3
        }
    ]
}
```

Cada lectura se vincula automaticamente a:
- La vaca identificada por `arete`.
- La bitacora de ordeno mas reciente de esa vaca (si existe).

**Response (200):**

```json
{
    "total": 2,
    "exitosos": 2,
    "fallidos": 0,
    "resultados": [
        {
            "arete": "ID_ARETE",
            "ok": true,
            "fiable": true,
            "sensor_id": "664f...",
            "bitacora_vinculada": "664e...",
            "banderas": [
                {
                    "campo": "conductividad_electrica",
                    "nivel": "sospechoso",
                    "mensaje": "Conductividad sospechosa (5.1 mS/cm)"
                }
            ]
        },
        {
            "arete": "ID_ARETE",
            "ok": true,
            "fiable": true,
            "sensor_id": "664f...",
            "bitacora_vinculada": "664e...",
            "banderas": [
                {
                    "campo": "conteo_celulas_somaticas",
                    "nivel": "sospechoso",
                    "mensaje": "CCS sospechoso (320000 cel/mL)"
                }
            ]
        }
    ]
}
```

## Validacion y fiabilidad

La API **siempre almacena** las lecturas recibidas, incluso si los valores estan fuera de rango. A diferencia del ingreso manual (que rechaza valores invalidos), la API marca los registros con campos de fiabilidad para no perder datos de sensores que podrían tener errores de calibracion.

### Comportamiento por caso

| Caso | Se guarda | `fiable` | Banderas |
|------|-----------|----------|----------|
| Valores normales | Si | `true` | Ninguna |
| Valores en rango pero clinicamente sospechosos | Si | `true` | `sospechoso` o `alto` |
| Valores fuera de rango permitido | Si | `false` | `no_fiable` |
| Valores no numericos | No | - | Error de parseo |
| Arete no encontrado | No | - | Error de vaca |

### Rangos de referencia

| Variable | Rango permitido | Rango normal | Alerta clinica |
|----------|----------------|--------------|----------------|
| CCS (cel/mL) | 0 - 5,000,000 | 0 - 200,000 | > 200,000 sospechoso; > 400,000 alto |
| pH | 6.0 - 8.0 | 6.6 - 6.8 | < 6.4 o > 7.0 |
| Temperatura (C) | 30.0 - 42.0 | 33.0 - 38.5 | < 32 o > 39.5 |
| Conductividad (mS/cm) | 3.0 - 8.0 | 4.0 - 4.9 | > 4.9 sospechoso; > 5.15 alto |

## Campos almacenados en SensorLeche

Cada lectura recibida por la API se guarda con:

| Campo | Valor |
|-------|-------|
| `origen` | `"api"` |
| `fiable` | `true` si todos los valores estan en rango permitido, `false` si alguno no |
| `banderas_calidad` | Lista de banderas con `campo`, `nivel` y `mensaje` |

En el frontend, el origen `api` se muestra como **SENSOR**.

## Errores comunes

| Status | Causa |
|--------|-------|
| 400 | JSON invalido o campo `lecturas` vacio |
| 401 | Token no proporcionado, expirado o invalido |
