from __future__ import annotations

import base64
import hashlib
import re
from collections.abc import Iterable

from cryptography.fernet import Fernet


def normalize_document(value: str) -> str:
    return re.sub(r"\D", "", value)


def document_type(value: str) -> str:
    normalized = normalize_document(value)
    if len(normalized) == 11 and _valid_cpf(normalized):
        return "cpf"
    if len(normalized) == 14 and _valid_cnpj(normalized):
        return "cnpj"
    raise ValueError("CPF/CNPJ inválido.")


def mask_document(value: str) -> str:
    normalized = normalize_document(value)
    if len(normalized) == 11:
        return f"***.***.***-{normalized[-2:]}"
    return f"**.***.***/****-{normalized[-2:]}"


class DocumentCipher:
    def __init__(self, key: str) -> None:
        derived = base64.urlsafe_b64encode(hashlib.sha256(key.encode("utf-8")).digest())
        self._fernet = Fernet(derived)

    def encrypt(self, value: str) -> str:
        return self._fernet.encrypt(value.encode("ascii")).decode("ascii")

    def decrypt(self, value: str) -> str:
        return self._fernet.decrypt(value.encode("ascii")).decode("ascii")


def _valid_cpf(value: str) -> bool:
    if len(set(value)) == 1:
        return False
    digits = [int(item) for item in value]
    first = _check_digit(digits[:9], range(10, 1, -1))
    second = _check_digit([*digits[:9], first], range(11, 1, -1))
    return digits[-2:] == [first, second]


def _valid_cnpj(value: str) -> bool:
    if len(set(value)) == 1:
        return False
    digits = [int(item) for item in value]
    first = _check_digit(digits[:12], [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2])
    second = _check_digit(
        [*digits[:12], first],
        [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2],
    )
    return digits[-2:] == [first, second]


def _check_digit(digits: list[int], weights: Iterable[int]) -> int:
    total = sum(digit * weight for digit, weight in zip(digits, weights, strict=True))
    remainder = total % 11
    return 0 if remainder < 2 else 11 - remainder
