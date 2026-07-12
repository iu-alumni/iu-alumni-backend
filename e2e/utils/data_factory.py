from __future__ import annotations

from dataclasses import dataclass, field
import uuid

from faker import Faker

from config import settings


_faker = Faker()


@dataclass(frozen=True, slots=True)
class TestUser:
    __test__ = False  # not a pytest test class, despite the name

    first_name: str
    last_name: str
    email: str
    password: str
    telegram_alias: str
    graduation_year: int


def unique_email(domain: str | None = None) -> str:
    domain = domain or settings.test_email_domain
    return f"e2e.{uuid.uuid4().hex[:12]}@{domain}"


def new_test_user(*, email: str | None = None, graduation_year: int | None = None) -> TestUser:
    return TestUser(
        first_name=_faker.first_name(),
        last_name=_faker.last_name(),
        email=email or unique_email(),
        password=settings.test_user_password,
        telegram_alias=f"e2e_{uuid.uuid4().hex[:8]}",
        graduation_year=graduation_year or _faker.random_int(min=2015, max=2024),
    )


def unique_event_title() -> str:
    return f"E2E Event {uuid.uuid4().hex[:8]}"


@dataclass(frozen=True, slots=True)
class TestEvent:
    __test__ = False  # not a pytest test class, despite the name

    title: str = field(default_factory=unique_event_title)
    description: str = "Created by an automated E2E test — safe to delete."
    # Full addresses don't reliably match a location-picker suggestion.
    location: str = "Innopolis"
