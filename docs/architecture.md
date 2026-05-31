# Arquitectura del Proyecto Mastitrack

## Estructura del Proyecto

```
pp-mastitis/
├── manage.py
├── pyproject.toml
├── mastitis_project/          # Configuracion Django
│   ├── settings.py            # SQLite (auth) + MongoDB (dominio), Fernet key
│   ├── urls.py                # Rutas raiz con include por app
│   ├── wsgi.py / asgi.py
│
├── core/                      # Utilidades compartidas
│   ├── crypto.py              # Cifrado/descifrado Fernet (Criptografia)
│   ├── context_processors.py  # Inyecta es_admin/es_operador/puede_gestionar en templates
│   ├── views.py               # Dashboard principal
│   └── templatetags/core_tags.py  # Filtros: porcentaje, prob_display, color_alerta, moneda
│
├── vacas/                     # App: gestion de vacas + visitas veterinarias
│   ├── documents.py           # Vaca, VisitaVeterinaria (costo cifrado)
│   ├── views.py               # CRUD vacas, crear visita, API por lote, paginacion
│   └── urls.py
│
├── bitacora/                  # App: bitacora de ordeno + sensores de leche
│   ├── documents.py           # BitacoraOrdeno (con calcular_metricas), SensorLeche
│   ├── validators.py          # Validacion de rangos, banderas de calidad, fiabilidad
│   ├── views.py               # CRUD bitacora, registrar/editar sensor, API resumen
│   └── urls.py
│
├── semaforo/                  # App: semaforo de riesgo de mastitis
│   ├── documents.py           # RiesgoMastitisHistorico, EventoRiesgoOperativo
│   ├── inference.py           # Inferencia combinada (modelo base + entrenado)
│   ├── services.py            # Logica centralizada de evaluacion
│   ├── views.py               # Panel, evaluar riesgo via AJAX, historial
│   └── urls.py
│
├── entrenamiento/             # App: gestion de modelos de red neuronal
│   ├── documents.py           # ModeloEntrenado (MongoDB)
│   ├── views.py               # Panel, exportar CSV, cargar/activar/desactivar/eliminar modelos
│   └── urls.py
│
├── calculadora/               # App: calculadora de perdidas y ROI
│   ├── documents.py           # ParametrosFinancieros (catalogo de precios)
│   ├── calculos.py            # Perdida, prevencion, reaccion, ROI, proyeccion SIR
│   ├── views.py               # Panel con sliders, 4 endpoints JSON, admin params
│   └── urls.py
│
├── api/                       # App: API REST con JWT para sensores
│   ├── auth.py                # Generacion y verificacion de tokens JWT
│   ├── views.py               # Endpoints: obtener token, registrar lecturas
│   └── urls.py
│
├── usuarios/                  # App: gestion de usuarios y roles
│   ├── views.py               # CRUD usuarios, asignacion de roles
│   └── urls.py
│
├── templates/                 # Templates globales + por app
│   ├── base.html              # Layout con sidebar colapsable + Bootstrap 5 CDN
│   ├── sidebar.html           # Menu lateral con navegacion por rol
│   ├── footer.html            # Footer institucional
│   ├── dashboard.html         # Panel general con tarjetas resumen
│   └── registration/login.html
│
├── modelos/                   # Modelos .joblib cargados desde entrenamiento
│
├── training/                  # Sub-repo de entrenamiento (venv independiente)
│   ├── entrenar.py            # Script con clases EntrenadorKaggle/EntrenadorMastitrack
│   ├── pyproject.toml         # Dependencias de entrenamiento (pandas, scikit-learn)
│   ├── datasets/              # Datasets CSV (Kaggle + exportados de la app)
│   └── output/                # Modelos .joblib generados
│
└── static/
    ├── css/main.css           # Paleta institucional, sidebar, cards, badges
    ├── js/main.js             # CSRF, fetchPost, sidebar toggle
    └── img/                   # Logos e imagenes (mastitrack, UNRC, vacas_fondo)
```

## Stack Tecnologico

- **Backend**: Django 4.2 monolitico
- **Base de datos de dominio**: MongoDB via MongoEngine
- **Base de datos de autenticacion**: SQLite (django.contrib.auth)
- **Frontend**: Django Templates + Bootstrap 5 (CDN) + Chart.js
- **Cifrado**: Fernet (cryptography)
- **Inferencia**: NumPy + scikit-learn (modelo base + modelo entrenado via joblib)
- **Auth API**: PyJWT (tokens JWT para endpoints de sensores)
- **Gestor de dependencias**: uv

## Colecciones MongoDB

| Coleccion                  | App          | Documento MongoEngine        |
|----------------------------|--------------|------------------------------|
| vacas                      | vacas        | Vaca                         |
| visitas_veterinarias       | vacas        | VisitaVeterinaria            |
| bitacoras_ordeno           | bitacora     | BitacoraOrdeno               |
| sensores_leche             | bitacora     | SensorLeche                  |
| riesgo_mastitis_historico  | semaforo     | RiesgoMastitisHistorico      |
| eventos_riesgo_operativo   | semaforo     | EventoRiesgoOperativo        |
| parametros_financieros     | calculadora  | ParametrosFinancieros        |
| modelos_entrenados         | entrenamiento| ModeloEntrenado              |

## Roles de Usuario

| Rol           | Acceso                                                                                    |
|---------------|-------------------------------------------------------------------------------------------|
| Superadmin    | Todo el sistema, gestion de usuarios                                                      |
| Administrador | Dashboard, Vacas (CRUD), Semaforo, Calculadora, Parametros financieros, edicion de sensores |
| Operador      | Dashboard (vista general), Vacas (solo lectura), Bitacora de ordeno                       |

Los roles se gestionan mediante grupos de Django (`administrador`, `operador`) + `is_superuser` y se inyectan en cada template via el context processor `core.context_processors.user_group` que expone: `es_superadmin`, `es_admin`, `es_operador`, `puede_gestionar`, `rol_usuario`.

## Modulos y Materias Asociadas

### 1. Semaforo de Riesgo (IA + Estadistica Multivariada)

- Toma datos de `SensorLeche` y metricas de `BitacoraOrdeno`.
- Inferencia combinada: 60% modelo base (4 neuronas especializadas) + 40% modelo entrenado (.joblib). Si no hay modelo entrenado activo, usa solo el base.
- Clasifica el riesgo: verde (<0.3), amarillo (0.3-0.7), rojo (>0.7).
- La evaluacion se dispara automaticamente al registrar un sensor, al editar el ultimo sensor, y al activar/desactivar un modelo.
- Logica centralizada en `semaforo/services.py`: `evaluar_vaca()`, `hay_datos_nuevos()`, `reevaluar_todas()`.
- Guarda el resultado en `riesgo_mastitis_historico` y consolida en `eventos_riesgo_operativo`.
- Actualiza `Vaca.diagnostico_mastitis` automaticamente: rojo → `sospecha_calculada`, no rojo + descartada → limpia.

Variables de entrada (6 features normalizadas):
- Conteo de celulas somaticas (normalizado / 1,000,000)
- Conductividad electrica (normalizado / 10)
- pH (centrado en 6.0)
- Temperatura (centrada en 37.0)
- Porcentaje de incumplimiento del ordeno ((100 - %) / 100)
- Fallas criticas (normalizado / 5)

### 1b. Diagnostico de Mastitis

- Campo `diagnostico_mastitis` en `Vaca` con tres estados: `confirmado`, `sospecha_calculada`, `sospecha_descartada`.
- `sospecha_calculada` se establece automaticamente cuando el semaforo evalua como rojo.
- `sospecha_descartada` persiste hasta el siguiente escaneo de leche (se limpia si el resultado no es rojo).
- `confirmado` solo se establece manualmente (veterinario/operador) y no se sobreescribe por el modelo.
- Al confirmar o descartar, tambien se actualiza `SensorLeche.diagnostico_mastitis` del ultimo sensor (para datos de entrenamiento).
- El dashboard muestra tarjetas de vacas con diagnostico activo (confirmado y sospecha) arriba de las evaluaciones de riesgo.

### 1c. Gestion de Modelos (Entrenamiento)

- Modulo `entrenamiento` para administrar modelos de red neuronal.
- Exportacion de datos como CSV filtrable por rango de fechas (sensor + bitacora + diagnostico).
- Carga de modelos `.joblib` con validacion al subir (deserializacion, `predict_proba`, 6 features).
- Validacion al activar: si el modelo no carga correctamente, no se activa y se muestra error.
- Al activar un modelo, se re-evaluan automaticamente todas las vacas con datos de sensor.
- Historial de modelos con acciones de activar, desactivar y eliminar.

### 2. Bitacora de Ordeno (BD NoSQL + Innovacion Social)

- Registro paso a paso del proceso de ordeno (pre, medicion, post).
- Calculo automatico de metricas: pasos cumplidos, porcentaje de cumplimiento, fallas criticas.
- Registro separado de datos de sensores de leche (CCS, pH, temperatura, conductividad).
- Estructura flexible con `DictField` para los pasos del ordeno.
- Validacion de sensores en 4 capas (ver seccion dedicada).
- Campo `origen` para distinguir datos manuales vs automaticos (sensor/API).

### 2b. API de Sensores (Criptografia + BD NoSQL)

- Autenticacion JWT (`PyJWT`) con tokens de 8 horas.
- Endpoint `POST /api/sensores/` que recibe lecturas en lote.
- Cada lectura se vincula automaticamente a la vaca por arete y a su bitacora mas reciente.
- Los datos fuera de rango se almacenan con `fiable=false` (no se rechazan).
- Se generan banderas de calidad por lectura.

### 2c. Validacion de Sensores de Leche

El sistema valida los datos de sensores en 4 capas:

| Capa | Donde | Funcion |
|------|-------|---------|
| Frontend | `form_sensor.html` | Inputs con `min`, `max`, `step`, placeholders y texto de ayuda |
| Validacion server | `validators.py` | Rechaza valores fuera de rango permitido (solo ingreso manual) |
| Validacion cruzada | `validators.py` | Parseo + rango + banderas en un solo pipeline |
| Banderas de calidad | `SensorLeche.banderas_calidad` | Marca registros clinicamente sospechosos o no fiables |

Rangos de referencia:

| Variable | Rango permitido | Rango normal | Alerta clinica |
|----------|----------------|--------------|----------------|
| CCS (cel/mL) | 0 - 5,000,000 | 0 - 200,000 | > 200,000 sospechoso; > 400,000 alto |
| pH | 6.0 - 8.0 | 6.6 - 6.8 | < 6.4 o > 7.0 |
| Temperatura (C) | 30.0 - 42.0 | 33.0 - 38.5 | < 32 o > 39.5 |
| Conductividad (mS/cm) | 3.0 - 8.0 | 4.0 - 4.9 | > 4.9 sospechoso; > 5.15 alto |

Comportamiento por origen:

- **Manual**: rechaza fuera de rango (el operador debe corregir).
- **API/Sensor**: almacena siempre, marca `fiable=false` si esta fuera de rango.

### 3. Calculadora de Perdidas y ROI (Finanzas Corporativas + Ec. Diferenciales)

**Endpoints JSON (calculos en Django, no en frontend):**
- `/calculadora/api/perdida/` - Perdida proyectada por leche descartada
- `/calculadora/api/roi/` - ROI de prevencion vs reaccion
- `/calculadora/api/proyeccion/` - Proyeccion de contagios (modelo exponencial discreto)
- `/calculadora/api/prevencion-vs-reaccion/` - Comparativo de costos desglosado

**Formulas principales:**
- Perdida de leche = vacas_afectadas * dias * produccion_diaria * precio_litro
- Costo de prevencion = sellador + toallas + pruebas CMT (mensual)
- Costo de reaccion = antibioticos + veterinario + leche perdida + reemplazo (15% tasa descarte)
- ROI = (costo_reaccion - costo_prevencion) / costo_prevencion * 100
- Proyeccion contagios: I(t+1) = I(t) + I(t) * tasa_contagio (acotado a 500)

**Panel de administracion:**
- Catalogo editable de precios de insumos, costos de reaccion y valor de produccion.
- Los precios alimentan todos los calculos del modulo ROI.

### 4. Criptografia

- El costo total de visitas veterinarias e información financiera se cifra con Fernet antes de guardarse en MongoDB.
- La clave Fernet se configura via variable de entorno `FERNET_KEY`, tiene un fallback definido en `settings.py` por si no se define en el `.env`.
- Funciones `cifrar()` y `descifrar()` en `core/crypto.py`.

## Flujo de Datos Principal

```
Operador registra ordeno (BitacoraOrdeno)
        |
        v
Datos de leche (SensorLeche)
   ├── Manual: operador ingresa desde el formulario (origen=manual)
   └── Automatico: sensor envia via API JWT (origen=api)
        |
        +---> Validacion de rangos (validators.py)
        +---> Banderas de calidad (sospechoso / alto / no_fiable)
        |
        v
Evaluacion automatica (semaforo/services.py)
        |
        +---> Inferencia combinada (60% base + 40% modelo entrenado)
        +---> RiesgoMastitisHistorico (resultado)
        +---> EventoRiesgoOperativo (consolidado para analisis)
        +---> Vaca.diagnostico_mastitis (sospecha_calculada si rojo)
        |
        v
Veterinario/operador confirma o descarta (vacas/views.py)
        |
        +---> Vaca.diagnostico_mastitis (confirmado / sospecha_descartada)
        +---> SensorLeche.diagnostico_mastitis (True / False para entrenamiento)
        |
        v
Exportar datos + reentrenar (entrenamiento/ + training/)
        |
        +---> CSV con diagnostico_mastitis como label
        +---> Nuevo modelo .joblib
        +---> Cargar y activar en la app
        +---> Re-evaluacion automatica de todas las vacas
        |
        v
Calculadora consume parametros financieros + datos de riesgo
        |
        +---> Tarjetas de perdida proyectada
        +---> Grafico de proyeccion de contagios
        +---> Comparativo prevencion vs reaccion
        +---> ROI
```
