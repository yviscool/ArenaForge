import unittest

from arena_forge.adapters.providers.submission_service import (
    CredentialBackendUnavailableError,
    MissingCredentialsError,
    ProviderSubmissionService,
    SubmissionLanguageError,
    SubmissionRequest,
    SubmissionUnsupportedError,
)
from arena_forge.core.domain import CredentialRecord, ProviderCapabilities, ProviderWorkspaceKind


class _FakeCredentialStore:
    def __init__(self, available=True, record=None):
        self.available = available
        self.record = record

    def is_available(self):
        return self.available

    def get_credentials(self, provider_name: str):
        return self.record

    def set_credentials(self, provider_name: str, username: str, secret: str):
        self.record = CredentialRecord(username=username, secret=secret)
        return self.record


class _FakeProvider:
    provider_name = "fake"

    def __init__(self):
        self.capabilities = ProviderCapabilities(
            workspace_kind=ProviderWorkspaceKind.CONTEST,
            supports_submission=True,
            requires_credentials=True,
        )
        self.calls = []

    def load_contest(self, contest_id: str):
        raise NotImplementedError

    def submit_solution(self, contest_id, problem_id, language_id, code, credentials):
        self.calls.append((contest_id, problem_id, language_id, code, credentials))


class _Registry:
    def __init__(self, provider):
        self.provider = provider

    def get(self, provider_name: str):
        return self.provider


class SubmissionServiceTests(unittest.TestCase):
    def test_submit_requires_supported_provider(self) -> None:
        provider = _FakeProvider()
        provider.capabilities = ProviderCapabilities()
        service = ProviderSubmissionService(_Registry(provider), _FakeCredentialStore(), {})
        with self.assertRaises(SubmissionUnsupportedError):
            service.submit(SubmissionRequest("fake", "1", "A", "C++", "code"))

    def test_submit_requires_backend_when_credentials_missing(self) -> None:
        provider = _FakeProvider()
        service = ProviderSubmissionService(
            _Registry(provider),
            _FakeCredentialStore(available=False),
            {"fake": {"cpp": 1}},
        )
        with self.assertRaises(CredentialBackendUnavailableError):
            service.submit(SubmissionRequest("fake", "1", "A", "C++", "code"))

    def test_submit_requires_language_mapping(self) -> None:
        provider = _FakeProvider()
        service = ProviderSubmissionService(
            _Registry(provider),
            _FakeCredentialStore(record=CredentialRecord(username="u", secret="s")),
            {"fake": {}},
        )
        with self.assertRaises(SubmissionLanguageError):
            service.submit(SubmissionRequest("fake", "1", "A", "Rust", "code"))

    def test_submit_uses_credentials_and_language_mapping(self) -> None:
        provider = _FakeProvider()
        record = CredentialRecord(username="u", secret="s")
        service = ProviderSubmissionService(
            _Registry(provider),
            _FakeCredentialStore(record=record),
            {"fake": {"cpp": 52}},
        )
        service.submit(SubmissionRequest("fake", "1", "A", "C++", "code"))
        self.assertEqual(provider.calls[0][2], 52)
        self.assertEqual(provider.calls[0][4], record)

    def test_submit_raises_when_credentials_missing(self) -> None:
        provider = _FakeProvider()
        service = ProviderSubmissionService(
            _Registry(provider),
            _FakeCredentialStore(record=None),
            {"fake": {"cpp": 1}},
        )
        with self.assertRaises(MissingCredentialsError):
            service.submit(SubmissionRequest("fake", "1", "A", "C++", "code"))


if __name__ == "__main__":
    unittest.main()
