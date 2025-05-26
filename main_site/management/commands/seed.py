from django.core.management.base import BaseCommand

from main_site.models import Registrant, Result

import json


class Command(BaseCommand):
    help = "Seed the database with results"

    def handle(self, *args, **options):
        # Delete all existing results
        Registrant.objects.all().delete()
        seed_registrants()

        # Create new results
        Result.objects.all().delete()
        seed_results()


def seed_registrants():
    with open("main_site/management/data/2024/registrants.json", "r") as f:
        registrants = json.load(f)

        for registrant in registrants:
            Registrant(
                first_name=registrant["first_name"],
                last_name=registrant.get("last_name", ""),
                gender=registrant["gender"],
                year=2024,
                email=f"{registrant['first_name']}.{registrant['last_name']}@example.com",
            ).save()


# Seed 2024 results
def seed_results():
    with open("main_site/management/data/2024/results.json", "r") as f:
        results = json.load(f)

    for result in results:
        Result(
            registrant=Registrant.objects.get(
                first_name=result["first_name"],
                last_name=result["last_name"],
                year=2024,
            ),
            overall_place=result.get("overall_place", None),
            gender_place=result.get("gender_place", None),
            time=result.get("time", ""),
            dnf=result.get("dnf", False),
            year=2024,
        ).save()
