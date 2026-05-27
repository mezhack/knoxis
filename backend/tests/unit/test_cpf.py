import pytest
from apps.core.cpf import is_valid, normalize, last2, mask


def test_cpf_valido():
    assert is_valid("529.982.247-25")
    assert is_valid("52998224725")


def test_cpf_invalido_digitos():
    assert not is_valid("111.111.111-11")
    assert not is_valid("000.000.000-00")
    assert not is_valid("123.456.789-00")


def test_cpf_formato_invalido():
    assert not is_valid("123")
    assert not is_valid("")


def test_normalize():
    assert normalize("123.456.789-09") == "12345678909"
    assert normalize("12345678909") == "12345678909"


def test_last2():
    assert last2("52998224725") == "25"


def test_mask():
    assert mask("52998224725") == "***.***.***.25"
