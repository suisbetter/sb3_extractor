"""
setup.py – legacy setuptools entry point.
The canonical configuration lives in pyproject.toml; this file exists only
for editable installs with older pip versions (pip < 21.3).
"""
from setuptools import setup

if __name__ == "__main__":
    setup()
