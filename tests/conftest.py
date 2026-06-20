import pytest
import database.db as db_module
from app import app as flask_app


@pytest.fixture
def app(tmp_path):
    db_file = tmp_path / "test.db"
    flask_app.config["TESTING"] = True
    flask_app.config["SECRET_KEY"] = "test-secret"
    original = db_module.DB_PATH
    db_module.DB_PATH = str(db_file)
    db_module.init_db()
    yield flask_app
    db_module.DB_PATH = original


@pytest.fixture
def client(app):
    return app.test_client()
