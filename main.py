#!/usr/bin/env python3
"""Script ejecutable para paca."""
import sys

# Forzar UTF-8 en consola de Windows (cp1252 no soporta ✓ ⚠ ⊗)
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

from paca import run

if __name__ == "__main__":
    sys.exit(run())
