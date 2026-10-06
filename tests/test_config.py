from src.config import Settings


def test_settings_load_correctly(monkeypatch):
    """
    Test that the settings class correctly loads environment variables.
    We use pytest's 'monkeypatch' fixture to temporarily set an env var
    just for this test.
    """
    # Temporarily set an environment variable
    monkeypatch.setenv("LLM_PROVIDER", "test-provider")
    monkeypatch.setenv("LLM_MODEL", "test-model")
    
    # Instantiate settings
    settings = Settings()
    
    # Assert that the settings picked up our environment variables
    assert settings.LLM_PROVIDER == "test-provider"
    assert settings.LLM_MODEL == "test-model"
    
    # Assert that defaults still work for things we didn't set
    assert settings.APP_ENV == "dev"
