#!/usr/bin/env python3
"""
Test file with various Python errors for LSP analysis
"""

# Syntax error - missing closing parenthesis
def broken_function():
    print("This will cause a syntax error"
    return True

# Undefined variable error
def undefined_var_error():
    result = undefined_variable + 5
    return result

# Type error
def type_error():
    number = "string" + 42
    return number

# Unused variable warning
def unused_variable():
    unused_var = "this is not used"
    return "something else"

# Missing import error
def missing_import():
    return os.path.join("a", "b")

# TODO comment
def todo_function():
    # TODO: implement this function properly
    pass

# Long line style warning
def long_line():
    return "This is a very long line that exceeds the recommended line length and should trigger a style warning from flake8 or similar linters"

# Undefined function call
def undefined_function_call():
    return some_undefined_function()

class TestClass:
    def __init__(self):
        self.value = None
    
    # Potential None access
    def potential_none_error(self):
        return self.value.upper()  # Could be None

# Missing main guard
broken_function()
