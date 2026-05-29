# APIs del sistema
El sistema cuenta con una API para recibir las lecturas de los sensores de leche.


### JWT
POST /api/token/ 
Obtener token JWT con credenciales:
```json
{
    "username": "user",
    "password": "password"
}
```

Responde: {"token": "eyJ...", "username": "operador1"}

### Sensores de leche
POST /api/sensores/
Registrar lecturas (con header Authorization: Bearer token):

```json
{
    "lecturas": [
        {
        "arete": "str",
        "conteo_celulas_somaticas": 1,
        "ph": 1,
        "temperatura": 1,
        "conductividad_electrica": 5.1
        },
        {
        "arete": "str",
        "conteo_celulas_somaticas": 1,
        "ph": 1,
        "temperatura": 1,
        "conductividad_electrica": 1
        }
    ]
}
```
Cada lectura se vincula automaticamente a la vaca por arete y a su bitacora de ordeno mas reciente.