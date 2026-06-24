import pytest
from app import app
from database.db import init_db, get_db


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("DATABASE", str(tmp_path / "test.db"))
    app.config["TESTING"] = True
    with app.test_client() as client:
        with app.app_context():
            init_db()
        yield client


def test_register_get(client):
    r = client.get("/register")
    assert r.status_code == 200


def test_register_success(client):
    r = client.post("/register", data={
        "name": "Test User", "email": "test@example.com", "password": "secret123"
    })
    assert r.status_code == 302
    assert "/dashboard" in r.headers["Location"]


def test_register_duplicate_email(client):
    data = {"name": "A", "email": "dup@example.com", "password": "secret123"}
    client.post("/register", data=data)
    r = client.post("/register", data=data)
    assert r.status_code == 400
    assert b"already exists" in r.data


def test_register_missing_name(client):
    r = client.post("/register", data={"name": "", "email": "a@b.com", "password": "secret123"})
    assert r.status_code == 400


def test_register_missing_email(client):
    r = client.post("/register", data={"name": "A", "email": "", "password": "secret123"})
    assert r.status_code == 400


def test_register_missing_password(client):
    r = client.post("/register", data={"name": "A", "email": "a@b.com", "password": ""})
    assert r.status_code == 400


def test_register_invalid_email(client):
    r = client.post("/register", data={"name": "A", "email": "notanemail", "password": "secret123"})
    assert r.status_code == 400
    assert b"valid email" in r.data


def test_register_short_password(client):
    r = client.post("/register", data={"name": "A", "email": "a@b.com", "password": "short"})
    assert r.status_code == 400
    assert b"8 characters" in r.data


def test_password_is_hashed(client, tmp_path, monkeypatch):
    monkeypatch.setenv("DATABASE", str(tmp_path / "test.db"))
    with app.app_context():
        init_db()
    client.post("/register", data={
        "name": "A", "email": "hash@example.com", "password": "plaintext123"
    })
    with app.app_context():
        db = get_db()
        row = db.execute(
            "SELECT password_hash FROM users WHERE email = ?", ("hash@example.com",)
        ).fetchone()
    assert row["password_hash"] != "plaintext123"
    assert len(row["password_hash"]) > 20
