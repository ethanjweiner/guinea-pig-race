from django.db import models
from django.core.validators import RegexValidator, MinValueValidator, MaxValueValidator
from django.utils import timezone
from django.core.exceptions import ValidationError


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


def validate_gender(value):
    """Validate gender choice"""
    print("validating gender")
    if value not in [choice[0] for choice in Registrant.GENDER_CHOICES]:
        raise ValidationError("Please select a valid gender option.")


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
                regex="^[a-zA-Z\s\-]+$",
                message="First name can only contain letters, spaces, and hyphens",
            )
        ],
    )
    last_name = models.CharField(
        max_length=255,
        validators=[
            RegexValidator(
                regex="^[a-zA-Z\s\-]+$",
                message="Last name can only contain letters, spaces, and hyphens",
            )
        ],
    )
    email = models.EmailField(
        max_length=255,
        validators=[
            RegexValidator(
                regex="^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$",
                message="Please enter a valid email address",
            )
        ],
    )
    date_of_birth = models.DateField(
        null=True,
        validators=[
            MinValueValidator(
                limit_value=timezone.now()
                .date()
                .replace(year=timezone.now().year - 100),
                message="Date of birth cannot be more than 100 years ago",
            ),
            MaxValueValidator(
                limit_value=timezone.now().date(),
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


    year = models.IntegerField(default=timezone.now().year)
    hometown = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        validators=[
            RegexValidator(
                regex="^[a-zA-Z\s\-\.,]+$",
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


class Result(models.Model):
    registrant = models.ForeignKey(Registrant, on_delete=models.CASCADE)
    overall_place = models.IntegerField(null=True)
    gender_place = models.IntegerField(null=True)
    time = models.CharField(max_length=255)
    dnf = models.BooleanField(default=False)
    year = models.IntegerField()
