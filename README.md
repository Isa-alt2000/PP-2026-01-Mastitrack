# Mastitrack

Aplicación web monolítica en Django para la gestión y prevención de mastitis bovina.

Este repositorio corresponde a un proyecto integrador semestral que sintetiza contenidos de Bases de Datos NoSQL, Inteligencia Artificial, Ecuaciones Diferenciales, Finanzas Corporativas, Estadística Multivariada y Criptografía.

## Objetivo general

Diseñar una plataforma simple y funcional para registrar información sanitaria y operativa del hato, evaluar riesgo de mastitis y estimar pérdidas económicas asociadas a la prevención o reacción ante alertas.

## Módulos planeados

- **Semáforo de riesgo**: evaluación de la probabilidad de mastitis por vaca usando una red neuronal con salida sigmoide. El resultado se clasificará en verde, amarillo o rojo.
- **Bitácora de ordeño**: registro paso a paso del proceso de ordeño con cálculo de métricas de cumplimiento y captura de datos de sensores de leche.
- **Calculadora de pérdidas y ROI**: simulación de pérdidas proyectadas, comparativo prevención vs reacción y cálculo de retorno de inversión. Los cálculos se ejecutarán en Django y se consumirán vía AJAX.

## Stack previsto

| Componente   | Tecnología                    |
|--------------|-------------------------------|
| Backend      | Django |
| Base de datos del dominio | MongoDB |
| Autenticación | SQLite / auth de Django |
| Frontend     | Django Templates |
| Gráficos     | Chart.js |
| Cifrado      | Fernet (cryptography) |
| Herramientas de entorno | uv |

## Estado del proyecto

Inicio del desarrollo.

Todavía no se han implementado los módulos funcionales; este repositorio solo contiene la base inicial del proyecto.

## Requisitos previos

- Python 3.10+
- MongoDB 6.0+ local o MongoDB Atlas
- uv

## Instalación local

```bash
# Crear entorno virtual
uv venv

# Activar entorno virtual
source .venv/bin/activate

# Instalar dependencias
uv pip install -r requirements.txt
```

## Configuración

Crear un archivo `.env` a partir del ejemplo:

```bash
cp .env.example .env
```

Variables esperadas:

- `DJANGO_SECRET_KEY`
- `DJANGO_DEBUG`
- `DJANGO_ALLOWED_HOSTS`
- `MONGODB_URI`
- `FERNET_KEY`

## Siguientes pasos

- Crear la estructura base del proyecto Django.
- Definir las apps principales del sistema.
- Configurar la conexión con MongoDB.
- Preparar el panel administrativo.
- Implementar los modelos y vistas iniciales.

## Estructura esperada

```text
pp-mastitis/
├── mastitis_project/
├── core/
├── vacas/
├── bitacora/
├── semaforo/
├── calculadora/
├── templates/
├── static/
└── docs/
```

## Documentación

La documentación técnica y de arquitectura se irá agregando progresivamente en la carpeta `docs/`.

## Licencia

Proyecto académico. Uso interno para fines universitarios.