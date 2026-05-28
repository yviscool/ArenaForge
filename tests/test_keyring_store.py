import unittest
from unittest.mock import patch

from arena_forge.adapters.security.keyring_store import KeyringCredentialStore


class _FakeKeyring:
    def __init__(self, *, delete_error=None) -> None:
        self.values = {}
        self.deleted = []
        self.delete_error = delete_error

    def get_password(self, service_name: str, username: str):
        return self.values.get((service_name, username))

    def set_password(self, service_name: str, username: str, secret: str) -> None:
        self.values[(service_name, username)] = secret

    def delete_password(self, service_name: str, username: str) -> None:
        if self.delete_error is not None:
            raise self.delete_error
        self.deleted.append((service_name, username))
        self.values.pop((service_name, username), None)


class KeyringStoreTests(unittest.TestCase):
    def test_set_credentials_replaces_old_secret_when_username_changes(self) -> None:
        fake_keyring = _FakeKeyring()
        fake_keyring.values[("arena:codeforces", "__username__")] = "old-user"
        fake_keyring.values[("arena:codeforces", "old-user")] = "old-secret"

        with patch("arena_forge.adapters.security.keyring_store.keyring", fake_keyring):
            store = KeyringCredentialStore("arena")
            record = store.set_credentials("codeforces", "new-user", "new-secret")

        self.assertEqual(record.username, "new-user")
        self.assertEqual(record.secret, "new-secret")
        self.assertEqual(fake_keyring.values[("arena:codeforces", "__username__")], "new-user")
        self.assertEqual(fake_keyring.values[("arena:codeforces", "new-user")], "new-secret")
        self.assertEqual(fake_keyring.deleted, [("arena:codeforces", "old-user")])

    def test_set_credentials_ignores_delete_errors_when_rotating_username(self) -> None:
        fake_keyring = _FakeKeyring(delete_error=OSError("backend failure"))
        fake_keyring.values[("arena:codeforces", "__username__")] = "old-user"
        fake_keyring.values[("arena:codeforces", "old-user")] = "old-secret"

        with patch("arena_forge.adapters.security.keyring_store.keyring", fake_keyring):
            store = KeyringCredentialStore("arena")
            record = store.set_credentials("codeforces", "new-user", "new-secret")

        self.assertEqual(record.username, "new-user")
        self.assertEqual(fake_keyring.values[("arena:codeforces", "__username__")], "new-user")
        self.assertEqual(fake_keyring.values[("arena:codeforces", "new-user")], "new-secret")


if __name__ == "__main__":
    unittest.main()
