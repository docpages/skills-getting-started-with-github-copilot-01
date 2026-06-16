"""
Backend tests for Mergington High School FastAPI application.

Tests are structured using the Arrange-Act-Assert (AAA) pattern.
"""

import pytest
import copy
from fastapi.testclient import TestClient
from src.app import app, activities


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


@pytest.fixture(autouse=True)
def reset_activities():
    """Reset activities to initial state before each test to ensure isolation."""
    # Store the original state
    original_activities = copy.deepcopy(activities)
    
    yield
    
    # Restore the original state after the test
    activities.clear()
    activities.update(original_activities)


class TestGetActivities:
    """Tests for GET /activities endpoint."""

    def test_get_activities_returns_all_activities(self, client):
        """Test that GET /activities returns the full activities dictionary."""
        # Arrange
        expected_keys = {
            "Chess Club",
            "Programming Class",
            "Gym Class",
            "Basketball Team",
            "Tennis Club",
            "Art Studio",
            "Drama Club",
            "Science Club",
            "Debate Team",
        }

        # Act
        response = client.get("/activities")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert set(data.keys()) == expected_keys
        assert all(
            "description" in activity
            and "schedule" in activity
            and "max_participants" in activity
            and "participants" in activity
            for activity in data.values()
        )

    def test_get_activities_returns_participants(self, client):
        """Test that activities include their current participants."""
        # Arrange
        # Act
        response = client.get("/activities")

        # Assert
        data = response.json()
        chess_club = data["Chess Club"]
        assert len(chess_club["participants"]) == 2
        assert "michael@mergington.edu" in chess_club["participants"]
        assert "daniel@mergington.edu" in chess_club["participants"]


class TestSignupForActivity:
    """Tests for POST /activities/{activity_name}/signup endpoint."""

    def test_signup_new_student_succeeds(self, client):
        """Test that a new student can successfully sign up for an activity."""
        # Arrange
        activity_name = "Chess Club"
        email = "newstudent@mergington.edu"

        # Act
        response = client.post(
            f"/activities/{activity_name}/signup?email={email}",
            params={"email": email},
        )

        # Assert
        assert response.status_code == 200
        assert response.json()["message"] == f"Signed up {email} for {activity_name}"
        assert email in activities[activity_name]["participants"]

    def test_signup_duplicate_email_fails(self, client):
        """Test that signing up with an email already in the activity returns 400."""
        # Arrange
        activity_name = "Chess Club"
        email = "michael@mergington.edu"

        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email},
        )

        # Assert
        assert response.status_code == 400
        assert response.json()["detail"] == "Student already signed up"

    def test_signup_nonexistent_activity_fails(self, client):
        """Test that signing up for a non-existent activity returns 404."""
        # Arrange
        activity_name = "Nonexistent Club"
        email = "student@mergington.edu"

        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email},
        )

        # Assert
        assert response.status_code == 404
        assert response.json()["detail"] == "Activity not found"

    def test_signup_updates_participant_count(self, client):
        """Test that signup correctly updates the participant count."""
        # Arrange
        activity_name = "Tennis Club"
        initial_count = len(activities[activity_name]["participants"])
        email = "newsignup@mergington.edu"

        # Act
        client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email},
        )

        # Assert
        assert len(activities[activity_name]["participants"]) == initial_count + 1


class TestRemoveFromActivity:
    """Tests for POST /activities/{activity_name}/remove endpoint."""

    def test_remove_participant_succeeds(self, client):
        """Test that removing an existing participant succeeds."""
        # Arrange
        activity_name = "Chess Club"
        email = "michael@mergington.edu"

        # Act
        response = client.post(
            f"/activities/{activity_name}/remove",
            params={"email": email},
        )

        # Assert
        assert response.status_code == 200
        assert response.json()["message"] == f"Removed {email} from {activity_name}"
        assert email not in activities[activity_name]["participants"]

    def test_remove_nonexistent_participant_fails(self, client):
        """Test that removing a non-existent participant returns 404."""
        # Arrange
        activity_name = "Chess Club"
        email = "notregistered@mergington.edu"

        # Act
        response = client.post(
            f"/activities/{activity_name}/remove",
            params={"email": email},
        )

        # Assert
        assert response.status_code == 404
        assert response.json()["detail"] == "Student not found in activity"

    def test_remove_from_nonexistent_activity_fails(self, client):
        """Test that removing from a non-existent activity returns 404."""
        # Arrange
        activity_name = "Nonexistent Club"
        email = "student@mergington.edu"

        # Act
        response = client.post(
            f"/activities/{activity_name}/remove",
            params={"email": email},
        )

        # Assert
        assert response.status_code == 404
        assert response.json()["detail"] == "Activity not found"

    def test_remove_updates_participant_count(self, client):
        """Test that removal correctly updates the participant count."""
        # Arrange
        activity_name = "Chess Club"
        initial_count = len(activities[activity_name]["participants"])
        email = "michael@mergington.edu"

        # Act
        client.post(
            f"/activities/{activity_name}/remove",
            params={"email": email},
        )

        # Assert
        assert len(activities[activity_name]["participants"]) == initial_count - 1
