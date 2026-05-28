from __future__ import annotations

from typing import Optional

from arena_forge.core.domain import CredentialRecord

try:
    import keyring
except ModuleNotFoundError:  # pragma: no cover - optional runtime dependency
    keyring = None


def _resolve_delete_secret_failures() -> tuple[type[BaseException], ...]:
    if keyring is None:
        return (OSError,)
    errors_module = getattr(keyring, "errors", None)
    keyring_errors = tuple(
        error_type
        for error_type in (
            getattr(errors_module, "PasswordDeleteError", None),
            getattr(errors_module, "KeyringError", None),
        )
        if isinstance(error_type, type) and issubclass(error_type, BaseException)
    )
    return keyring_errors + (OSError,)


_DELETE_SECRET_FAILURES = _resolve_delete_secret_failures()


class KeyringCredentialStore:
    def __init__(self, service_namespace: str) -> None:
        self.service_namespace = service_namespace
        self.backend_name = "keyring" if keyring is not None else "unavailable"

    def is_available(self) -> bool:
        return keyring is not None

    def _service_name(self, provider_name: str) -> str:
        return f"{self.service_namespace}:{provider_name}"

    def get_credentials(self, provider_name: str) -> Optional[CredentialRecord]:
        if keyring is None:
            return None
        service_name = self._service_name(provider_name)
        username = keyring.get_password(service_name, "__username__")
        if not username:
            return None
        secret = keyring.get_password(service_name, username)
        if secret is None:
            return None
        return CredentialRecord(username=username, secret=secret)

    def set_credentials(self, provider_name: str, username: str, secret: str) -> CredentialRecord:
        if keyring is None:
            raise RuntimeError("keyring backend is unavailable")
        service_name = self._service_name(provider_name)
        previous_username = keyring.get_password(service_name, "__username__")
        keyring.set_password(service_name, username, secret)
        if previous_username and previous_username != username:
            self._delete_secret(service_name, previous_username)
        keyring.set_password(service_name, "__username__", username)
        return CredentialRecord(username=username, secret=secret)

    def _delete_secret(self, service_name: str, username: str) -> None:
        delete_password = getattr(keyring, "delete_password", None)
        if delete_password is None:
            return
        try:
            delete_password(service_name, username)
        except _DELETE_SECRET_FAILURES:
            return


def build_credential_store(service_namespace: str) -> KeyringCredentialStore:
    return KeyringCredentialStore(service_namespace)
