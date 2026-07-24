from dataclasses import dataclass
from math import ceil


@dataclass(frozen=True)
class HeatAssignment:
    heat_number: int
    heat_name: str
    heat_type: str
    position: int
    registrant: object


def parse_seed_time(seed_time):
    if not seed_time:
        return None

    try:
        minutes, seconds = map(int, str(seed_time).split(":"))
    except (TypeError, ValueError):
        return None

    if minutes < 0 or seconds < 0 or seconds > 59:
        return None

    return minutes * 60 + seconds


def build_heat_assignments(
    registrants,
    regular_heat_size,
    men_championship_size,
    women_championship_size,
):
    _validate_heat_size(regular_heat_size, "Regular heat size")
    _validate_heat_size(men_championship_size, "Men's championship heat size")
    _validate_heat_size(women_championship_size, "Women's championship heat size")

    registrants = list(registrants)

    men_championship = _fastest_gender_registrants(registrants, "male", men_championship_size)
    women_championship = _fastest_gender_registrants(registrants, "female", women_championship_size)
    championship_ids = {id(registrant) for registrant in men_championship + women_championship}

    regular_registrants = [
        registrant for registrant in registrants if id(registrant) not in championship_ids
    ]
    regular_registrants.sort(key=_slowest_first_key)

    assignments = []
    heat_number = 1

    for heat_registrants in _balanced_heats(regular_registrants, regular_heat_size):
        assignments.extend(
            _assign_heat(
                heat_number,
                f"Heat {heat_number}",
                "Co-ed",
                heat_registrants,
            )
        )
        heat_number += 1

    championship_heats = [
        ("Women's Championship", "Women's Championship", women_championship),
        ("Men's Championship", "Men's Championship", men_championship),
    ]

    for heat_name, heat_type, heat_registrants in championship_heats:
        if not heat_registrants:
            continue

        assignments.extend(
            _assign_heat(
                heat_number,
                heat_name,
                heat_type,
                heat_registrants,
            )
        )
        heat_number += 1

    return assignments


def _validate_heat_size(size, label):
    if size < 1:
        raise ValueError(f"{label} must be at least 1.")


def _fastest_gender_registrants(registrants, gender, count):
    gender_registrants = [
        registrant for registrant in registrants if getattr(registrant, "gender", None) == gender
    ]
    gender_registrants.sort(key=_fastest_first_key)
    return gender_registrants[:count]


def _balanced_heats(registrants, target_size):
    if not registrants:
        return []

    heat_count = ceil(len(registrants) / target_size)
    base_size, larger_heat_count = divmod(len(registrants), heat_count)
    heat_sizes = [
        base_size + 1 if index < larger_heat_count else base_size
        for index in range(heat_count)
    ]

    heats = []
    start = 0
    for size in heat_sizes:
        end = start + size
        heats.append(registrants[start:end])
        start = end

    return heats


def _assign_heat(heat_number, heat_name, heat_type, registrants):
    return [
        HeatAssignment(
            heat_number=heat_number,
            heat_name=heat_name,
            heat_type=heat_type,
            position=position,
            registrant=registrant,
        )
        for position, registrant in enumerate(registrants, start=1)
    ]


def _fastest_first_key(registrant):
    seed_seconds = parse_seed_time(getattr(registrant, "seed_time", None))
    return (
        seed_seconds is None,
        seed_seconds if seed_seconds is not None else float("inf"),
        *_registrant_tie_breaker(registrant),
    )


def _slowest_first_key(registrant):
    seed_seconds = parse_seed_time(getattr(registrant, "seed_time", None))
    return (
        seed_seconds is not None,
        -seed_seconds if seed_seconds is not None else 0,
        *_registrant_tie_breaker(registrant),
    )


def _registrant_tie_breaker(registrant):
    return (
        str(getattr(registrant, "last_name", "")).lower(),
        str(getattr(registrant, "first_name", "")).lower(),
        str(getattr(registrant, "email", "")).lower(),
        str(getattr(registrant, "pk", "")),
    )
