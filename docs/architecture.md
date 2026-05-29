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
│   ├── inference.py           # Red neuronal simulada (6->4->1, sigmoide)
│   ├── views.py               # Panel, evaluar riesgo via AJAX, historial
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
- **Inferencia**: NumPy (red neuronal con pesos ficticios)
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
- Ejecuta inferencia con una red neuronal de una capa oculta (6 entradas -> 4 neuronas -> 1 salida sigmoide).
- Clasifica el riesgo: verde (<0.3), amarillo (0.3-0.7), rojo (>0.7).
- Guarda el resultado en `riesgo_mastitis_historico`.
- Consolida variables en `eventos_riesgo_operativo` para analisis posterior.

Variables de entrada de la red neuronal:
- Conteo de celulas somaticas (normalizado / 1,000,000)
- Conductividad electrica (normalizado / 10)
- pH (centrado en 6.0)
- Temperatura (centrada en 37.0)
- Porcentaje de incumplimiento del ordeno
- Fallas criticas (normalizado / 5)

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
Admin ejecuta evaluacion de riesgo (inference.py)
        |
        +---> RiesgoMastitisHistorico (resultado de la NN)
        +---> EventoRiesgoOperativo (consolidado para analisis)
        |
        v
Calculadora consume parametros financieros + datos de riesgo
        |
        +---> Tarjetas de perdida proyectada
        +---> Grafico de proyeccion de contagios
        +---> Comparativo prevencion vs reaccion
        +---> ROI
```
