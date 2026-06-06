from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_env_is_ignored_and_not_packaged():
    gitignore = (ROOT / ".gitignore").read_text()
    manifest = (ROOT / "MANIFEST.in").read_text()

    assert ".env" in gitignore.splitlines()
    assert "include .env" not in manifest


def test_manifest_includes_runtime_static_and_schema_assets():
    manifest = (ROOT / "MANIFEST.in").read_text()
    assert "recursive-include ytgrid *.py *.sql *.html *.css *.js" in manifest
