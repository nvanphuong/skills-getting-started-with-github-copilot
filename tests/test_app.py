from copy import deepcopy
import unittest

from fastapi.testclient import TestClient

from src.app import activities, app


class UnregisterTests(unittest.TestCase):
    def setUp(self):
        self.original_activities = deepcopy(activities)
        self.client = TestClient(app)

    def tearDown(self):
        activities.clear()
        activities.update(self.original_activities)
        self.client.close()

    def test_unregister_removes_only_selected_participant(self):
        response = self.client.delete(
            "/activities/Chess%20Club/unregister",
            params={"email": "michael@mergington.edu"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {"message": "Unregistered michael@mergington.edu from Chess Club"},
        )
        updated = self.client.get("/activities").json()
        self.assertEqual(
            updated["Chess Club"]["participants"], ["daniel@mergington.edu"]
        )
        self.assertEqual(
            updated["Programming Class"],
            self.original_activities["Programming Class"],
        )

    def test_unregister_unknown_activity(self):
        response = self.client.delete(
            "/activities/Unknown/unregister",
            params={"email": "michael@mergington.edu"},
        )

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json(), {"detail": "Activity not found"})
        self.assertEqual(activities, self.original_activities)

    def test_unregister_unknown_participant(self):
        response = self.client.delete(
            "/activities/Chess%20Club/unregister",
            params={"email": "missing@mergington.edu"},
        )

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json(), {"detail": "Participant not found"})
        self.assertEqual(activities, self.original_activities)

    def test_unregister_last_participant_and_sign_up_again(self):
        for email in self.original_activities["Chess Club"]["participants"]:
            response = self.client.delete(
                "/activities/Chess%20Club/unregister", params={"email": email}
            )
            self.assertEqual(response.status_code, 200)

        self.assertEqual(
            self.client.get("/activities").json()["Chess Club"]["participants"], []
        )
        response = self.client.post(
            "/activities/Chess%20Club/signup",
            params={"email": "michael@mergington.edu"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            activities["Chess Club"]["participants"], ["michael@mergington.edu"]
        )
