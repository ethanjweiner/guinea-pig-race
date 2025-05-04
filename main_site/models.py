from django.db import models


GENDER_CHOICES = [
    ("male", "Male"),
    ("female", "Female"),
    ("non-binary", "Non-binary"),
]


# TODO: Add additional validation here
class Registrant(models.Model):
    id = models.CharField(max_length=255, primary_key=True)
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    email = models.EmailField(max_length=255)
    date_of_birth = models.DateField(null=True)
    gender = models.CharField(max_length=255, choices=GENDER_CHOICES)
    phone = models.CharField(max_length=12)
    seed_time = models.CharField(max_length=255)
    sponsor = models.CharField(max_length=255)
    year = models.IntegerField()
    hometown = models.CharField(max_length=255, null=True)


class Result(models.Model):
    registrant = models.ForeignKey(Registrant, on_delete=models.CASCADE)
    overall_place = models.IntegerField(null=True)
    gender_place = models.IntegerField(null=True)
    time = models.CharField(max_length=255)
    dnf = models.BooleanField(default=False)
    year = models.IntegerField()
