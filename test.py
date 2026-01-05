"""Test module for demonstrating coding agent capabilities."""

import unittest
from typing import List, Optional


def add(a: int, b: int) -> int:
    """Add two numbers."""
    return a + b


def multiply(a: int, b: int) -> int:
    """Multiply two numbers."""
    return a * b


def divide(a: float, b: float) -> float:
    """Divide two numbers."""
    if b == 0:
        raise ValueError("Cannot divide by zero")
    return a / b


class Calculator:
    """A simple calculator class."""
    
    def __init__(self):
        self.history = []
    
    def calculate(self, operation: str, a: float, b: float) -> float:
        """Perform calculation and store in history."""
        if operation == "add":
            result = a + b
        elif operation == "subtract":
            result = a - b
        elif operation == "multiply": 
            result = a * b
        elif operation == "divide": 
            if b == 0:
                raise ValueError("Cannot divide by zero")
            result = a / b
        else:
            raise ValueError(f"Unknown operation: {operation}")
        
        self.history.append({
            "operation": operation,
            "operands": (a, b),
            "result": result
        })
        
        return result
    
    def get_history(self) -> List[dict]:
        """Return calculation history."""
        return self.history
    
    def clear_history(self):
        """Clear calculation history."""
        self.history = []


class DataProcessor:
    """Process data with various operations."""
    
    def __init__(self, data: Optional[List[int]] = None):
        self.data = data or []
    
    def filter_positive(self) -> List[int]:
        """Filter positive numbers from data."""
        return [x for x in self.data if x > 0]
    
    def sum_values(self) -> int:
        """Calculate sum of all values."""
        return sum(self.data)
    
    def average(self) -> float:
        """Calculate average of values."""
        if not self.data:
            return 0.0
        return sum(self. data) / len(self.data)
    
    def sort_data(self, reverse: bool = False) -> List[int]:
        """Sort data in ascending or descending order."""
        return sorted(self.data, reverse=reverse)


class TestCalculator(unittest.TestCase):
    """Unit tests for Calculator class."""
    
    def setUp(self):
        self.calc = Calculator()
    
    def test_add(self):
        result = self.calc.calculate("add", 5, 3)
        self.assertEqual(result, 8)
    
    def test_divide_by_zero(self):
        with self.assertRaises(ValueError):
            self.calc.calculate("divide", 10, 0)
    
    def test_history(self):
        self.calc.calculate("add", 1, 2)
        self.calc.calculate("multiply", 3, 4)
        self.assertEqual(len(self.calc.get_history()), 2)


if __name__ == "__main__":
    unittest.main()