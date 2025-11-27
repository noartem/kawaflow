from typing import Any, Optional, Set

EXACT_SENSITIVE_KEYS = {
    "password",
    "passwd",
    "pwd",
    "secret",
    "token",
    "auth",
    "authorization",
    "credential",
    "private",
    "session",
    "cookie",
    "jwt",
    "bearer",
}

SENSITIVE_KEY_PATTERNS = {
    "api_key",
    "access_token",
    "refresh_token",
    "private_key",
    "secret_key",
    "auth_token",
    "session_token",
    "bearer_token",
    "jwt_token",
}

SENSITIVE_TEXT_PATTERNS = [
    "password=",
    "token=",
    "key=",
    "secret=",
    "auth=",
    "Bearer ",
    "Basic ",
    "jwt:",
    "api_key:",
]


class SensivityFilter:
    def __init__(
        self,
        exact_sensitive_keys=EXACT_SENSITIVE_KEYS,
        sensitive_key_patterns=SENSITIVE_KEY_PATTERNS,
        sensitive_text_patterns=SENSITIVE_TEXT_PATTERNS,
    ):
        self.exact_sensitive_keys = exact_sensitive_keys
        self.sensitive_key_patterns = sensitive_key_patterns
        self.sensitive_text_patterns = sensitive_text_patterns

    def __call__(self, data: Any, _seen: Optional[Set[int]] = None) -> Any:
        if data is None:
            return None

        if _seen is None:
            _seen = set()

        data_id = id(data)
        if data_id in _seen:
            return "[CIRCULAR_REFERENCE]"

        try:
            if isinstance(data, dict):
                _seen.add(data_id)
                filtered = {}
                for key, value in data.items():
                    if self.check_key(key) and not isinstance(value, (dict, list)):
                        filtered[key] = "[FILTERED]"
                    else:
                        filtered[key] = self.__call__(value, _seen)
                _seen.remove(data_id)
                return filtered

            elif isinstance(data, list):
                _seen.add(data_id)
                result = [self.__call__(item, _seen) for item in data]
                _seen.remove(data_id)
                return result

            elif isinstance(data, str):
                if self.check_text(data):
                    return "[FILTERED]"
                return data

            else:
                return data

        except (RecursionError, RuntimeError):
            return "[RECURSION_ERROR]"

    def check_key(self, key: str) -> bool:
        return key.lower() in self.exact_sensitive_keys or any(
            pattern in key.lower() for pattern in self.sensitive_key_patterns
        )

    def check_text(self, text: str) -> bool:
        return any(
            pattern.lower() in text.lower() for pattern in self.sensitive_text_patterns
        )

    def check_data(self, data: Any) -> bool:
        if isinstance(data, dict):
            return any(
                self.check_key(key) or self.check_data(value)
                for key, value in data.items()
            )
        elif isinstance(data, list):
            return any(self.check_data(item) for item in data)
        elif isinstance(data, str):
            return self.check_text(data)
        else:
            return False
