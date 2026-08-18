import os
import tempfile

import pytest

import app as app_module
from models import db, UploadedFile


@pytest.fixture
def client_and_tmp(monkeypatch):
    tmpdir = tempfile.mkdtemp(prefix="crm_delete_")
    monkeypatch.setattr(app_module, "DRAFT_DIR", tmpdir)

    app_module.app.config["TESTING"] = True
    with app_module.app.app_context():
        db.create_all()
        yield app_module.app.test_client(), tmpdir
        db.session.remove()
        db.drop_all()


def test_delete_file_requires_confirmation_and_removes_record_and_disk_file(client_and_tmp):
    client, tmpdir = client_and_tmp

    with client.session_transaction() as sess:
        sess["username"] = "uploader"

    file_key = "report_2026"
    draft_path = os.path.join(tmpdir, f"uploader_{file_key}_draft.xlsx")
    with open(draft_path, "wb") as handle:
        handle.write(b"test")

    with app_module.app.app_context():
        record = UploadedFile(
            username="uploader",
            key=file_key,
            filename="report_2026.xlsx",
            file_path=draft_path,
            size_bytes=4,
        )
        db.session.add(record)
        db.session.commit()

    response = client.post(f"/delete/{file_key}")
    assert response.status_code == 200, response.get_data(as_text=True)
    payload = response.get_json()
    assert payload["ok"] is True
    assert not os.path.exists(draft_path)

    with app_module.app.app_context():
        assert UploadedFile.query.filter_by(username="uploader", key=file_key).count() == 0


def test_delete_file_handles_missing_physical_file_without_error(client_and_tmp):
    client, tmpdir = client_and_tmp

    with client.session_transaction() as sess:
        sess["username"] = "uploader"

    file_key = "missing_file"
    draft_path = os.path.join(tmpdir, f"uploader_{file_key}_draft.xlsx")

    with app_module.app.app_context():
        record = UploadedFile(
            username="uploader",
            key=file_key,
            filename="missing_file.xlsx",
            file_path=draft_path,
            size_bytes=0,
        )
        db.session.add(record)
        db.session.commit()

    response = client.post(f"/delete/{file_key}")
    assert response.status_code == 200, response.get_data(as_text=True)
    payload = response.get_json()
    assert payload["ok"] is True
    assert payload["message"] == "File deleted successfully."

    with app_module.app.app_context():
        assert UploadedFile.query.filter_by(username="uploader", key=file_key).count() == 0
