# Guia de Instalacion

## Requisitos previos

- Python 3.10 o superior
- MongoDB 6.0+ (local o MongoDB Atlas)
- [uv](https://docs.astral.sh/uv/) (gestor de paquetes)
- Git

### Instalar uv

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

En Windows:
```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

## Paso 1: Clonar el repositorio

```bash
git clone <url-del-repo>
cd pp-mastitis
```

## Paso 2: Crear y activar entorno virtual

```bash
uv venv mastitisvenv
source mastitisvenv/bin/activate
```

En Windows:
```bash
uv venv mastitisvenv
mastitisvenv\Scripts\activate
```

## Paso 3: Instalar dependencias

```bash
uv pip install -r requirements.txt
```

Dependencias principales:

| Paquete        | Version | Uso                              |
|----------------|---------|----------------------------------|
| Django         | 4.2.17  | Framework web                    |
| mongoengine    | 0.29.1  | ODM para MongoDB                 |
| cryptography   | 44.0.0  | Cifrado Fernet                   |
| numpy          | 1.26.4  | Inferencia red neuronal          |
| python-dotenv  | 1.1.0   | Carga de variables de entorno    |

## Paso 4: Configurar variables de entorno

Copiar el archivo de ejemplo y editarlo:

```bash
cp .env.example .env
```

Editar `.env` con los valores reales:

```env
# Generar una clave secreta de Django
DJANGO_SECRET_KEY=<tu-clave-secreta>

# Modo debug (True para desarrollo)
DJANGO_DEBUG=True

# Hosts permitidos
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1

# URI de conexion a MongoDB
MONGODB_URI=mongodb://localhost:27017/mastitis_db

# Clave Fernet para cifrado
FERNET_KEY=<tu-clave-fernet>
```

### Generar claves

Para generar la clave secreta de Django:
```bash
uv run python -c "import secrets; print(secrets.token_urlsafe(50))"
```

Para generar la clave Fernet:
```bash
uv run python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

### Configuracion de MongoDB Atlas

Si se usa MongoDB Atlas en lugar de una instancia local, la URI tiene este formato:

```
mongodb+srv://usuario:password@cluster.mongodb.net/mastitis_db
```

O con replica set explicito:

```
mongodb://usuario:password@shard-00.host:27017,shard-01.host:27017,shard-02.host:27017/?ssl=true&replicaSet=atlas-xxx&authSource=admin
```

## Paso 5: Migrar base de datos SQLite

Django usa SQLite unicamente para el sistema de autenticacion (usuarios, grupos, sesiones). Los datos de dominio van en MongoDB.

```bash
uv run manage.py migrate
```

## Paso 6: Crear grupos de usuario

```bash
uv run manage.py shell -c "
from django.contrib.auth.models import Group
Group.objects.get_or_create(name='administrador')
Group.objects.get_or_create(name='operador')
"
```

## Paso 7: Crear superusuario

```bash
uv run manage.py createsuperuser
```

Seguir las instrucciones para ingresar usuario, email y contrasena.

## Paso 8: Iniciar el servidor

```bash
uv run manage.py runserver
```

Acceder a `http://localhost:8000/`

## Post-instalacion

### Asignar roles a usuarios

1. Ir a `http://localhost:8000/admin/`
2. Iniciar sesion con el superusuario
3. En la seccion "Usuarios", editar cada usuario y asignarle el grupo `administrador` u `operador`

### Verificar conexion a MongoDB

Si hay problemas de conexion, verificar que:
- MongoDB esta corriendo (local) o el cluster Atlas esta activo
- La URI en `.env` es correcta
- El usuario tiene permisos de lectura/escritura sobre la base de datos
- Si se usa Atlas, la IP actual esta en la whitelist del cluster
