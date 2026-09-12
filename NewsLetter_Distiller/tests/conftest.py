import pytest

# Every environment variable the tool reads (newsletter_distiller.config,
# newsletter_distiller.ai.provider). Tests must not depend on — or be
# broken by — whatever happens to be exported in the developer's shell
# (e.g. from trying the README's usage examples).
_ISOLATED_ENV_VARS = (
    "NEWSLETTER_DISTILLER_PROVIDER",
    "NEWSLETTER_DISTILLER_MODEL",
    "NEWSLETTER_DISTILLER_BASE_URL",
    "NEWSLETTER_DISTILLER_VISION",
    "NEWSLETTER_DISTILLER_API_KEY",
    "ANTHROPIC_API_KEY",
)


@pytest.fixture(autouse=True)
def _isolated_env(monkeypatch):
    """Clear the tool's env vars before every test; tests that need one
    set it explicitly via monkeypatch.setenv.
    """
    for var in _ISOLATED_ENV_VARS:
        monkeypatch.delenv(var, raising=False)
