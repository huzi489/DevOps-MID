import pytest

from app.app import create_app

VALID = {
    "name": "Ali Khan",
    "registration_number": "FA22-BCS-001",
    "assignment_title": "Lab 3",
    "submission_url": "https://github.com/ali/lab3",
}


@pytest.fixture
def client(tmp_path):
    return create_app(str(tmp_path / "subs.json")).test_client()


def test_valid_submission_is_saved_and_listed(client):
    r = client.post("/submit", json=VALID)
    assert r.status_code == 201
    listed = client.get("/submissions").get_json()
    assert VALID in listed


def test_missing_registration_number_is_rejected_with_message(client):
    data = {**VALID, "registration_number": ""}
    r = client.post("/submit", json=data)
    assert r.status_code == 400
    assert "Registration number is required" in r.get_json()["errors"]["registration_number"]
    assert client.get("/submissions").get_json() == []


def test_invalid_url_is_rejected_and_not_saved(client):
    r = client.post("/submit", json={**VALID, "submission_url": "not a url"})
    assert r.status_code == 400
    assert "submission_url" in r.get_json()["errors"]
    assert client.get("/submissions").get_json() == []
