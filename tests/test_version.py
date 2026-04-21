"""
Smoke test: package version matches the current release.

Guards against divergence between pyproject.toml and ascend/__init__.py.
Bumped at release time alongside the version-site files.
"""
import ascend


def test_version_matches_release():
    assert ascend.__version__ == "2.4.2"


def test_author_set():
    assert ascend.__author__ == "ASCEND by OW-AI"
