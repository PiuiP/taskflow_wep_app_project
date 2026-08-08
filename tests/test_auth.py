import pytest
from unittest.mock import MagicMock, patch

def test_login_success(client, mock_db):
    fake_user = MagicMock()
    fake_user.username = "admin"
    fake_user.password_hash = "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGfa37lW"
    fake_user.role = "admin"
    
    mock_db.query.return_value.filter.return_value.first.return_value = fake_user
    
    with patch("app.routes.auth.check_password", return_value=True):
        response = client.post("/login", data={
            "username": "admin",
            "password": "admin123"
        })
    
    assert response.status_code == 303
    assert response.headers["location"] == "/admin/users"
    assert "access_token" in response.cookies
    assert response.cookies["access_token"] != ""
    mock_db.query.assert_called_once()