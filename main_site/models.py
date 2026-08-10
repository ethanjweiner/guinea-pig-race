from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator, RegexValidator
from django.db import models
from django.db.models import Q
from django.utils import timezone


def validate_seed_time(value):
    """Validate that seed time is in MM:SS format and reasonable"""
    if not value:
        return
    try:
        minutes, seconds = map(int, value.split(":"))
        if minutes < 0 or seconds < 0 or seconds > 59:
            raise ValidationError("Invalid time format. Use MM:SS format.")
        if minutes > 30:  # Assuming 30 minutes is a reasonable max
            raise ValidationError("Seed time seems unusually high.")
    except ValueError:
        raise ValidationError("Invalid time format. Use MM:SS format.")


def validate_result_time(value):
    """Validate that result time is in M:SS or M:SS.xx format."""
    if not value:
        return

    try:
        parse_result_time_seconds(value)
    except (TypeError, ValueError):
        raise ValidationError("Invalid time format. Use M:SS or M:SS.xx format.")


def parse_result_time_seconds(value):
    value = value.strip()

    if "." in value:
        time_part, fraction = value.split(".", 1)
        if not fraction.isdigit():
            raise ValueError("Invalid fractional seconds.")
    else:
        time_part = value
        fraction = None

    parts = time_part.split(":")
    if len(parts) == 3:
        minutes, seconds, colon_fraction = parts
        if fraction is not None:
            raise ValueError("Invalid time format.")
        fraction = colon_fraction
    elif len(parts) == 2:
        minutes, seconds = parts
    else:
        raise ValueError("Invalid time format.")

    minutes = int(minutes)
    seconds = int(seconds)
    if fraction is not None and not fraction.isdigit():
        raise ValueError("Invalid fractional seconds.")

    if minutes < 0 or seconds < 0 or seconds > 59:
        raise ValueError("Invalid result time.")

    fractional_seconds = float(f"0.{fraction}") if fraction is not None else 0
    return minutes * 60 + seconds + fractional_seconds


def validate_gender(value):
    """Validate gender choice"""
    if value not in [choice[0] for choice in Registrant.GENDER_CHOICES]:
        raise ValidationError("Please select a valid gender option.")


def current_year():
    return timezone.now().year


def current_date():
    return timezone.now().date()


def earliest_birth_date():
    return current_date().replace(year=current_year() - 100)


class Registrant(models.Model):
    GENDER_CHOICES = [
        ("male", "Male"),
        ("female", "Female"),
        ("non-binary", "Non-Binary"),
    ]

    first_name = models.CharField(
        max_length=255,
        validators=[
            RegexValidator(
                regex=r"^[a-zA-Z\s\-]+$",
                message="First name can only contain letters, spaces, and hyphens",
            )
        ],
    )
    last_name = models.CharField(
        max_length=255,
        validators=[
            RegexValidator(
                regex=r"^[a-zA-Z\s\-]+$",
                message="Last name can only contain letters, spaces, and hyphens",
            )
        ],
    )
    email = models.EmailField(
        max_length=255,
        validators=[
            RegexValidator(
                regex=r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$",
                message="Please enter a valid email address",
            )
        ],
    )
    date_of_birth = models.DateField(
        null=True,
        validators=[
            MinValueValidator(
                limit_value=earliest_birth_date,
                message="Date of birth cannot be more than 100 years ago",
            ),
            MaxValueValidator(
                limit_value=current_date,
                message="Date of birth cannot be in the future",
            ),
        ],
    )
    gender = models.CharField(
        max_length=255,
        choices=GENDER_CHOICES,
        error_messages={
            "invalid_choice": "Please select a valid gender option.",
        },
    )
    seed_time = models.CharField(max_length=255, validators=[validate_seed_time])
    sponsor = models.CharField(max_length=255, blank=True, null=True)

    @property
    def seed_time_seconds(self):
        """Convert seed_time to seconds for proper numerical sorting"""
        if not self.seed_time:
            return 0
        try:
            minutes, seconds = map(int, self.seed_time.split(":"))
            return minutes * 60 + seconds
        except (ValueError, AttributeError):
            return 0

    @property
    def age(self):
        if not self.date_of_birth:
            return None

        today = timezone.now().date()
        has_had_birthday = (today.month, today.day) >= (
            self.date_of_birth.month,
            self.date_of_birth.day,
        )
        return today.year - self.date_of_birth.year - (not has_had_birthday)

    year = models.IntegerField(default=current_year)
    hometown = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        validators=[
            RegexValidator(
                regex=r"^[a-zA-Z\s\-\.,]+$",
                message="Hometown can only contain letters, spaces, hyphens, periods, and commas",
            )
        ],
    )
    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name} {self.year}"

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["email", "year"],
                name="unique_registration_per_year",
                violation_error_message="You have already registered for this year.",
            )
        ]


class ResultQuerySet(models.QuerySet):
    def visible_results(self):
        return self.filter(Q(dnf=True) | ~Q(time=""))


class Result(models.Model):
    HEAT_CHOICES = [
        (f"Heat {heat_number}", f"Heat {heat_number}")
        for heat_number in range(1, 14)
    ] + [("Championship", "Championship")]

    registrant = models.ForeignKey(Registrant, on_delete=models.CASCADE)
    time = models.CharField(max_length=255, validators=[validate_result_time])
    heat = models.CharField(max_length=32, choices=HEAT_CHOICES, blank=True, default="")
    dnf = models.BooleanField(default=False)
    year = models.IntegerField(default=current_year)

    objects = ResultQuerySet.as_manager()

    @property
    def time_seconds(self):
        if self.dnf or not self.time:
            return float("inf")

        return parse_result_time_seconds(self.time)

    @property
    def overall_place(self):
        results = Result.objects.visible_results().filter(year=self.year)
        results = sorted(results, key=lambda x: (x.dnf, x.time_seconds))
        return results.index(self) + 1

    @property
    def gender_place(self):
        results = Result.objects.visible_results().filter(
            year=self.year, registrant__gender=self.registrant.gender
        )
        results = sorted(results, key=lambda x: (x.dnf, x.time_seconds))
        return results.index(self) + 1

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["registrant", "year"],
                name="unique_result_per_registrant_year",
            )
        ]
