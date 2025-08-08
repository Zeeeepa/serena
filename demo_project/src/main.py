#!/usr/bin/env python3
"""
Demo Python project with various errors for Serena analysis.
"""

import os
import sys
import json
import missing_module  # Import error - module doesn't exist

def calculate_total(items):
    """Calculate total price of items."""
    total = 0
    for item in items:
        total += item.price  # Potential AttributeError if item has no price
    return total

def process_data(data):
    """Process data with various potential issues."""
    if data is None:
        return None
    
    # Undefined variable error
    result = undefined_variable + data  # NameError
    
    # Type error - trying to add incompatible types
    mixed_result = "string" + 42  # TypeError
    
    return result

def unused_function():
    """This function is never called - dead code."""
    print("This function is unused")
    return True

class DataProcessor:
    """Example class with various issues."""
    
    def __init__(self, config):
        self.config = config
        self.data = []
    
    def add_item(self, item):
        """Add item to processor."""
        # Missing validation
        self.data.append(item)
    
    def process_all(self):
        """Process all items."""
        results = []
        for item in self.data:
            # Potential KeyError if item is dict without 'value' key
            processed = item['value'] * 2
            results.append(processed)
        return results

if __name__ == "__main__":
    # Missing error handling
    processor = DataProcessor(None)
    processor.add_item({"name": "test"})  # Missing 'value' key
    results = processor.process_all()  # Will cause KeyError
    print(f"Results: {results}")
