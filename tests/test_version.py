"""
Smoke test: package version matches 2.2.0.

Guards against divergence between pyproject.toml and ascend/__init__.py.
"""
import ascend


def test_version_matches_release():
    assert ascend.__version__ == "2.2.0"


def test_author_set():
    assert ascend.__author__ == "ASCEND by OW-AI"
