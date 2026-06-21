import logging
import sys

from app.core.logging import app_logger, setup_logging


def test_setup_logging_development(monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "DEV")
    logger = setup_logging()
    assert logger is not None
    assert logger.level == logging.DEBUG
    console_handlers = [h for h in logger.handlers if isinstance(h, logging.StreamHandler)]
    assert len(console_handlers) > 0
    file_handlers = [h for h in logger.handlers if isinstance(h, logging.handlers.RotatingFileHandler)]
    assert len(file_handlers) == 0


def test_setup_logging_production(monkeypatch, tmp_path):
    monkeypatch.setenv("ENVIRONMENT", "PROD")
    monkeypatch.chdir(tmp_path)
    logger = setup_logging()
    assert logger is not None
    assert logger.level == logging.INFO
    console_handlers = [h for h in logger.handlers if isinstance(h, logging.StreamHandler)]
    assert len(console_handlers) > 0
    file_handlers = [h for h in logger.handlers if isinstance(h, logging.handlers.RotatingFileHandler)]
    assert len(file_handlers) > 0


def test_setup_logging_removes_existing_handlers(monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "DEV")
    logger = logging.getLogger()
    dummy_handler = logging.StreamHandler(sys.stdout)
    logger.addHandler(dummy_handler)
    initial_handlers_count = len(logger.handlers)
    setup_logging()
    assert len(logger.handlers) < initial_handlers_count


def test_app_logger_exists():
    assert app_logger is not None
    assert app_logger.name == "iu_alumni"


def test_specific_logger_levels(monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "DEV")
    setup_logging()
    uvicorn_logger = logging.getLogger("uvicorn")
    sqlalchemy_logger = logging.getLogger("sqlalchemy.engine")
    assert uvicorn_logger.level == logging.INFO
    assert sqlalchemy_logger.level == logging.WARNING
