# Calculadora de Perdidas y ROI

Modulo de simulacion financiera que permite a los administradores estimar el impacto economico de la mastitis bovina y comparar los costos de prevencion frente a los de reaccion. Todas las formulas se alimentan de parametros financieros configurables con historial de trazabilidad.

## Acceso

- **Ruta:** `/calculadora/`
- **Permisos:** Solo superadmin y grupo `administrador` (decorador `requiere_gestion`)
- **Modulo Django:** `calculadora`

## Arquitectura del modulo

```
calculadora/
    calculos.py       # Funciones de calculo (formulas)
    documents.py      # Modelo ParametrosFinancieros (MongoDB)
    views.py          # Vistas del panel y APIs internas
    urls.py           # Rutas
templates/calculadora/
    panel.html            # Panel principal con sliders, graficos y desgloses
    admin_parametros.html # Gestion de parametros con historial
```

## Parametros financieros

Todos los calculos dependen de un conjunto de parametros almacenados en la coleccion `parametros_financieros` de MongoDB. Los parametros vigentes son siempre el documento mas reciente (ordenado por `-fecha_actualizacion`).

### Estructura del documento

| Campo | Tipo | Descripcion |
|-------|------|-------------|
| `fecha_actualizacion` | DateTime | Fecha y hora del registro |
| `modificado_por` | String | Nombre del usuario que registro la entrada |
| `precios_insumos` | Dict | Precios unitarios de insumos de prevencion |
| `costos_reaccion` | Dict | Costos unitarios de tratamiento reactivo |
| `valor_produccion` | Dict | Parametros de produccion lechera |

### Valores por defecto

**Precios de insumos (`precios_insumos`)**

| Clave | Default | Unidad |
|-------|---------|--------|
| `sellador_yodo_litro` | 120.50 | $/litro |
| `toallas_paquete` | 85.00 | $/paquete (100 uds) |
| `prueba_cmt` | 45.00 | $/prueba |

**Costos de reaccion (`costos_reaccion`)**

| Clave | Default | Unidad |
|-------|---------|--------|
| `precio_promedio_antibiotico` | 850.00 | $/tratamiento |
| `costo_promedio_consulta_vet` | 600.00 | $/consulta |
| `costo_reemplazo_vaca` | 35,000.00 | $/vaca |

**Valor de produccion (`valor_produccion`)**

| Clave | Default | Unidad |
|-------|---------|--------|
| `precio_venta_litro_leche` | 11.50 | $/litro |
| `produccion_promedio_vaca_dia` | 25.0 | litros/vaca/dia |

### Historial y trazabilidad

Cada modificacion de parametros crea un **nuevo documento** en lugar de editar el existente. Esto genera un historial completo de cambios. El documento mas reciente es el vigente; los anteriores se conservan como referencia.

Ruta de administracion: `/calculadora/parametros/`

## Sliders de simulacion

El panel tiene 3 controles deslizantes que alimentan todos los calculos:

| Control | Rango | Default | Descripcion |
|---------|-------|---------|-------------|
| Dias sin atencion | 1 - 30 | 7 | Dias que pasan sin atender la alerta |
| Vacas afectadas | 1 - total activas | 3 (o total si < 3) | Numero de vacas enfermas |
| Total del hato | 1 - total activas | Total activas | Tamano del hato para calculos de prevencion |
| Incluir riesgo de descarte | checkbox | desactivado | Suma el costo de reemplazo (15%) al calculo de ROI, costo de reaccion y desglose |

Los valores maximos de "Vacas afectadas" y "Total del hato" se vinculan dinamicamente a `Vaca.objects(activa=True).count()`.

Los sliders actualizan las etiquetas en tiempo real (evento `input`), pero los calculos y graficos solo se disparan al soltar el slider (evento `change`) para evitar llamadas excesivas a las APIs.

## Formulas

### 1. Perdida proyectada

Estima la perdida economica por no atender una alerta de mastitis. Asume que cada vaca enferma pierde el 100% de su produccion durante el periodo.

```
litros_descartados = vacas_afectadas * dias * produccion_promedio_vaca_dia

perdida_leche = litros_descartados * precio_venta_litro_leche
```

**Ejemplo:** 3 vacas, 7 dias, 25 lt/dia, $11.50/lt:
```
litros = 3 * 7 * 25 = 525 lt
perdida = 525 * 11.50 = $6,037.50
```

**API:** `GET /calculadora/api/perdida/?dias=7&vacas=3`

**Retorna:**

```json
{
    "dias": 7,
    "vacas_afectadas": 3,
    "litros_descartados": 525.0,
    "perdida_leche": 6037.5
}
```

### 2. Costo de prevencion (mensual)

Calcula el costo mensual de mantener un programa de prevencion de mastitis.

**Constantes fijas:**
- Ordenos por mes: 60 (2 ordenos/dia x 30 dias)
- Dosis de sellador por ordeno: 0.005 litros
- Toallas por paquete: 100 unidades
- Pruebas CMT por mes: 2 por vaca

```
costo_sellador = precio_sellador_litro * vacas_total * ordenos_mes * 0.005

costo_toallas = precio_toallas_paquete * (vacas_total * ordenos_mes / 100)

costo_cmt = precio_prueba_cmt * vacas_total * 2

total_prevencion = costo_sellador + costo_toallas + costo_cmt
```

**Ejemplo:** 50 vacas, valores default:
```
sellador  = 120.50 * 50 * 60 * 0.005 = $1,807.50
toallas   = 85.00 * (50 * 60 / 100)  = $2,550.00
cmt       = 45.00 * 50 * 2           = $4,500.00
total     = $8,857.50
```

### 3. Costo de reaccion

Calcula el costo de reaccionar ante un brote de mastitis. Incluye 4 componentes.

**Constantes fijas:**
- Dias de tratamiento: 7
- Tasa de descarte: 15% (probabilidad de que una vaca enferma sea dada de baja)

```
costo_antibiotico = precio_antibiotico * vacas_enfermas

costo_veterinario = costo_consulta_vet * vacas_enfermas

leche_perdida = vacas_enfermas * 7 * produccion_promedio_vaca_dia * precio_litro

costo_reemplazo = costo_reemplazo_vaca * vacas_enfermas * 0.15

total_reaccion = costo_antibiotico + costo_veterinario + leche_perdida + costo_reemplazo
```

**Ejemplo:** 5 vacas enfermas, valores default:
```
antibiotico  = 850.00 * 5                   = $4,250.00
veterinario  = 600.00 * 5                   = $3,000.00
leche        = 5 * 7 * 25 * 11.50           = $10,062.50
reemplazo    = 35,000.00 * 5 * 0.15         = $26,250.00
total        = $43,562.50
```

**API:** `GET /calculadora/api/prevencion-vs-reaccion/?vacas_total=50&vacas_enfermas=5`

**Retorna:**

```json
{
    "prevencion": {
        "costo_sellador": 1807.5,
        "costo_toallas": 2550.0,
        "costo_cmt": 4500.0,
        "total_prevencion": 8857.5
    },
    "reaccion": {
        "costo_antibiotico": 4250.0,
        "costo_veterinario": 3000.0,
        "leche_perdida": 10062.5,
        "costo_reemplazo": 26250.0,
        "total_reaccion": 43562.5
    }
}
```

### 4. ROI de prevencion

Calcula el retorno de inversion comparando dos escenarios: no prevenir (pagar el costo total de reaccion) vs prevenir (pagar prevencion + tratamiento de los casos residuales que la prevencion no evita).

**Efectividad de prevencion:** Se asume un 70% de efectividad. El 30% de los casos de mastitis aun ocurren a pesar de la prevencion y generan costos de tratamiento.

**Costo de reemplazo:** Excluido del calculo base. Se puede incluir opcionalmente desde la interfaz.

```
costo_evitable = costo_antibiotico + costo_veterinario + leche_perdida

costo_sin_prevencion = costo_evitable

costo_residual = costo_evitable * (1 - 0.70)

costo_con_prevencion = total_prevencion + costo_residual

ahorro = costo_sin_prevencion - costo_con_prevencion

ROI = (ahorro / costo_con_prevencion) * 100
```

**Ejemplo:** 50 vacas totales, 5 enfermas, 30 dias de simulacion:
```
costo_evitable     = 4,250 + 3,000 + 10,062.50 = $17,312.50
costo_residual     = 17,312.50 * 0.30           = $5,193.75
costo_con_prev     = 8,857.50 + 5,193.75        = $14,051.25
ahorro             = 17,312.50 - 14,051.25      = $3,261.25
ROI                = (3,261.25 / 14,051.25) * 100 = 23.2%
```

Un ROI positivo indica que la prevencion es mas economica que la reaccion. El panel muestra ademas un banner con la ganancia por peso invertido: "Ganas $X por cada $1 invertido en prevencion".

**API:** `GET /calculadora/api/roi/?vacas_total=50&vacas_enfermas=5&dias=30`

**Retorna:**

```json
{
    "prevencion": { "...desglose..." },
    "reaccion": { "...desglose..." },
    "ahorro_estimado": 3261.25,
    "riesgo_reemplazo": 26250.0,
    "roi_porcentaje": 23.21,
    "efectividad": 0.7
}
```

### 5. Proyeccion de contagios

Modelo SIR simplificado con crecimiento exponencial discreto. Simula la propagacion de la mastitis dia a dia.

**Constantes fijas:**
- Tasa de contagio por defecto: 0.1 (10% diario)

```
Para cada dia t:
    nuevas_infectadas(t) = infectadas(t) * tasa_contagio
    infectadas(t+1) = infectadas(t) + nuevas_infectadas(t)

    Si infectadas(t+1) > vacas_total:
        infectadas(t+1) = vacas_total
```

Equivale a un crecimiento exponencial `I(t) = I_0 * (1 + r)^t` acotado por el tamano del hato.

**Ejemplo:** 3 infectadas iniciales, tasa 0.1, hato de 50:
```
Dia 0:  3
Dia 1:  3 + 0.3  = 3.3  -> 3
Dia 2:  3.3 + 0.33 = 3.63 -> 4
...
Dia 10: ~7.8 -> 8
Dia 20: ~20.2 -> 20
Dia 30: ~52.3 -> 50 (acotado al hato)
```

**API:** `GET /calculadora/api/proyeccion/?infectadas=3&dias=30&vacas_total=50`

**Retorna:**

```json
{
    "proyeccion": [
        {"dia": 0, "infectadas": 3},
        {"dia": 1, "infectadas": 3},
        {"dia": 2, "infectadas": 4},
        "..."
    ]
}
```

El parametro `tasa` es opcional (default 0.1) y puede enviarse en la URL, aunque el panel no lo expone al usuario.

## APIs internas

Todas las APIs son de uso interno del panel (no publicas). Requieren sesion autenticada y permisos de gestion.

| Endpoint | Metodo | Parametros | Descripcion |
|----------|--------|------------|-------------|
| `/calculadora/api/perdida/` | GET | `dias`, `vacas` | Perdida proyectada |
| `/calculadora/api/roi/` | GET | `vacas_total`, `vacas_enfermas` | ROI con desglose completo |
| `/calculadora/api/proyeccion/` | GET | `infectadas`, `dias`, `tasa`, `vacas_total` | Proyeccion de contagios |
| `/calculadora/api/prevencion-vs-reaccion/` | GET | `vacas_total`, `vacas_enfermas` | Comparativa de costos |

## Interfaz del panel

El panel (`/calculadora/`) se compone de:

1. **Infoboxes de parametros:** Muestran los precios unitarios vigentes en 3 columnas (produccion, insumos, costos de reaccion).
2. **Sliders de simulacion:** 3 controles deslizantes + checkbox de riesgo de descarte.
3. **Banner de ganancia:** Muestra "Ganas $X por cada $1 invertido en prevencion", actualizado en tiempo real.
4. **Tarjetas de resultados:** Perdida proyectada (rojo), costo de reaccion (dorado), ROI de prevencion (verde).
5. **Grafico de contagios:** Curva SIR de propagacion (Chart.js, tipo linea).
6. **Grafico prevencion vs reaccion:** Barras comparativas de costos totales (Chart.js, tipo barra). Respeta el checkbox de descarte.
7. **Tablas de desglose:** Detalle de cada componente de costo con la formula aplicada y los montos parciales. La fila de reemplazo se muestra/oculta segun el checkbox.

## Supuestos y limitaciones

| Supuesto | Valor | Justificacion |
|----------|-------|---------------|
| Tasa de contagio | 10% diario | Estimacion conservadora para mastitis contagiosa |
| Dias de tratamiento | max 7 | Duracion tipica de tratamiento con antibioticos. Se usa `min(dias_simulacion, 7)` |
| Tasa de descarte | 15% | Porcentaje de vacas que no se recuperan y deben reemplazarse (opcional en ROI) |
| Efectividad de prevencion | 70% | Ningun programa previene el 100% de los casos. El 30% residual genera costos de tratamiento |
| Ordenos por mes | 60 | 2 ordenos diarios x 30 dias |
| Perdida de produccion | 100% | Asume que la vaca enferma pierde toda su produccion durante el tratamiento |
| Dosis sellador | 0.005 lt/ordeno | Consumo promedio por aplicacion |

Estos valores estan fijos en el codigo (`calculadora/calculos.py`). Los parametros financieros (precios) si son editables por el administrador desde `/calculadora/parametros/`. Para detalles sobre los cambios en la formula de ROI, ver `docs/cambios.md`.
