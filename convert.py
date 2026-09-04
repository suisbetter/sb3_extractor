#!/usr/bin/env python3
"""
convert.py — convenience wrapper for the sb3_converter package.

This file exists so users can run the converter directly with
`python convert.py /path/to/project.sb3` without installing the package.

It does NOT duplicate the conversion logic: it imports the real
implementation from sb3_converter.core and re-uses the package CLI so there
is a single source of truth for the extraction/HTML-generation code.
"""
import os
import sys

# Allow running this file directly (without `pip install -e .`) by adding the
# repository root (the parent of this file's directory) to sys.path.
_REPO_ROOT = os.path.dirname(os.path.abspath(__file__))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from sb3_converter.cli import main  # noqa: E402  (path adjusted above)


if __name__ == "__main__":
    main()
