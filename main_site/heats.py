from dataclasses import dataclass
from math import ceil, log


COED_CHAMPIONSHIP_SIZE_MULTIPLIER = 1.3


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
    largest_heat_size,
    men_championship_size,
    women_championship_size,
    coed_heat_count=None,
):
    _validate_heat_size(largest_heat_size, "Largest co-ed heat size")
    _validate_heat_size(men_championship_size, "Men's championship heat size")
    _validate_heat_size(women_championship_size, "Women's championship heat size")
    if coed_heat_count is not None:
        _validate_heat_size(coed_heat_count, "Number of co-ed heats")

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

    smallest_coed_heat_size = _minimum_coed_heat_size(
        men_championship_size,
        women_championship_size,
    )

    for heat_registrants in _progressive_heats(
        regular_registrants,
        largest_heat_size,
        smallest_coed_heat_size,
        coed_heat_count,
    ):
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


def _minimum_coed_heat_size(men_championship_size, women_championship_size):
    largest_championship_size = max(men_championship_size, women_championship_size)
    return ceil(largest_championship_size * COED_CHAMPIONSHIP_SIZE_MULTIPLIER)


def _fastest_gender_registrants(registrants, gender, count):
    gender_registrants = [
        registrant for registrant in registrants if getattr(registrant, "gender", None) == gender
    ]
    gender_registrants.sort(key=_fastest_first_key)
    return gender_registrants[:count]


def _progressive_heats(registrants, largest_size, smallest_size, heat_count=None):
    if not registrants:
        return []

    if largest_size < smallest_size:
        raise ValueError(
            "Largest co-ed heat size must be at least 30% larger than the "
            "largest championship heat size."
        )

    fixed_heat_count = heat_count is not None
    if heat_count is None:
        heat_count = ceil(len(registrants) / largest_size)
        while (heat_count * smallest_size) > len(registrants):
            heat_count -= 1
        heat_count = max(1, heat_count)

    heat_sizes = _progressive_heat_sizes(
        heat_count,
        len(registrants),
        largest_size,
        smallest_size,
    )

    while not fixed_heat_count and sum(heat_sizes) < len(registrants):
        heat_count += 1
        heat_sizes = _progressive_heat_sizes(
            heat_count,
            len(registrants),
            largest_size,
            smallest_size,
        )

    heats = []
    start = 0
    for size in heat_sizes:
        end = start + size
        heat_registrants = registrants[start:end]
        if heat_registrants:
            heats.append(heat_registrants)
        start = end

    return heats


def _progressive_heat_sizes(heat_count, registrant_count, largest_size, smallest_size):
    minimum_capacity = heat_count * smallest_size
    maximum_capacity = heat_count * largest_size

    if registrant_count < minimum_capacity:
        raise ValueError(
            f"Number of co-ed heats is too high for the minimum co-ed heat size. "
            f"With {registrant_count} non-championship registrants, use at most "
            f"{registrant_count // smallest_size} co-ed heats."
        )

    if registrant_count > maximum_capacity:
        raise ValueError(
            f"Number of co-ed heats is too low for the largest co-ed heat size. "
            f"With {registrant_count} non-championship registrants, use at least "
            f"{ceil(registrant_count / largest_size)} co-ed heats."
        )

    if heat_count == 1:
        return [registrant_count]

    size_range = largest_size - smallest_size
    log_denominator = log(heat_count)
    sizes = []

    for index in range(heat_count):
        progress = log(index + 1) / log_denominator
        size = round(largest_size - (size_range * progress))
        sizes.append(max(smallest_size, min(largest_size, size)))

    return _fit_heat_sizes_to_registrant_count(
        _enforce_decreasing_sizes(sizes),
        registrant_count,
        largest_size,
        smallest_size,
    )


def _fit_heat_sizes_to_registrant_count(
    sizes,
    registrant_count,
    largest_size,
    smallest_size,
):
    while sum(sizes) < registrant_count:
        expanded = False

        for index in range(len(sizes)):
            previous_size = largest_size if index == 0 else sizes[index - 1]
            if sizes[index] >= largest_size or sizes[index] + 1 > previous_size:
                continue

            sizes[index] += 1
            expanded = True
            break

        if not expanded:
            break

    while sum(sizes) > registrant_count:
        reduced = False

        for index in range(len(sizes) - 1, -1, -1):
            next_size = sizes[index + 1] if index + 1 < len(sizes) else smallest_size
            if sizes[index] <= smallest_size or sizes[index] - 1 < next_size:
                continue

            sizes[index] -= 1
            reduced = True
            break

        if not reduced:
            break

    return sizes


def _enforce_decreasing_sizes(sizes):
    progressive_sizes = []
    previous_size = None

    for size in sizes:
        if previous_size is not None:
            size = min(size, previous_size)
        progressive_sizes.append(size)
        previous_size = size

    return progressive_sizes


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
