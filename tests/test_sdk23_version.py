"""
SDK 2.3.0 — version alignment tests.

Ensures `__version__` in ascend/__init__.py matches `SDK_VERSION` in
ascend/constants.py AND the version in pyproject.toml. Prior releases
drifted between 2.1.1 and 2.2.0; this guards against that regression.
"""
from __future__ import annotations

import os
import re

import ascend
from ascend.constants import SDK_VERSION


EXPECTED = "2.4.1"


def test_init_version():
    assert ascend.__version__ == EXPECTED


def test_constants_version():
    assert SDK_VERSION == EXPECTED


def test_constants_and_init_agree():
    assert ascend.__version__ == SDK_VERSION


def test_pyproject_version_aligned():
    """pyproject.toml version must match the package version."""
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    pyproject = os.path.join(root, "pyproject.toml")
    with open(pyproject, "r", encoding="utf-8") as f:
        content = f.read()
    m = re.search(r'^version\s*=\s*"([^"]+)"', content, re.MULTILINE)
    assert m, "version line not found in pyproject.toml"
    assert m.group(1) == EXPECTED, (
        f"pyproject.toml version {m.group(1)!r} != {EXPECTED!r}"
    )
