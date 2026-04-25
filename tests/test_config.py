import pytest

from ynab_mcp.config import Settings, SettingsError, get_settings


def test_get_settings_reads_token_from_environment():
    settings = get_settings({"YNAB_ACCESS_TOKEN": "pat-token"})

    assert settings == Settings(access_token="pat-token")


def test_get_settings_strips_surrounding_whitespace():
    settings = get_settings({"YNAB_ACCESS_TOKEN": "  pat-token  "})

    assert settings.access_token == "pat-token"


def test_get_settings_rejects_missing_token():
    with pytest.raises(SettingsError, match="YNAB_ACCESS_TOKEN"):
        get_settings({})


def test_get_settings_rejects_blank_token():
    with pytest.raises(SettingsError, match="YNAB_ACCESS_TOKEN"):
        get_settings({"YNAB_ACCESS_TOKEN": "   "})
