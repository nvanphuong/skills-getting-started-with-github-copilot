from copy import deepcopy
import unittest

from fastapi.testclient import TestClient

from src.app import activities, app


class ActivityAPITests(unittest.TestCase):
    def setUp(self):
        self.original_activities = deepcopy(activities)
        self.addCleanup(self.restore_activities)
        self.client = TestClient(app)
        self.addCleanup(self.client.close)

    def restore_activities(self):
        activities.clear()
        activities.update(self.original_activities)

    def test_root_redirects_to_activity_page(self):
        # Arrange
        url = "/"

        # Act
        response = self.client.get(url, follow_redirects=False)

        # Assert
        self.assertEqual(response.status_code, 307)
        self.assertEqual(response.headers["location"], "/static/index.html")

    def test_root_serves_activity_page(self):
        # Arrange
        url = "/"

        # Act
        response = self.client.get(url)

        # Assert
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.url.path, "/static/index.html")
        self.assertIn("text/html", response.headers["content-type"])
        self.assertIn('id="activities-list"', response.text)
        self.assertIn('id="signup-form"', response.text)

    def test_static_assets_are_served(self):
        # Arrange
        assets = (
            ("app.js", "javascript"),
            ("styles.css", "text/css"),
        )

        for filename, content_type in assets:
            with self.subTest(filename=filename):
                # Act
                response = self.client.get(f"/static/{filename}")

                # Assert
                self.assertEqual(response.status_code, 200)
                self.assertIn(content_type, response.headers["content-type"])
                self.assertTrue(response.content)

    def test_get_activities_returns_details_without_mutation(self):
        # Arrange
        url = "/activities"

        # Act
        response = self.client.get(url)

        # Assert
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), self.original_activities)
        for activity in response.json().values():
            self.assertIsInstance(activity["description"], str)
            self.assertIsInstance(activity["schedule"], str)
            self.assertIsInstance(activity["max_participants"], int)
            self.assertIsInstance(activity["participants"], list)
        self.assertTrue(response.json()["Chess Club"]["participants"])
        self.assertEqual(response.json()["Art Club"]["participants"], [])
        self.assertEqual(activities, self.original_activities)

    def test_signup_is_visible_in_subsequent_activity_listing(self):
        # Arrange
        email = "student+chess@mergington.edu"
        expected = deepcopy(self.original_activities)
        expected["Chess Club"]["participants"].append(email)

        # Act
        response = self.client.post(
            "/activities/Chess%20Club/signup", params={"email": email}
        )
        updated = self.client.get("/activities")

        # Assert
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {"message": f"Signed up {email} for Chess Club"},
        )
        self.assertEqual(updated.status_code, 200)
        self.assertEqual(updated.json(), expected)

    def test_signup_unknown_activity_does_not_mutate_state(self):
        # Arrange
        email = "student@mergington.edu"

        # Act
        response = self.client.post(
            "/activities/Unknown/signup",
            params={"email": email},
        )

        # Assert
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json(), {"detail": "Activity not found"})
        self.assertEqual(activities, self.original_activities)

    def test_missing_email_does_not_mutate_state(self):
        # Arrange
        requests = (("POST", "signup"), ("DELETE", "unregister"))

        for method, action in requests:
            with self.subTest(action=action):
                # Act
                response = self.client.request(
                    method, f"/activities/Chess%20Club/{action}"
                )

                # Assert
                self.assertEqual(response.status_code, 422)
                self.assertTrue(
                    any(
                        error["loc"] == ["query", "email"]
                        for error in response.json()["detail"]
                    )
                )
                self.assertEqual(activities, self.original_activities)

    def test_missing_static_asset_returns_not_found(self):
        # Arrange
        url = "/static/does-not-exist.css"

        # Act
        response = self.client.get(url)

        # Assert
        self.assertEqual(response.status_code, 404)

    def test_unregister_removes_only_selected_participant(self):
        # Arrange
        email = "michael@mergington.edu"

        # Act
        response = self.client.delete(
            "/activities/Chess%20Club/unregister",
            params={"email": email},
        )
        updated = self.client.get("/activities")

        # Assert
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {"message": "Unregistered michael@mergington.edu from Chess Club"},
        )
        self.assertEqual(updated.status_code, 200)
        self.assertEqual(
            updated.json()["Chess Club"]["participants"], ["daniel@mergington.edu"]
        )
        self.assertEqual(
            updated.json()["Programming Class"],
            self.original_activities["Programming Class"],
        )

    def test_unregister_unknown_activity(self):
        # Arrange
        email = "michael@mergington.edu"

        # Act
        response = self.client.delete(
            "/activities/Unknown/unregister",
            params={"email": email},
        )

        # Assert
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json(), {"detail": "Activity not found"})
        self.assertEqual(activities, self.original_activities)

    def test_unregister_unknown_participant(self):
        # Arrange
        email = "missing@mergington.edu"

        # Act
        response = self.client.delete(
            "/activities/Chess%20Club/unregister",
            params={"email": email},
        )

        # Assert
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json(), {"detail": "Participant not found"})
        self.assertEqual(activities, self.original_activities)

    def test_repeated_unregister_does_not_remove_other_participants(self):
        # Arrange
        params = {"email": "michael@mergington.edu"}
        expected = deepcopy(self.original_activities)
        expected["Chess Club"]["participants"].remove(params["email"])

        # Act
        first_response = self.client.delete(
            "/activities/Chess%20Club/unregister", params=params
        )
        response = self.client.delete(
            "/activities/Chess%20Club/unregister", params=params
        )
        updated = self.client.get("/activities")

        # Assert
        self.assertEqual(first_response.status_code, 200)
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json(), {"detail": "Participant not found"})
        self.assertEqual(updated.status_code, 200)
        self.assertEqual(updated.json(), expected)

    def test_unregister_last_participant_leaves_empty_list(self):
        # Arrange
        emails = self.original_activities["Chess Club"]["participants"]

        # Act
        responses = [
            self.client.delete(
                "/activities/Chess%20Club/unregister", params={"email": email}
            )
            for email in emails
        ]
        updated = self.client.get("/activities")

        # Assert
        for response in responses:
            self.assertEqual(response.status_code, 200)
        self.assertEqual(updated.status_code, 200)
        self.assertEqual(updated.json()["Chess Club"]["participants"], [])

    def test_unregistered_participant_can_sign_up_again(self):
        # Arrange
        email = "michael@mergington.edu"
        self.client.delete(
            "/activities/Chess%20Club/unregister", params={"email": email}
        )

        # Act
        response = self.client.post(
            "/activities/Chess%20Club/signup",
            params={"email": email},
        )
        updated = self.client.get("/activities")

        # Assert
        self.assertEqual(response.status_code, 200)
        self.assertEqual(updated.status_code, 200)
        self.assertEqual(
            updated.json()["Chess Club"]["participants"],
            ["daniel@mergington.edu", email],
        )
