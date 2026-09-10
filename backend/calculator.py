"""Framework-free arithmetic operations for Hello Agent."""

Number = int | float


class DivisionByZeroError(ValueError):
    """Raised when a division operation receives zero as its divisor."""


def add_numbers(left: Number, right: Number) -> Number:
    """Return the sum of two numbers."""
    return left + right


def subtract_numbers(left: Number, right: Number) -> Number:
    """Return the result of subtracting right from left."""
    return left - right


def multiply_numbers(left: Number, right: Number) -> Number:
    """Return the product of two numbers."""
    return left * right


def divide_numbers(left: Number, right: Number) -> float:
    """Return left divided by right, rejecting a zero divisor explicitly."""
    if right == 0:
        raise DivisionByZeroError("Cannot divide by zero.")

    return left / right
