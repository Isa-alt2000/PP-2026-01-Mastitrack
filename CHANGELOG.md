# Changelog

## [0.3.0] - 2026-05-28
### Diseno y vistas de vacas
- Vista de tarjetas como vista principal del registro de vacas, con agrupacion por lote en contenedores y paginacion de 25.
- Toggle para alternar entre vista de tarjetas y vista de lista.
- Tarjetas con imagen de fondo (`vacas_fondo.png`) y degradado oscuro para legibilidad.
- Detalle de vaca rediseñado: layout vertical centrado, imagen hero con degradado blanco, nombre en grande y arete debajo.
- Boton "Regresar al listado" en la parte inferior del detalle.

### API de sensores
- Nueva app `api` con autenticacion JWT (PyJWT).
- Endpoint `POST /api/token/` para obtener token con credenciales de usuario.
- Endpoint `POST /api/sensores/` para recibir lecturas de sensores en lote, vinculadas automaticamente a vacas por arete y a su bitacora mas reciente.

### Validacion de sensores
- Validacion en 4 capas: frontend (min/max/step/placeholders), servidor (rechazo fuera de rango), validacion cruzada y banderas de calidad.
- Rangos de referencia para CCS, pH, temperatura y conductividad electrica.
- Campo `origen` en SensorLeche con valores `manual` y `api` (mostrado como "SENSOR" en frontend).
- Campo `fiable` para marcar lecturas de API con valores fuera de rango (se almacenan, no se rechazan).
- Campo `banderas_calidad` con niveles `sospechoso`, `alto` y `no_fiable`.
- Badges con colores institucionales para origen, fiabilidad y banderas.

### Detalle de vaca
- Ultimo sensor de leche visible en la pagina de cada vaca con todos sus campos y banderas.
- Boton de edicion de sensor visible solo para administradores.
- Vista y ruta de edicion de sensor (`/bitacora/sensor/<id>/editar/`).

### Documentacion
- README actualizado: nombre Mastitrack, PyJWT en stack, `uv sync`, 3 roles, estructura completa.
- `docs/architecture.md` actualizado con apps api y usuarios, validacion de sensores, flujo de datos.
- `docs/api.md` reescrito con documentacion completa de endpoints, validacion y fiabilidad.
- `docs/databases.md` actualizado con campos nuevos de sensores_leche.

## [0.3.0] - 2026-05-28
### Semaforo de riesgo y fixes

- **Evaluaciones visibles al cargar**: al abrir el panel del semaforo se muestran automaticamente las evaluaciones mas recientes de cada vaca (nivel de alerta, probabilidad y fecha).
- **Evaluacion automatica con datos nuevos**: si al cargar el panel se detectan datos de sensor mas recientes que la ultima evaluacion (o un modelo nuevo), se ejecuta la inferencia automaticamente sin intervencion manual.
- **Boton de evaluar con control de duplicados**: el boton "Evaluar" solo esta habilitado si existen datos de sensor nuevos o una version de modelo distinta. Si ya se evaluo con los datos actuales, el boton aparece deshabilitado como "Evaluado". Al intentar evaluar via AJAX sin datos nuevos, el backend responde con HTTP 409 y un mensaje explicativo.
- **Probabilidad con 4 decimales**: el historial y el panel ahora muestran la probabilidad como porcentaje con cuatro decimales (ej. 85.1234%) en vez de mostrar el valor crudo de 0 a 1.
- **Version de modelo centralizada**: se agrego la constante `VERSION_MODELO` en `inference.py` para comparar si el modelo cambio desde la ultima evaluacion.

### Dashboard

- La tabla de ultimas evaluaciones ahora usa `prob_display` y formato de fecha `d/m/Y H:i`.
- Nuevo filtro `prob_display`: convierte probabilidad (0-1) a porcentaje con 4 decimales.

### Documentación
- Añadido `CHANGELOG.md` y diagrama de base de datos en `docs/databases.md` con mermaid.

## [0.2.0] - 2026-05-27
### UI

- Navegacion migrada de navbar superior a sidebar lateral colapsable con iconos SVG.
- El sidebar recuerda su estado (expandido/colapsado) entre paginas via localStorage.
- En movil, el sidebar se oculta y se accede con un boton hamburguesa flotante.
- Footer con logo de la UNRC, texto del proyecto y logo de Mastitrack.

## [0.2.0] - 2026-05-26
### Identidad

- Logo de la aplicacion (`mastitrack_logo.png`) en navbar y login.
- Favicon personalizado (`mastitrack_favicon.ico`).

### Roles y permisos

- Tres niveles de rol: superadmin (is_superuser), administrador (grupo), operador (grupo).
- Pildora de rol visible junto al nombre de usuario en el sidebar.
- Variable de contexto `puede_gestionar` (superadmin o admin) para controlar acceso en templates y vistas.
- Modulo de usuarios (`/usuarios/`) para crear y editar usuarios con asignacion de rol.
- Restricciones de acceso aplicadas en backend (con decoraodres) y frontend (templates):
  - Operador: solo puede ver vacas y agregar entradas a la bitacora.
  - Superadmin y admin: acceso completo al CRUD, semáforo, calculadora, parametros y usuarios.
- Vista y formulario de edicion de vacas agregados.

## [0.1.0] - 2026-05-20
### Esqueleto inicial

- Proyecto Django monolitico con MongoDB (MongoEngine) y SQLite (auth).
- Cuatro apps de dominio: vacas, bitacora, semaforo, calculadora.
- Modulo core con cifrado Fernet, context processors y template tags.
- Siete colecciones MongoDB definidas.
- Red neuronal simulada para inferencia de riesgo de mastitis. (real será implementada despues)
- Calculadora de perdidas con formulas de ROI, proyeccion de contagios y comparativo prevencion vs reaccion.
- Endpoints JSON para calculos (AJAX desde frontend).
- Templates con Bootstrap 5 y Chart.js.
- Configuracion final via `.env` con python-dotenv.
- Documentacion: architecture.md, install.md, README.md.
