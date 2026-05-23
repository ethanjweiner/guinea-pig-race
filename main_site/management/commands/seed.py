import json
from pathlib import Path

from django.core.management.base import BaseCommand

from main_site.models import Registrant, Result


DATA_DIR = Path(__file__).resolve().parents[1] / "data"


class Command(BaseCommand):
    help = "Seed the database with results"

    def handle(self, *args, **options):
        for year_dir in sorted(DATA_DIR.iterdir()):
            if not year_dir.is_dir() or not year_dir.name.isdigit():
                continue

            year = int(year_dir.name)
            Result.objects.filter(year=year).delete()
            Registrant.objects.filter(year=year).delete()
            seed_registrants(year_dir, year)
            seed_results(year_dir, year)

            self.stdout.write(self.style.SUCCESS(f"Seeded {year} results"))


def seed_registrants(year_dir, year):
    with (year_dir / "registrants.json").open() as f:
        registrants = json.load(f)

        for registrant in registrants:
            Registrant(
                first_name=registrant["first_name"],
                last_name=registrant.get("last_name", ""),
                gender=registrant["gender"],
                year=year,
                email=f"{registrant['first_name']}.{registrant['last_name']}@example.com".lower(),
                seed_time=registrant.get("seed_time", ""),
            ).save()


def seed_results(year_dir, year):
    with (year_dir / "results.json").open() as f:
        results = json.load(f)

    for result in results:
        Result(
            registrant=Registrant.objects.get(
                first_name=result["first_name"],
                last_name=result["last_name"],
                year=year,
            ),
            time=normalize_time(result.get("time", "")),
            dnf=result.get("dnf", False),
            year=year,
        ).save()


def normalize_time(value):
    if not value:
        return ""

    parts = value.split(":")
    if len(parts) == 3 and int(parts[2]) == 0:
        return f"{parts[0]}:{parts[1]}"

    if len(parts) == 3:
        return f"{parts[0]}:{parts[1]}.{parts[2]}"

    return value
