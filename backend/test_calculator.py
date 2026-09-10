import pytest

from calculator import (
    DivisionByZeroError,
    add_numbers,
    divide_numbers,
    multiply_numbers,
    subtract_numbers,
)


def test_add_numbers() -> None:
    assert add_numbers(2, 3) == 5


def test_subtract_numbers() -> None:
    assert subtract_numbers(7, 3) == 4


def test_multiply_numbers() -> None:
    assert multiply_numbers(4, 5) == 20


def test_divide_numbers() -> None:
    assert divide_numbers(7, 2) == 3.5


def test_subtract_numbers_supports_negative_decimal_values() -> None:
    assert subtract_numbers(2.5, -1) == 3.5


def test_divide_numbers_rejects_zero_divisor() -> None:
    with pytest.raises(DivisionByZeroError, match="Cannot divide by zero"):
        divide_numbers(1, 0)
