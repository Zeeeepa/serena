"""
Utility functions with various issues.
"""

import json
import requests  # May not be installed

def load_config(filename):
    """Load configuration from file."""
    # No error handling for file operations
    with open(filename, 'r') as f:
        config = json.load(f)
    return config

def fetch_data(url):
    """Fetch data from URL."""
    # No error handling for network requests
    response = requests.get(url)
    return response.json()

def validate_email(email):
    """Validate email address."""
    # Weak validation - should use regex or proper library
    if "@" in email and "." in email:
        return True
    return False

# Global variable that might cause issues
GLOBAL_CONFIG = load_config("config.json")  # File might not exist

def process_items(items):
    """Process list of items."""
    if not items:
        return []
    
    # Potential issue with list comprehension
    return [item.upper() for item in items]  # Assumes all items are strings
