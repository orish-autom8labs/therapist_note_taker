# Services module
# Lazy imports to avoid pulling in heavy dependencies (e.g., websockets,
# google-auth-oauthlib) when only a subset of services is needed.

__all__ = [
    'TranscriptionService',
    'DriveService',
    'EmailService',
]

_imports = {
    'TranscriptionService': '.transcription_service',
    'DriveService': '.drive_service',
    'EmailService': '.email_service',
}


def __getattr__(name):
    if name in _imports:
        import importlib
        module = importlib.import_module(_imports[name], __name__)
        return getattr(module, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
