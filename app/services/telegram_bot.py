"""Telegram Bot API utilities for sending messages and managing bot interactions."""

import os
from typing import Any

import httpx

from app.core.logging import app_logger


class TelegramBotService:
    """Service for interacting with Telegram Bot API."""

    BASE_URL = "https://api.telegram.org"
    ADMIN_CHAT_ID = -4725261280  # Hard-coded admin group chat ID

    def __init__(self):
        """Initialize the Telegram bot service with token from environment."""
        self.token = os.getenv("TELEGRAM_TOKEN", "")
        if not self.token:
            app_logger.warning("TELEGRAM_TOKEN not set in environment")

    def _get_api_url(self, method: str) -> str:
        """Get the full API URL for a Telegram Bot API method."""
        return f"{self.BASE_URL}/bot{self.token}/{method}"

    async def send_message(
        self, chat_id: int, text: str, parse_mode: str = "HTML", **kwargs
    ) -> dict[str, Any]:
        """Send a text message to a chat.

        Args:
            chat_id: Chat ID to send to
            text: Message text
            parse_mode: Parse mode (HTML or Markdown)
            **kwargs: Additional parameters to pass to Telegram API

        Returns:
            Response from Telegram API
        """
        payload = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": parse_mode,
            **kwargs,
        }

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    self._get_api_url("sendMessage"),
                    json=payload,
                    timeout=30.0,
                )
                data = response.json()
                if not data.get("ok"):
                    app_logger.error(
                        f"Telegram API error: {data.get('description', 'Unknown error')}"
                    )
                    raise RuntimeError(f"Telegram API error: {data.get('description')}")
                return data.get("result", {})
            except Exception as e:
                app_logger.error(f"Error sending message to {chat_id}: {e}")
                raise

    async def send_poll(
        self,
        chat_id: int,
        question: str,
        options: list[str],
        is_anonymous: bool = False,
        allows_multiple_answers: bool = False,
    ) -> dict[str, Any]:
        """Send a poll to a chat.

        Args:
            chat_id: Chat ID to send to
            question: Poll question
            options: List of poll options
            is_anonymous: Whether poll is anonymous
            allows_multiple_answers: Whether multiple answers are allowed

        Returns:
            Response from Telegram API with poll data
        """
        payload = {
            "chat_id": chat_id,
            "question": question,
            "options": options,
            "is_anonymous": is_anonymous,
            "allows_multiple_answers": allows_multiple_answers,
            "type": "regular",
        }

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    self._get_api_url("sendPoll"),
                    json=payload,
                    timeout=30.0,
                )
                data = response.json()
                if not data.get("ok"):
                    app_logger.error(
                        f"Telegram API error: {data.get('description', 'Unknown error')}"
                    )
                    raise RuntimeError(f"Telegram API error: {data.get('description')}")
                return data.get("result", {})
            except Exception as e:
                app_logger.error(f"Error sending poll to {chat_id}: {e}")
                raise


# Singleton instance
telegram_service = TelegramBotService()
