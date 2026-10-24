"""Unit tests for the safe AST calculator tool."""

import pytest
from src.graph import calculator_tool


def test_basic_arithmetic():
    """Tests addition, subtraction, multiplication, and division."""
    assert calculator_tool("20 - 12") == 8
    assert calculator_tool("10 + 5") == 15
    assert calculator_tool("6 * 7") == 42
    assert calculator_tool("20 / 4") == 5


def test_decimals_and_negatives():
    """Tests float handling and negative numbers."""
    assert calculator_tool("1.5 + 2.5") == 4
    assert calculator_tool("10 - 15.5") == -5.5
    assert calculator_tool("-5 * 3") == -15


def test_exponentiation():
    """Tests power operations within allowed bounds."""
    assert calculator_tool("2 ** 3") == 8
    assert calculator_tool("3 ** 2") == 9


def test_exponent_bound_rejection():
    """Tests that excessive exponentiation (DoS risk) is rejected."""
    with pytest.raises(ValueError, match="Maximum supported exponent"):
        calculator_tool("2 ** 50")

    with pytest.raises(ValueError, match="Maximum supported exponent"):
        calculator_tool("100000 ** 2")


def test_division_by_zero():
    """Tests that division by zero raises ZeroDivisionError cleanly."""
    with pytest.raises(ZeroDivisionError):
        calculator_tool("10 / 0")

    with pytest.raises(ZeroDivisionError):
        calculator_tool("5 // 0")


def test_empty_and_whitespace():
    """Tests that empty strings are rejected."""
    with pytest.raises(ValueError):
        calculator_tool("")

    with pytest.raises(ValueError):
        calculator_tool("   ")


@pytest.mark.parametrize(
    "malicious_expr",
    [
        "__import__('os').system('echo pwned')",
        "eval('2 + 2')",
        "open('/etc/passwd').read()",
        "exec('import sys')",
        "x + 5",
        "lambda: 1",
        "[x for x in range(10)]",
        "{'a': 1}",
        "(10).bit_length()",
    ],
)
def test_malicious_code_rejection(malicious_expr):
    """Verifies that non-numeric code, calls, imports, and variables are strictly rejected."""
    with pytest.raises(Exception):
        calculator_tool(malicious_expr)
