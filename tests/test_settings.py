"""Unit tests for settings service using mocks."""
from unittest.mock import MagicMock


def test_get_event_settings_existing():
    """Test getting existing event settings."""
    from app.services.settings import get_event_settings


    mock_db = MagicMock()


    mock_settings = MagicMock()
    mock_settings.value = {"auto_approve": False}


    mock_query = mock_db.query.return_value
    mock_filter = mock_query.filter.return_value
    mock_filter.first.return_value = mock_settings


    result = get_event_settings(mock_db)


    assert result == {"auto_approve": False}

    mock_db.query.assert_called_once()
    mock_filter.first.assert_called_once()


def test_get_event_settings_not_existing():
    """Test getting settings when they don't exist."""
    from app.services.settings import get_event_settings


    mock_db = MagicMock()


    mock_query = mock_db.query.return_value
    mock_filter = mock_query.filter.return_value
    mock_filter.first.return_value = None


    mock_db.add = MagicMock()
    mock_db.commit = MagicMock()
    mock_db.refresh = MagicMock()


    result = get_event_settings(mock_db)

    assert result == {"auto_approve": True}


    mock_db.add.assert_called_once()
    mock_db.commit.assert_called_once()


def test_update_auto_approve_setting_existing():
    """Test updating existing auto_approve setting."""
    from app.services.settings import update_auto_approve_setting


    mock_db = MagicMock()


    mock_settings = MagicMock()
    mock_settings.value = {"auto_approve": False}

    mock_query = mock_db.query.return_value
    mock_filter = mock_query.filter.return_value
    mock_filter.first.return_value = mock_settings


    mock_db.commit = MagicMock()
    mock_db.refresh = MagicMock()


    result = update_auto_approve_setting(mock_db, True)


    assert result == {"auto_approve": True}
    assert mock_settings.value["auto_approve"] is True


    mock_db.commit.assert_called_once()
    mock_db.refresh.assert_called_once_with(mock_settings)


def test_update_auto_approve_setting_not_existing():
    """Test updating auto_approve when settings don't exist."""
    from app.services.settings import update_auto_approve_setting


    mock_db = MagicMock()


    mock_query = mock_db.query.return_value
    mock_filter = mock_query.filter.return_value
    mock_filter.first.return_value = None


    mock_db.add = MagicMock()
    mock_db.commit = MagicMock()
    mock_db.refresh = MagicMock()

    result = update_auto_approve_setting(mock_db, False)


    assert result == {"auto_approve": False}

    mock_db.add.assert_called_once()
    mock_db.commit.assert_called_once()
    mock_db.refresh.assert_called_once()
