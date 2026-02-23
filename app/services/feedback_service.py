"""Service for managing polls and feedback."""

import os
from typing import Any

from sqlalchemy.orm import Session

from app.core.logging import app_logger
from app.models.telegram import Feedback, Poll
from app.services.telegram_bot import telegram_service


FEEDBACK_QUESTIONS = [
    {
        "question": "How relevant and valuable do you find our innovative approach?\n1 — not valuable at all, 5 — very valuable\n\n"
        "Насколько актуальным и ценным вы считаете наш инновационный подход?\n1 — совсем не ценно, 5 — очень ценно",
        "options": ["1", "2", "3", "4", "5"],
    },
    {
        "question": "How intuitive does the app seem for creating and joining events?\n1 — not intuitive at all, 5 — completely clear\n\n"
        "Насколько интуитивным кажется приложение для создания и присоединения к событиям?\n1 — совсем не интуитивно, 5 — абсолютно понятно",
        "options": ["1", "2", "3", "4", "5"],
    },
    {
        "question": "How likely are you to recommend the app to your classmates?\n1 — not likely at all, 5 — extremely likely\n\n"
        "Насколько вероятно, что вы порекомендуете приложение своим однокурсникам?\n1 — совсем не вероятно, 5 — крайне вероятно",
        "options": ["1", "2", "3", "4", "5"],
    },
]


class FeedbackService:
    """Service for managing feedback polls and responses."""

    @staticmethod
    async def send_feedback_polls(db: Session, chat_id: int) -> None:
        """Send all feedback polls to a user.

        Args:
            db: Database session
            chat_id: Chat ID to send polls to
        """
        for poll_data in FEEDBACK_QUESTIONS:
            try:
                result = await telegram_service.send_poll(
                    chat_id=chat_id,
                    question=poll_data["question"],
                    options=poll_data["options"],
                    is_anonymous=False,
                    allows_multiple_answers=False,
                )

                if result and "id" in result:
                    poll_id = result["id"]
                    # Save poll to database
                    poll = Poll(
                        poll_id=poll_id,
                        question=poll_data["question"],
                        options=poll_data["options"],
                    )
                    db.add(poll)
                    db.commit()
                    app_logger.info(f"Sent poll {poll_id} to chat {chat_id}")
            except Exception as e:
                app_logger.error(f"Error sending feedback poll: {e}")
                db.rollback()

    @staticmethod
    def process_poll_answer(
        db: Session, poll_id: str, option_ids: list[int], alias: str
    ) -> dict[str, Any]:
        """Process a poll answer from a user.

        Args:
            db: Database session
            poll_id: ID of the poll answered
            option_ids: List of option indices selected
            alias: User's Telegram alias

        Returns:
            Status dictionary
        """
        try:
            # Get poll from database
            poll = db.query(Poll).filter(Poll.poll_id == poll_id).first()

            if not poll:
                app_logger.warning(f"Poll {poll_id} not found (timeout)")
                return {"status": "timeout"}

            # Convert option indices to answer text
            answer_options = [
                poll.options[i] for i in option_ids if i < len(poll.options)
            ]
            answer = ", ".join(answer_options)

            # Save feedback
            feedback = Feedback(
                alias=alias, question=poll.question, answer=answer
            )
            db.add(feedback)

            # Delete poll from database after processing
            db.delete(poll)
            db.commit()

            # Send to external webhook if configured
            if os.getenv("FEEDBACK_WEBHOOK_URL"):
                try:
                    import asyncio

                    import httpx

                    async def send_webhook():
                        async with httpx.AsyncClient() as client:
                            await client.post(
                                os.getenv("FEEDBACK_WEBHOOK_URL"),
                                json={
                                    "alias": alias,
                                    "question": poll.question,
                                    "answer": answer,
                                },
                                timeout=10.0,
                            )

                    asyncio.run(send_webhook())
                except Exception as e:
                    app_logger.error(f"Error sending feedback webhook: {e}")

            return {"status": "ok"}
        except Exception as e:
            app_logger.error(f"Error processing poll answer: {e}")
            db.rollback()
            return {"status": "error", "message": str(e)}

    @staticmethod
    def get_all_feedback(db: Session) -> list[dict[str, Any]]:
        """Get all feedback responses.

        Args:
            db: Database session

        Returns:
            List of feedback records
        """
        try:
            feedbacks = (
                db.query(Feedback)
                .order_by(Feedback.created_at.desc())
                .all()
            )
            return [
                {
                    "id": f.id,
                    "alias": f.alias,
                    "question": f.question,
                    "answer": f.answer,
                    "created_at": f.created_at.isoformat(),
                }
                for f in feedbacks
            ]
        except Exception as e:
            app_logger.error(f"Error retrieving feedback: {e}")
            return []
