"""Badge evaluation engine.

Given an alumni and a trigger metric, looks up every badge whose
trigger_metrics include the trigger, dispatches to the right strategy
implementation, and awards anything that just crossed the threshold.

Public entry points:
    evaluate_for_user(db, alumni, trigger) -> list[UserBadge]
    list_my_badges(db, alumni) -> dict   # for /profile/me/badges
    list_for_user(db, alumni_id) -> dict # public view
"""
from __future__ import annotations

from datetime import datetime
import logging
from typing import Any
import uuid

from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.badge import Badge, UserBadge
from app.models.events import Event
from app.models.users import Alumni


logger = logging.getLogger("iu_alumni")


# ─────────────────────────── progress helpers ──────────────────────────────


def _events_attended_count(db: Session, alumni_id: str) -> int:
    return (
        db.query(func.count(Event.id))
        .filter(Event.participants_ids.any(alumni_id))
        .scalar()
        or 0
    )


def _owned_events(db: Session, alumni_id: str) -> list[Event]:
    return db.query(Event).filter(Event.owner_id == alumni_id).all()


def _distinct_cities_hosted(db: Session, alumni_id: str) -> int:
    rows = (
        db.query(func.lower(func.trim(Event.location)))
        .filter(Event.owner_id == alumni_id, Event.approved.is_(True))
        .distinct()
        .all()
    )
    return len({r[0] for r in rows if r[0]})


def _max_attendees_on_owned(db: Session, alumni_id: str) -> int:
    owned = _owned_events(db, alumni_id)
    return max((len(e.participants_ids or []) for e in owned), default=0)


def _cross_city_attendances(db: Session, alumni: Alumni) -> int:
    if not alumni.location:
        return 0
    home = alumni.location.strip().lower()
    rows = (
        db.query(Event.location)
        .filter(Event.participants_ids.any(alumni.id))
        .all()
    )
    return sum(
        1 for (loc,) in rows if loc and loc.strip().lower() != home
    )


def _profile_fields_complete(alumni: Alumni, fields: list[str]) -> tuple[int, int]:
    """Returns (filled, total) — number of listed fields that are non-empty."""
    filled = 0
    for f in fields:
        v = getattr(alumni, f, None)
        if v not in (None, ""):
            filled += 1
    return filled, len(fields)


def _badge_count(db: Session, alumni_id: str) -> int:
    return (
        db.query(func.count(UserBadge.id))
        .filter(UserBadge.alumni_id == alumni_id)
        .scalar()
        or 0
    )


# ─────────────────────────── strategies ────────────────────────────────────


def _strategy_progress(
    db: Session, alumni: Alumni, badge: Badge
) -> tuple[int, int, str]:
    """Returns (progress, threshold, metric_label) for the locked card UI."""
    params = badge.params or {}
    strat = badge.strategy

    if strat == "count_threshold":
        metric = params.get("metric", "")
        threshold = int(params.get("threshold", 1))
        if metric == "events_attended":
            return (
                _events_attended_count(db, alumni.id),
                threshold,
                "alumni events attended",
            )
        if metric == "max_attendees_on_owned":
            return (
                _max_attendees_on_owned(db, alumni.id),
                threshold,
                "attendees on biggest hosted event",
            )
        if metric == "cross_city_attendances":
            return (
                _cross_city_attendances(db, alumni),
                threshold,
                "events attended outside home city",
            )

    if strat == "distinct_count":
        threshold = int(params.get("threshold", 1))
        if params.get("metric") == "distinct_cities_hosted":
            return (
                _distinct_cities_hosted(db, alumni.id),
                threshold,
                "distinct cities hosted in",
            )

    if strat == "year_range":
        try:
            year = int(alumni.graduation_year)
        except (TypeError, ValueError):
            year = 0
        lo, hi = int(params.get("min", 0)), int(params.get("max", 0))
        in_range = 1 if lo <= year <= hi else 0
        return in_range, 1, f"graduation year in {lo}-{hi}"

    if strat == "profile_completeness":
        fields = params.get("fields", [])
        filled, total = _profile_fields_complete(alumni, fields)
        return filled, total, "profile fields completed"

    if strat == "badge_count":
        threshold = int(params.get("threshold", 10))
        return _badge_count(db, alumni.id), threshold, "badges earned"

    if strat == "first_n":
        n = int(params.get("n", 1))
        awarded_so_far = (
            db.query(func.count(UserBadge.id))
            .filter(UserBadge.badge_id == badge.id)
            .scalar()
            or 0
        )
        # "Progress" here means how close the user is to qualifying — for
        # Pioneer that's just "has show_location been flipped." Once flipped,
        # they qualify if there's still room (awarded_so_far < n).
        qualifies = 1 if getattr(alumni, "show_location", False) and alumni.location else 0
        if awarded_so_far >= n:
            # Window closed.
            return 0, 1, f"first {n} to pin location (window closed)"
        return qualifies, 1, f"first {n} to pin location on map"

    if strat == "per_city_first":
        # Always shows as not-yet — we can't pre-judge a city.
        return 0, 1, "create the first event in a new city"

    if strat in ("leaderboard", "manual"):
        return 0, 1, "awarded by an admin" if strat == "manual" else "year-end leaderboard"

    return 0, 1, "criteria"


def _should_award(
    db: Session, alumni: Alumni, badge: Badge
) -> tuple[bool, dict[str, Any]]:
    """Returns (should_award, extra_metadata). Pure read of current state."""
    params = badge.params or {}
    strat = badge.strategy

    if strat == "count_threshold":
        progress, threshold, _ = _strategy_progress(db, alumni, badge)
        return progress >= threshold, {}

    if strat == "distinct_count":
        progress, threshold, _ = _strategy_progress(db, alumni, badge)
        return progress >= threshold, {}

    if strat == "year_range":
        try:
            year = int(alumni.graduation_year)
        except (TypeError, ValueError):
            return False, {}
        lo, hi = int(params.get("min", 0)), int(params.get("max", 0))
        return lo <= year <= hi, {}

    if strat == "profile_completeness":
        fields = params.get("fields", [])
        filled, total = _profile_fields_complete(alumni, fields)
        return filled >= total and total > 0, {}

    if strat == "badge_count":
        threshold = int(params.get("threshold", 10))
        return _badge_count(db, alumni.id) >= threshold, {}

    if strat == "first_n":
        n = int(params.get("n", 1))
        if not (getattr(alumni, "show_location", False) and alumni.location):
            return False, {}
        # Atomic gate: count under lock when we actually insert.
        awarded_so_far = (
            db.query(func.count(UserBadge.id))
            .filter(UserBadge.badge_id == badge.id)
            .scalar()
            or 0
        )
        return awarded_so_far < n, {}

    if strat == "per_city_first":
        # Awarded by the event_approved hook with city metadata. We need a
        # city to make the decision; without an event in scope we can't.
        return False, {}

    # leaderboard + manual never auto-award.
    return False, {}


def _award(
    db: Session,
    alumni_id: str,
    badge: Badge,
    extra: dict | None = None,
    awarded_by: str | None = None,
) -> UserBadge | None:
    """Insert a UserBadge row. Idempotent on (alumni_id, badge_id, extra).

    `awarded_by` records the admin id for manual awards; leave None for
    the auto-evaluator so the row keeps its "system-awarded" meaning.
    """
    row = UserBadge(
        id=str(uuid.uuid4()),
        alumni_id=alumni_id,
        badge_id=badge.id,
        awarded_at=datetime.utcnow(),
        extra=extra or {},
        awarded_by=awarded_by,
    )
    db.add(row)
    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        return None
    return row


# ─────────────────────────── public API ────────────────────────────────────


# Strategies whose criteria are one-way / historical / externally-owned.
# Even if `_should_award` returns False now (e.g. a user edits their profile
# and the raw signal disappears), we KEEP these badges. They represent a
# moment in time or an admin decision, not an ongoing condition.
_NON_REVOCABLE_STRATEGIES = {
    "first_n",           # Pioneer — "first 100 to pin location" is historical
    "per_city_first",    # Founding Host — first event in a city is historical
    "leaderboard",       # Local Legend — awarded annually, historical
    "manual",            # OSS Contributor / Suggestion Box — admin choice
    "year_range",        # Innopolis OG — graduation year is a lifetime fact
}


def revoke_ineligible(db: Session, alumni: Alumni) -> list[str]:
    """Delete any of the alumnus's badges whose criteria no longer hold.

    Only touches badges whose strategy is revocable (count-based, distinct-
    count, profile completeness, badge count). Historical / lifetime badges
    listed in `_NON_REVOCABLE_STRATEGIES` are preserved even if the raw
    signal isn't there anymore.

    Cascades: if revoking a badge drops the total count below Badge
    Collector's threshold, Badge Collector is revoked too. Loop is bounded
    at 3 rounds to prevent runaway.

    Returns the list of revoked badge codes.
    """
    revoked: list[str] = []
    for _round in range(3):
        did_revoke = False
        awarded = (
            db.query(UserBadge, Badge)
            .join(Badge, Badge.id == UserBadge.badge_id)
            .filter(UserBadge.alumni_id == alumni.id)
            .all()
        )
        for ub, b in awarded:
            if b.strategy in _NON_REVOCABLE_STRATEGIES:
                continue
            try:
                should_keep, _extra = _should_award(db, alumni, b)
                if not should_keep:
                    db.delete(ub)
                    # Flush so subsequent checks in this round (e.g. Badge
                    # Collector's count query) see the deletion.
                    db.flush()
                    revoked.append(b.code)
                    did_revoke = True
            except Exception as e:
                logger.error("badge revoke check failed for %s: %s", b.code, e)
        if did_revoke:
            db.commit()
        else:
            break
    return revoked


def evaluate_for_user(
    db: Session, alumni: Alumni, trigger: str, context: dict | None = None
) -> list[UserBadge]:
    """Evaluate every badge whose trigger_metrics include `trigger`.

    Failure-tolerant: each badge's eval is wrapped so one bad strategy
    doesn't block the others or the calling request.

    Recursion guard: if `trigger == "badge_awarded"` (set by us after every
    award to chain Badge Collector), we skip awarding Badge Collector itself
    from inside a Badge Collector awarding to avoid an infinite loop.
    """
    if context is None:
        context = {}

    badges = (
        db.query(Badge).filter(Badge.trigger_metrics.contains([trigger])).all()
    )
    already = {
        ub.badge_id
        for ub in db.query(UserBadge.badge_id)
        .filter(UserBadge.alumni_id == alumni.id)
        .all()
    }

    newly_awarded: list[UserBadge] = []
    for b in badges:
        # Skip already-earned single-instance badges. Per-city/leaderboard
        # badges live in `extra` so we allow repeats — but for v1 the only
        # badge that can repeat is Local Legend (manual-cron), so this
        # blanket-skip is fine.
        if b.id in already and b.strategy not in ("per_city_first",):
            continue
        # Anti-recursion: don't re-evaluate Badge Collector inside its own chain.
        if b.code == "badge_collector" and context.get("from_badge_awarded"):
            continue
        try:
            should, extra = _should_award(db, alumni, b)
            if should:
                row = _award(db, alumni.id, b, extra)
                if row is not None:
                    newly_awarded.append(row)
        except Exception as e:
            logger.error("badge eval failed for %s: %s", b.code, e)

    if newly_awarded:
        db.commit()
        # Chain into Badge Collector evaluation.
        try:
            chained = evaluate_for_user(
                db,
                alumni,
                "badge_awarded",
                context={"from_badge_awarded": True},
            )
            newly_awarded.extend(chained)
        except Exception as e:
            logger.error("badge_awarded cascade failed: %s", e)

    return newly_awarded


def award_founding_host(
    db: Session, alumni: Alumni, event: Event
) -> UserBadge | None:
    """Per-city first hook — call when an event is approved.

    Awards "Founding Host" with metadata={"city": <event.location lowercased>}
    if no earlier approved event exists in that city.
    """
    if not event.location:
        return None
    badge = db.query(Badge).filter(Badge.code == "founding_host").first()
    if not badge:
        return None
    city = event.location.strip().lower()

    # Is there an earlier approved event in this city by anyone (incl. self)?
    earlier = (
        db.query(Event)
        .filter(
            Event.approved.is_(True),
            func.lower(func.trim(Event.location)) == city,
            Event.datetime < event.datetime,
        )
        .first()
    )
    if earlier is not None:
        return None

    return _award(db, alumni.id, badge, {"city": city})


def list_my_badges(db: Session, alumni: Alumni) -> dict[str, Any]:
    """Shape: {earned: [...], locked: [...], newly_earned: [...]}.

    Computes progress on locked badges from current data; no progress table.
    """
    catalog = db.query(Badge).all()
    awards = (
        db.query(UserBadge).filter(UserBadge.alumni_id == alumni.id).all()
    )
    earned_index: dict[str, list[UserBadge]] = {}
    for a in awards:
        earned_index.setdefault(a.badge_id, []).append(a)

    earned: list[dict] = []
    locked: list[dict] = []
    newly: list[dict] = []
    seen_to_mark: list[UserBadge] = []

    for b in catalog:
        if b.id in earned_index:
            for ub in earned_index[b.id]:
                earned.append(
                    {
                        "code": b.code,
                        "name": b.name,
                        "description": b.description,
                        "tier": b.tier,
                        "icon_key": b.icon_key,
                        "awarded_at": ub.awarded_at,
                        "extra": ub.extra or {},
                    }
                )
                if ub.seen_at is None:
                    newly.append(
                        {
                            "code": b.code,
                            "name": b.name,
                            "description": b.description,
                            "tier": b.tier,
                            "icon_key": b.icon_key,
                        }
                    )
                    seen_to_mark.append(ub)
        else:
            progress, threshold, metric = _strategy_progress(db, alumni, b)
            locked.append(
                {
                    "code": b.code,
                    "name": b.name,
                    "description": b.description,
                    "tier": b.tier,
                    "icon_key": b.icon_key,
                    "progress": progress,
                    "threshold": threshold,
                    "metric_label": metric,
                }
            )

    return {"earned": earned, "locked": locked, "newly_earned": newly}


def list_for_user(db: Session, alumni_id: str) -> dict[str, Any]:
    """Public view — earned only, no progress on locked, no newly_earned."""
    awards = (
        db.query(UserBadge, Badge)
        .join(Badge, Badge.id == UserBadge.badge_id)
        .filter(UserBadge.alumni_id == alumni_id)
        .all()
    )
    earned = [
        {
            "code": b.code,
            "name": b.name,
            "description": b.description,
            "tier": b.tier,
            "icon_key": b.icon_key,
            "awarded_at": ub.awarded_at,
            "extra": ub.extra or {},
        }
        for ub, b in awards
    ]
    return {"earned": earned, "locked": [], "newly_earned": []}


def mark_seen(db: Session, alumni: Alumni, badge_code: str) -> bool:
    badge = db.query(Badge).filter(Badge.code == badge_code).first()
    if not badge:
        return False
    rows = (
        db.query(UserBadge)
        .filter(
            UserBadge.alumni_id == alumni.id,
            UserBadge.badge_id == badge.id,
            UserBadge.seen_at.is_(None),
        )
        .all()
    )
    for r in rows:
        r.seen_at = datetime.utcnow()
    db.commit()
    return bool(rows)


# ─────────────────────────── manual admin actions ──────────────────────────


class ManualAwardError(Exception):
    """Raised for a manual-award / manual-revoke pre-condition failure.

    The message is safe to surface as a 4xx response body.
    """


def manual_award(
    db: Session,
    alumni: Alumni,
    badge_code: str,
    admin_id: str,
    metadata: dict | None = None,
) -> UserBadge:
    """Insert a UserBadge row for the given code on behalf of an admin.

    Raises ManualAwardError if the badge doesn't exist or the row is a
    duplicate (idempotent uniqueness constraint hit).
    """
    badge = db.query(Badge).filter(Badge.code == badge_code).first()
    if badge is None:
        raise ManualAwardError(f"badge '{badge_code}' does not exist")

    row = _award(db, alumni.id, badge, metadata, awarded_by=admin_id)
    if row is None:
        raise ManualAwardError(
            f"badge '{badge_code}' already awarded to this user with the same metadata"
        )
    db.commit()
    return row


def manual_revoke(
    db: Session,
    alumni: Alumni,
    badge_code: str,
    metadata: dict | None = None,
) -> Badge:
    """Delete the matching UserBadge row for `badge_code` (+ optional metadata).

    Raises ManualAwardError if the badge doesn't exist or the user doesn't
    hold it. Returns the Badge for the caller to include in the response.
    """
    badge = db.query(Badge).filter(Badge.code == badge_code).first()
    if badge is None:
        raise ManualAwardError(f"badge '{badge_code}' does not exist")

    q = db.query(UserBadge).filter(
        UserBadge.alumni_id == alumni.id, UserBadge.badge_id == badge.id
    )
    if metadata is not None:
        q = q.filter(UserBadge.extra == metadata)
    rows = q.all()
    if not rows:
        raise ManualAwardError(
            f"user does not hold badge '{badge_code}'"
            + (f" with metadata {metadata}" if metadata else "")
        )
    for r in rows:
        db.delete(r)
    db.commit()
    return badge
