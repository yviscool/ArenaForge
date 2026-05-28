from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from arena_forge.core.domain import CredentialRecord


class SubmissionServiceError(RuntimeError):
    message_key = "error.submission_failed"

    def __init__(self, message_key: Optional[str] = None, **context: object) -> None:
        super().__init__(message_key or self.message_key)
        self.message_key = message_key or self.message_key
        self.context = {key: str(value) for key, value in context.items()}


class SubmissionUnsupportedError(SubmissionServiceError):
    message_key = "error.provider_submission_unsupported"


class CredentialBackendUnavailableError(SubmissionServiceError):
    message_key = "error.credential_backend_unavailable"


class MissingCredentialsError(SubmissionServiceError):
    message_key = "error.credentials_missing"


class SubmissionLanguageError(SubmissionServiceError):
    message_key = "error.submission_language_unsupported"


class SubmissionDependencyUnavailableError(SubmissionServiceError):
    message_key = "error.submission_dependencies_unavailable"


class SubmissionTransportError(SubmissionServiceError):
    message_key = "error.submission_transport_failed"


_TRANSPORT_FAILURES = (OSError, ValueError)


def canonical_language_key(language_name: str) -> str:
    normalized = language_name.strip().lower()
    if "c++" in normalized or normalized == "cpp":
        return "cpp"
    if normalized.startswith("py"):
        return "py"
    if normalized.startswith("java"):
        return "java"
    return normalized


@dataclass(frozen=True)
class SubmissionRequest:
    provider_name: str
    contest_id: str
    problem_id: str
    language_name: str
    code: str


class ProviderSubmissionService:
    def __init__(self, provider_registry, credential_store, submission_language_ids: dict[str, dict[str, int]]):
        self.provider_registry = provider_registry
        self.credential_store = credential_store
        self.submission_language_ids = submission_language_ids

    def get_credentials(self, provider_name: str) -> Optional[CredentialRecord]:
        if self.credential_store is None or not self.credential_store.is_available():
            return None
        return self.credential_store.get_credentials(provider_name)

    def set_credentials(self, provider_name: str, username: str, secret: str) -> CredentialRecord:
        if self.credential_store is None or not self.credential_store.is_available():
            raise CredentialBackendUnavailableError()
        return self.credential_store.set_credentials(provider_name, username, secret)

    def submit(self, request: SubmissionRequest, credentials: Optional[CredentialRecord] = None) -> None:
        provider = self.provider_registry.get(request.provider_name)
        capabilities = getattr(provider, "capabilities", None)
        if capabilities is None or not capabilities.supports_submission:
            raise SubmissionUnsupportedError(provider=request.provider_name)

        if credentials is None:
            if self.credential_store is None or not self.credential_store.is_available():
                raise CredentialBackendUnavailableError(provider=request.provider_name)
            credentials = self.credential_store.get_credentials(request.provider_name)
            if credentials is None:
                raise MissingCredentialsError(provider=request.provider_name)

        provider_languages = self.submission_language_ids.get(request.provider_name, {})
        language_key = canonical_language_key(request.language_name)
        language_id = provider_languages.get(language_key)
        if language_id is None:
            raise SubmissionLanguageError(provider=request.provider_name, language=request.language_name)

        try:
            provider.submit_solution(
                request.contest_id,
                request.problem_id,
                language_id,
                request.code,
                credentials,
            )
        except SubmissionServiceError:
            raise
        except ModuleNotFoundError as exc:
            raise SubmissionDependencyUnavailableError(provider=request.provider_name) from exc
        except _TRANSPORT_FAILURES as exc:
            detail = str(exc).strip() or exc.__class__.__name__
            raise SubmissionTransportError(provider=request.provider_name, detail=detail) from exc
