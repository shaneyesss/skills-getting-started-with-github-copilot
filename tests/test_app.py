import sys
import copy
from fastapi.testclient import TestClient

# Ensure src is on path so we can import app
sys.path.append("src")

from app import app, activities

client = TestClient(app)


# fixture to reset activities before each test
import pytest

@pytest.fixture(autouse=True)
def reset_activities():
    # because activities is mutated in tests, restore original state
    original = {
        name: {
            "description": data["description"],
            "schedule": data["schedule"],
            "max_participants": data["max_participants"],
            "participants": list(data["participants"]),
        }
        for name, data in activities.items()
    }
    yield
    activities.clear()
    activities.update(copy.deepcopy(original))


def test_get_activities_returns_all():
    # Arrange: nothing special, baseline state is defined

    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, dict)
    assert "Chess Club" in data
    assert data["Chess Club"]["description"].startswith("Learn strategies")


def test_signup_adds_participant_and_prevents_duplicates():
    # Arrange
    activity = "Chess Club"
    email = "newstudent@mergington.edu"

    # Act: sign up first time
    res1 = client.post(f"/activities/{activity}/signup", params={"email": email})

    # Assert first request succeeded
    assert res1.status_code == 200
    assert "Signed up" in res1.json()["message"]

    # Act: fetch activities to confirm
    res2 = client.get("/activities")
    assert res2.status_code == 200
    assert email in res2.json()[activity]["participants"]

    # Act: attempt duplicate signup
    res3 = client.post(f"/activities/{activity}/signup", params={"email": email})

    # Assert duplicate rejected
    assert res3.status_code == 400
    assert "already signed up" in res3.json()["detail"]


def test_unregistration_removes_participant_and_errors_when_not_signed_up():
    # Arrange: ensure one known participant in Tennis Club
    activity = "Tennis Club"
    existing = activities[activity]["participants"][0]

    # Act: unregister existing user
    res1 = client.delete(f"/activities/{activity}/unregister", params={"email": existing})

    # Assert removal succeeded
    assert res1.status_code == 200
    assert existing not in activities[activity]["participants"]

    # Act: attempt to unregister again
    res2 = client.delete(f"/activities/{activity}/unregister", params={"email": existing})

    # Assert error
    assert res2.status_code == 400
    assert "not signed up" in res2.json()["detail"]
