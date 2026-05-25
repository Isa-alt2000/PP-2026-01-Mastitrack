# Arquitectura del Proyecto Mastitrack

## Estructura del Proyecto

```
pp-mastitis/
├── manage.py
├── requirements.txt
├── mastitis_project/          # Configuracion Django
│   ├── settings.py            # SQLite (auth) + MongoDB (dominio), Fernet key
│   ├── urls.py                # Rutas raiz con include por app
│   ├── wsgi.py / asgi.py
│
├── core/                      # Utilidades compartidas
│   ├── crypto.py              # Cifrado/descifrado Fernet (Criptografia)
│   ├── context_processors.py  # Inyecta es_admin/es_operador en templates
│   ├── views.py               # Dashboard principal
│   └── templatetags/core_tags.py  # Filtros: porcentaje, color_alerta, moneda
│
├── vacas/                     # App: gestion de vacas + visitas veterinarias
│   ├── documents.py           # Vaca, VisitaVeterinaria (costo cifrado)
│   ├── views.py               # CRUD vacas, crear visita, API por lote
│   └── urls.py
│
├── bitacora/                  # App: bitacora de ordeno + sensores de leche
│   ├── documents.py           # BitacoraOrdeno (con calcular_metricas), SensorLeche
│   ├── views.py               # CRUD bitacora, registrar sensor, API resumen
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
├── templates/                 # Templates globales + por app
│   ├── base.html              # Layout con Bootstrap 5 CDN
│   ├── navbar.html            # Navegacion segun rol (admin/operador)
│   ├── dashboard.html         # Panel general con tarjetas resumen
│   └── registration/login.html
│
└── static/
    ├── css/main.css
    └── js/main.js             # Utilidad getCookie para CSRF + fetchPost
```

## Stack Tecnologico

- **Backend**: Django 4.2 monolitico
- **Base de datos de dominio**: MongoDB via MongoEngine
- **Base de datos de autenticacion**: SQLite (django.contrib.auth)
- **Frontend**: Django Templates + Bootstrap 5 (CDN) + Chart.js
- **Cifrado**: Fernet (cryptography)
- **Inferencia**: NumPy (red neuronal con pesos ficticios)

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

| Rol           | Acceso                                                                 |
|---------------|------------------------------------------------------------------------|
| Administrador | Dashboard, Vacas (CRUD), Semaforo, Calculadora, Parametros financieros |
| Operador      | Dashboard (vista general), Vacas (solo lectura), Bitacora de ordeno    |

Los roles se gestionan mediante grupos de Django (`administrador`, `operador`) y se inyectan en cada template via el context processor `core.context_processors.user_group`.

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
Operador/Sensor registra datos de leche (SensorLeche)
        |
        v
Admin ejecuta evaluacion de riesgo (inference.py)
        |
        +---> RiesgoMastitisHistorico (resultado de la NN)
        |
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
