from __future__ import annotations

from faker import Faker
import pytest

from pages.mobile.profile_editing_page import MobileProfileEditingPage
from pages.mobile.profile_page import MobileProfilePage
from pages.mobile.root_navigation import RootNavigation


pytestmark = pytest.mark.mobile

_faker = Faker()

# Both first and last name are required to save (see
# `profile_editing_cubit.dart::_validate`) — the shared test account has no
# last name set, so these fall back to a real value rather than resaving it
# blank, which the app wouldn't accept anyway.
_FALLBACK_FIRST_NAME = "Aleksandr"
_FALLBACK_LAST_NAME = "Kovalev"


@pytest.mark.smoke
def test_edit_profile_name_is_saved(logged_in_page) -> None:
    RootNavigation(logged_in_page).go_to_profile()
    profile_page = MobileProfilePage(logged_in_page)
    profile_page.is_loaded()
    profile_page.open_edit()

    editing_page = MobileProfileEditingPage(logged_in_page)
    editing_page.is_loaded()
    original_first_name = editing_page.first_name_input.input_value() or _FALLBACK_FIRST_NAME
    original_last_name = editing_page.last_name_input.input_value() or _FALLBACK_LAST_NAME
    new_first_name = _faker.first_name()

    try:
        editing_page.set_first_name(new_first_name)
        editing_page.set_last_name(original_last_name)
        editing_page.save()

        profile_page.is_loaded()
        profile_page.expect_name(new_first_name)
    finally:
        profile_page.open_edit()
        editing_page.is_loaded()
        editing_page.set_first_name(original_first_name)
        editing_page.set_last_name(original_last_name)
        editing_page.save()
        profile_page.is_loaded()


@pytest.mark.negative
def test_edit_profile_with_empty_name_is_rejected(logged_in_page) -> None:
    RootNavigation(logged_in_page).go_to_profile()
    profile_page = MobileProfilePage(logged_in_page)
    profile_page.is_loaded()
    profile_page.open_edit()

    editing_page = MobileProfileEditingPage(logged_in_page)
    editing_page.is_loaded()
    editing_page.set_first_name("")
    editing_page.save()

    editing_page.is_loaded()
