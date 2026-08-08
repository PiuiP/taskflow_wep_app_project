import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient

with patch("app.database.init_db"):
    from app.main import app
    from app.database import get_db 

@pytest.fixture
def mock_db():
    return MagicMock()

@pytest.fixture
def client(mock_db):
    def override_get_db():
        yield mock_db

    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()