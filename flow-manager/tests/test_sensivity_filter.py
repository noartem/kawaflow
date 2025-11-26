import pytest

from sensivity_filter import SensivityFilter


@pytest.fixture
def sensitive_filter():
    return SensivityFilter()


class TestSensitiveDataFiltering:

    def test_filter_sensitive_keys(self, sensitive_filter):
        data = {
            "username": "testuser",
            "password": "secret123",
            "api_key": "abc123",
            "normal_field": "normal_value",
        }

        filtered = sensitive_filter(data)

        assert filtered["username"] == "testuser"
        assert filtered["password"] == "[FILTERED]"
        assert filtered["api_key"] == "[FILTERED]"
        assert filtered["normal_field"] == "normal_value"

    def test_filter_nested_sensitive_data(self, sensitive_filter):
        data = {
            "config": {
                "database": {"host": "localhost", "password": "dbpass123"},
                "auth": {"secret": "jwt_secret", "public_key": "public_data"},
            },
            "users": [
                {"name": "user1", "token": "token123"},
                {"name": "user2", "role": "admin"},
            ],
        }

        filtered = sensitive_filter(data)

        assert filtered["config"]["database"]["host"] == "localhost"
        assert filtered["config"]["database"]["password"] == "[FILTERED]"
        assert filtered["config"]["auth"]["secret"] == "[FILTERED]"
        assert filtered["config"]["auth"]["public_key"] == "public_data"
        assert filtered["users"][0]["name"] == "user1"
        assert filtered["users"][0]["token"] == "[FILTERED]"
        assert filtered["users"][1]["name"] == "user2"
        assert filtered["users"][1]["role"] == "admin"

    def test_filter_sensitive_strings(self, sensitive_filter):
        sensitive_string = "Authorization: Bearer token123"
        normal_string = "This is a normal message"

        filtered_sensitive = sensitive_filter(sensitive_string)
        filtered_normal = sensitive_filter(normal_string)

        assert filtered_sensitive == "[FILTERED]"
        assert filtered_normal == "This is a normal message"

    def test_check_key(self, sensitive_filter):
        sensitive_keys = [
            "password",
            "PASSWORD",
            "api_key",
            "API_KEY",
            "secret",
            "token",
            "auth",
        ]
        normal_keys = ["username", "email", "name", "status", "data"]

        for key in sensitive_keys:
            assert sensitive_filter.check_key(key) is True

        for key in normal_keys:
            assert sensitive_filter.check_key(key) is False

    def test_check_text(self, sensitive_filter):
        sensitive_texts = [
            "password=secret123",
            "Bearer token123",
            "api_key:abc123",
            "Authorization: Basic dXNlcjpwYXNz",
        ]
        normal_texts = [
            "This is a normal message",
            "Container started successfully",
            "Status: running",
        ]

        for text in sensitive_texts:
            assert sensitive_filter.check_text(text) is True

        for text in normal_texts:
            assert sensitive_filter.check_text(text) is False

    def test_check_data(self, sensitive_filter):
        sensitive_data = {
            "config": {"password": "secret"},
            "message": "Bearer token123",
        }
        normal_data = {"status": "running", "message": "Container started"}

        assert sensitive_filter.check_data(sensitive_data) is True
        assert sensitive_filter.check_data(normal_data) is False
