#!/usr/bin/env python3
"""
Example of good Python code with no real errors.
"""

import os
import sys
import json

def calculate_total(items):
    """Calculate total price of items."""
    total = 0
    for item in items:
        if hasattr(item, 'price'):
            total += item.price
    return total

def process_data(data):
    """Process data safely."""
    if data is None:
        return None
    
    # Properly defined variable
    result = data * 2
    return result

class DataProcessor:
    """Example class with proper implementation."""
    
    def __init__(self, config=None):
        self.config = config or {}
        self.data = []
    
    def add_item(self, item):
        """Add item to processor with validation."""
        if isinstance(item, dict) and 'value' in item:
            self.data.append(item)
        else:
            raise ValueError("Item must be a dict with 'value' key")
    
    def process_all(self):
        """Process all items safely."""
        results = []
        for item in self.data:
            if 'value' in item:
                processed = item['value'] * 2
                results.append(processed)
        return results

if __name__ == "__main__":
    # Proper error handling
    try:
        processor = DataProcessor()
        processor.add_item({"value": 10, "name": "test"})
        results = processor.process_all()
        print(f"Results: {results}")
    except Exception as e:
        print(f"Error: {e}")
