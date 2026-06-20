import database.db as db_module


def test_login_valid_credentials(client, app):
    db_module.create_user("Test User", "test@example.com", "password123")
    response = client.post("/login", data={"email": "test@example.com", "password": "password123"})
    assert response.status_code == 302
    assert response.headers["Location"] == "/dashboard"
    with client.session_transaction() as sess:
        assert "user_id" in sess


def test_login_wrong_password(client, app):
    db_module.create_user("Test User", "test@example.com", "password123")
    response = client.post("/login", data={"email": "test@example.com", "password": "wrongpass"})
    assert response.status_code == 200
    assert b"Invalid email or password." in response.data


def test_login_unknown_email(client):
    response = client.post("/login", data={"email": "nobody@example.com", "password": "password123"})
    assert response.status_code == 200
    assert b"Invalid email or password." in response.data


def test_login_blank_fields(client):
    response = client.post("/login", data={"email": "", "password": ""})
    assert response.status_code == 200
    assert b"Email and password are required." in response.data


def test_logout_clears_session(client, app):
    db_module.create_user("Test User", "test@example.com", "password123")
    client.post("/login", data={"email": "test@example.com", "password": "password123"})
    response = client.get("/logout")
    assert response.status_code == 302
    assert response.headers["Location"] == "/"
    with client.session_transaction() as sess:
        assert "user_id" not in sess


def test_login_page_redirects_to_dashboard_when_logged_in(client, app):
    db_module.create_user("Test User", "test@example.com", "password123")
    client.post("/login", data={"email": "test@example.com", "password": "password123"})
    response = client.get("/login")
    assert response.status_code == 302
    assert response.headers["Location"] == "/dashboard"


def test_register_page_redirects_to_dashboard_when_logged_in(client, app):
    db_module.create_user("Test User", "test@example.com", "password123")
    client.post("/login", data={"email": "test@example.com", "password": "password123"})
    response = client.get("/register")
    assert response.status_code == 302
    assert response.headers["Location"] == "/dashboard"


def test_dashboard_after_logout_redirects_to_login(client, app):
    db_module.create_user("Test User", "test@example.com", "password123")
    client.post("/login", data={"email": "test@example.com", "password": "password123"})
    client.get("/logout")
    response = client.get("/dashboard")
    assert response.status_code == 302
    assert response.headers["Location"] == "/login"
