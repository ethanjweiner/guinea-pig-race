from django.core.management.base import BaseCommand

from main_site.models import Registrant, Result

import json


class Command(BaseCommand):
    help = "Seed the database with results"

    def handle(self, *args, **options):
        # Delete all existing results
        Result.objects.all().delete()
        Registrant.objects.all().delete()

        # Create new results
        seed_registrants()
        seed_results()


def seed_registrants():
    with open("main_site/management/data/2024/registrants.json", "r") as f:
        registrants = json.load(f)

        for registrant in registrants:
            Registrant(
                id=registrant["id"],
                first_name=registrant["first_name"],
                last_name=registrant.get("last_name", ""),
                gender=registrant["gender"],
                year=2024,
            ).save()


def seed_results():
    with open("main_site/management/data/2024/results.json", "r") as f:
        results = json.load(f)

    for result in results:
        Result(
            registrant=Registrant.objects.get(id=result["registrant"]),
            overall_place=result.get("overall_place", None),
            gender_place=result.get("gender_place", None),
            time=result.get("time", ""),
            dnf=result.get("dnf", False),
            year=2024,
        ).save()
