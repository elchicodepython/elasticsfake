import os
import sys
from pathlib import Path
from unittest.mock import MagicMock

# Must set CONFIG_FILE_PATH before importing anything from the app
FIXTURES_DIR = Path(__file__).parent / "fixtures"
os.environ["CONFIG_FILE_PATH"] = str(FIXTURES_DIR / "config.yaml")

# Add the inner elasticsfake source dir to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "elasticsfake"))

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(scope="session")
def app():
    from app.api import app as fastapi_app
    return fastapi_app


@pytest.fixture(autouse=True)
def mock_bulk_handler():
    import conf
    mock = MagicMock()
    captured = []

    def handle_bulk(events):
        captured.extend(events)

    mock.handle_bulk = handle_bulk
    mock.captured = captured

    original = conf.container.bulk_handler
    conf.container.bulk_handler = mock
    yield mock
    conf.container.bulk_handler = original
    captured.clear()


@pytest.fixture
def client(app):
    return TestClient(app)


@pytest.fixture
def auth_client(app):
    """Client with auth dependency overridden to require elastic/changeme."""
    import secrets
    from fastapi import Depends, HTTPException
    from fastapi.security import HTTPBasic, HTTPBasicCredentials
    from app.api import _auth

    _basic = HTTPBasic(auto_error=False)

    def enforced_auth(credentials: HTTPBasicCredentials = Depends(_basic)):
        if credentials is None:
            raise HTTPException(
                status_code=401,
                detail="Authentication required",
                headers={"WWW-Authenticate": "Basic"},
            )
        ok = secrets.compare_digest(credentials.username, "elastic") and \
             secrets.compare_digest(credentials.password, "changeme")
        if not ok:
            raise HTTPException(
                status_code=401,
                detail="Invalid credentials",
                headers={"WWW-Authenticate": "Basic"},
            )

    app.dependency_overrides[_auth] = enforced_auth
    yield TestClient(app)
    app.dependency_overrides.clear()
