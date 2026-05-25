from cryptography.fernet import Fernet
from django.conf import settings


def _get_fernet():
    key = settings.FERNET_KEY
    if isinstance(key, str):
        key = key.encode()
    return Fernet(key)


def cifrar(valor: str) -> str:
    f = _get_fernet()
    return f.encrypt(valor.encode()).decode()


def descifrar(token: str) -> str:
    f = _get_fernet()
    return f.decrypt(token.encode()).decode()


def generar_clave() -> str:
    return Fernet.generate_key().decode()
