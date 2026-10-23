import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

import app as quote_app


class QuoteGeneratorTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        db = str(Path(self.temp_dir.name) / "test_quotes.db")
        self.app = quote_app.create_app({"TESTING": True, "DATABASE": db})
        self.client = self.app.test_client()

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_home_page_loads(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Quote Generator", response.data)

    def test_health_endpoint(self):
        response = self.client.get("/api/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["status"], "ok")

    @patch("app.requests.get")
    def test_random_quote_is_saved_to_history(self, mock_get):
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {"quote": "Test quote", "author": "Test Author"}
        mock_get.return_value = mock_response
        response = self.client.post("/api/quotes/random")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["quote"], "Test quote")
        history = self.client.get("/api/history").get_json()
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0]["author"], "Test Author")

    @patch("app.requests.get", side_effect=quote_app.requests.RequestException("offline"))
    def test_api_failure_uses_fallback(self, _mock_get):
        response = self.client.post("/api/quotes/random")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["source"], "fallback")
        self.assertTrue(response.get_json()["quote"])

    @patch("app.requests.get")
    def test_clear_history(self, mock_get):
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {"quote": "Test quote", "author": "Test Author"}
        mock_get.return_value = mock_response
        self.client.post("/api/quotes/random")
        response = self.client.delete("/api/history")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.client.get("/api/history").get_json(), [])


if __name__ == "__main__":
    unittest.main()
