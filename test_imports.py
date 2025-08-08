#!/usr/bin/env python3
"""Test script to check imports"""

import sys
print("Python version:", sys.version)
print("Python path:")
for p in sys.path:
    print(f"  {p}")
print()

try:
    import pydantic_core
    print("✅ pydantic_core imported successfully")
except ImportError as e:
    print(f"❌ pydantic_core import failed: {e}")

try:
    import pydantic
    print("✅ pydantic imported successfully")
except ImportError as e:
    print(f"❌ pydantic import failed: {e}")

try:
    import yaml
    print("✅ yaml imported successfully")
except ImportError as e:
    print(f"❌ yaml import failed: {e}")

try:
    from serena.config.serena_config import ProjectConfig
    print("✅ serena.config.serena_config imported successfully")
except ImportError as e:
    print(f"❌ serena.config.serena_config import failed: {e}")

try:
    from serena.project import Project
    print("✅ serena.project imported successfully")
except ImportError as e:
    print(f"❌ serena.project import failed: {e}")

try:
    from solidlsp.ls_config import Language
    print("✅ solidlsp.ls_config imported successfully")
except ImportError as e:
    print(f"❌ solidlsp.ls_config import failed: {e}")
