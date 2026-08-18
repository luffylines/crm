import json
import os
import tempfile

import app as app_module
from models import db, User


def test_default_users_are_seeded_when_database_is_empty(monkeypatch):
    tmpdir = tempfile.mkdtemp(prefix="crm_seed_")
    users_file = os.path.join(tmpdir, "users.json")
    with open(users_file, "w", encoding="utf-8") as handle:
        json.dump({
            "users": [
                {"username": "chan", "password": "chan123"},
                {"username": "admin", "password": "admin123"},
            ]
        }, handle)

    monkeypatch.setattr(app_module, "__file__", os.path.join(tmpdir, "app.py"))
    monkeypatch.setattr(app_module, "__name__", "app")

    app_module.app.config["TESTING"] = True
    with app_module.app.app_context():
        db.drop_all()
        db.create_all()
        app_module.ensure_default_users(users_file)

        assert User.query.filter_by(username="chan").count() == 1
        assert User.query.filter_by(username="admin").count() == 1

        chan = User.query.filter_by(username="chan").first()
        admin = User.query.filter_by(username="admin").first()

        assert chan.check_password("chan123") is True
        assert admin.check_password("admin123") is True
        assert chan.role == "User"
        assert admin.role == "Admin"

        db.session.remove()
        db.drop_all()
