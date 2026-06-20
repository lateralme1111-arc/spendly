import database.db as db_module


def _login(client, email="profile@example.com", password="password123"):
    db_module.create_user("Profile User", email, password)
    client.post("/login", data={"email": email, "password": password})
    return client


# ------------------------------------------------------------------ #
# GET /profile                                                         #
# ------------------------------------------------------------------ #

def test_profile_redirects_when_logged_out(client):
    response = client.get("/profile")
    assert response.status_code == 302
    assert response.headers["Location"] == "/login"


def test_profile_renders_when_logged_in(client, app):
    _login(client)
    response = client.get("/profile")
    assert response.status_code == 200
    assert b"Profile User" in response.data
    assert b"profile@example.com" in response.data


# ------------------------------------------------------------------ #
# POST /profile (name update)                                          #
# ------------------------------------------------------------------ #

def test_profile_name_update_valid(client, app):
    _login(client)
    response = client.post("/profile", data={"name": "New Name"})
    assert response.status_code == 302
    assert response.headers["Location"] == "/profile?updated=name"


def test_profile_name_update_empty(client, app):
    _login(client)
    response = client.post("/profile", data={"name": "   "})
    assert response.status_code == 200
    assert b"Name cannot be empty." in response.data


# ------------------------------------------------------------------ #
# POST /profile/password                                               #
# ------------------------------------------------------------------ #

def test_profile_password_logged_out(client):
    response = client.post(
        "/profile/password",
        data={"current_password": "x", "new_password": "y", "confirm_password": "y"},
    )
    assert response.status_code == 302
    assert response.headers["Location"] == "/login"


def test_profile_password_change_valid(client, app):
    _login(client)
    response = client.post(
        "/profile/password",
        data={
            "current_password": "password123",
            "new_password":     "newpassword1",
            "confirm_password": "newpassword1",
        },
    )
    assert response.status_code == 302
    assert response.headers["Location"] == "/profile?updated=password"


def test_profile_password_wrong_current(client, app):
    _login(client)
    response = client.post(
        "/profile/password",
        data={
            "current_password": "wrongpassword",
            "new_password":     "newpassword1",
            "confirm_password": "newpassword1",
        },
    )
    assert response.status_code == 200
    assert b"Current password is incorrect." in response.data


def test_profile_password_too_short(client, app):
    _login(client)
    response = client.post(
        "/profile/password",
        data={
            "current_password": "password123",
            "new_password":     "short",
            "confirm_password": "short",
        },
    )
    assert response.status_code == 200
    assert b"New password must be at least 8 characters." in response.data


def test_profile_password_mismatch(client, app):
    _login(client)
    response = client.post(
        "/profile/password",
        data={
            "current_password": "password123",
            "new_password":     "newpassword1",
            "confirm_password": "differentpass",
        },
    )
    assert response.status_code == 200
    assert b"Passwords do not match." in response.data


def test_profile_password_same_as_current(client, app):
    _login(client)
    response = client.post(
        "/profile/password",
        data={
            "current_password": "password123",
            "new_password":     "password123",
            "confirm_password": "password123",
        },
    )
    assert response.status_code == 200
    assert b"New password must differ from your current password." in response.data
