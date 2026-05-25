# MastitisApp

Aplicacion web monolitica en Django para la gestion y prevencion de mastitis bovina. 
Proyecto integrador semestral que sintetiza contenidos de Bases de Datos NoSQL, Inteligencia Artificial, Ecuaciones Diferenciales, Finanzas Corporativas, Estadistica Multivariada y Criptografia.

## Modulos

- **Semaforo de riesgo**: evalua la probabilidad de mastitis por vaca usando una red neuronal con salida sigmoide. Clasifica en verde, amarillo o rojo.
- **Bitacora de ordeno**: registro paso a paso del proceso de ordeno con calculo automatico de metricas de cumplimiento y captura de datos de sensores de leche.
- **Calculadora de perdidas y ROI**: simulacion de perdidas proyectadas, comparativo prevencion vs reaccion y calculo de retorno de inversion. Los calculos se ejecutan en Django y se consumen via AJAX.

## Stack

| Componente   | Tecnologia                     |
|--------------|--------------------------------|
| Backend      | Django 4.2                     |
| BD dominio   | MongoDB (MongoEngine)          |
| BD auth      | SQLite (django.contrib.auth)   |
| Frontend     | Django Templates + Bootstrap 5 |
| Graficos     | Chart.js                       |
| Cifrado      | Fernet (cryptography)          |
| Inferencia   | NumPy                          |

## Requisitos previos

- Python 3.10+
- MongoDB 6.0+ (local o Atlas)
- [uv](https://docs.astral.sh/uv/)

## Instalacion

```bash
# Crear entorno virtual e instalar dependencias
uv venv mastitisvenv
source mastitisvenv/bin/activate
uv pip install -r requirements.txt

# Configurar variables de entorno
cp .env.example .env
# Editar .env con tus valores (MONGODB_URI, DJANGO_SECRET_KEY, FERNET_KEY)

# Migrar SQLite (autenticacion)
uv run manage.py migrate

# Crear superusuario
uv run manage.py createsuperuser

# Crear grupos de usuario
uv run manage.py shell -c "
from django.contrib.auth.models import Group
Group.objects.get_or_create(name='administrador')
Group.objects.get_or_create(name='operador')
"

# Iniciar servidor
uv run manage.py runserver
```

## Uso

1. Acceder a `http://localhost:8000/`
2. Iniciar sesion con el superusuario creado
3. Desde el admin de Django (`/admin/`), asignar usuarios a los grupos `administrador` u `operador`

### Permisos por rol

| Rol           | Acceso                                                           |
|---------------|------------------------------------------------------------------|
| Administrador | Vacas (CRUD), Semaforo, Calculadora, Parametros financieros      |
| Operador      | Vacas (lectura), Bitacora de ordeno, Dashboard general           |

## Estructura del proyecto

```
pp-mastitis/
├── mastitis_project/   # Configuracion Django
├── core/               # Utilidades: crypto, context processors, dashboard
├── vacas/              # Gestion de vacas y visitas veterinarias
├── bitacora/           # Bitacora de ordeno y sensores de leche
├── semaforo/           # Semaforo de riesgo (inferencia NN)
├── calculadora/        # Calculadora ROI y parametros financieros
├── templates/          # Templates HTML
├── static/             # CSS y JS
└── docs/               # Documentacion de arquitectura
```

Ver [docs/architecture.md](docs/architecture.md) para documentacion detallada.

## Variables de entorno

| Variable             | Descripcion                          | Ejemplo                                    |
|----------------------|--------------------------------------|--------------------------------------------|
| DJANGO_SECRET_KEY    | Clave secreta de Django              | (generada automaticamente)                 |
| DJANGO_DEBUG         | Modo debug                           | True                                       |
| DJANGO_ALLOWED_HOSTS | Hosts permitidos separados por coma  | localhost,127.0.0.1                        |
| MONGODB_URI          | URI de conexion a MongoDB            | mongodb://localhost:27017/mastitis_db       |
| FERNET_KEY           | Clave Fernet para cifrado            | (generada automaticamente)                 |
