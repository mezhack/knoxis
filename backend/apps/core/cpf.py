import hashlib
import hmac
import re

from django.conf import settings


def normalize(cpf: str) -> str:
    return re.sub(r"\D", "", cpf)


def is_valid(cpf: str) -> bool:
    cpf = normalize(cpf)
    if len(cpf) != 11:
        return False
    if len(set(cpf)) == 1:
        return False
    for i in range(2):
        total = sum(int(cpf[j]) * (10 + i - j) for j in range(9 + i))
        expected = (total * 10 % 11) % 10
        if expected != int(cpf[9 + i]):
            return False
    return True


def hash_cpf(cpf: str) -> str:
    cpf = normalize(cpf)
    key = settings.CPF_HMAC_KEY.encode()
    return hmac.new(key, cpf.encode(), hashlib.sha256).hexdigest()


def last2(cpf: str) -> str:
    cpf = normalize(cpf)
    return cpf[-2:]


def mask(cpf: str) -> str:
    cpf = normalize(cpf)
    if len(cpf) == 11:
        return f"***.***.***.{cpf[-2:]}"
    return "***.***.***-**"
