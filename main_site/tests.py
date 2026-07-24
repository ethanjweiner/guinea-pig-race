from io import BytesIO
from types import SimpleNamespace
from zipfile import ZipFile

from django.contrib.auth.models import User
from django.test import SimpleTestCase, TestCase

from main_site.heat_workbook import build_printable_heat_workbook
from main_site.heats import build_heat_assignments
from main_site.models import Registrant, current_year


def registrant(first_name, gender, seed_time):
    return SimpleNamespace(
        first_name=first_name,
        last_name="Runner",
        email=f"{first_name.lower()}@example.com",
        date_of_birth="1990-01-01",
        gender=gender,
        seed_time=seed_time,
        sponsor="",
        hometown="",
        pk=first_name,
    )


class HeatBuilderTests(SimpleTestCase):
    def test_championship_heats_select_fastest_men_and_women_only(self):
        runners = [
            registrant("FastNonBinary", "non-binary", "04:30"),
            registrant("FastMan", "male", "04:40"),
            registrant("SlowMan", "male", "07:00"),
            registrant("FastWoman", "female", "04:50"),
            registrant("SlowWoman", "female", "07:10"),
        ]

        assignments = build_heat_assignments(
            runners,
            regular_heat_size=4,
            men_championship_size=1,
            women_championship_size=1,
        )

        championship_names = {
            assignment.heat_name: assignment.registrant.first_name
            for assignment in assignments
            if assignment.heat_type.endswith("Championship")
        }
        coed_names = [
            assignment.registrant.first_name
            for assignment in assignments
            if assignment.heat_type == "Co-ed"
        ]

        self.assertEqual(championship_names["Men's Championship"], "FastMan")
        self.assertEqual(championship_names["Women's Championship"], "FastWoman")
        self.assertIn("FastNonBinary", coed_names)

    def test_regular_heats_are_balanced_and_slow_to_fast(self):
        runners = [
            registrant(f"Runner{index}", "non-binary", f"{minutes:02d}:00")
            for index, minutes in enumerate(range(5, 15), start=1)
        ]

        assignments = build_heat_assignments(
            runners,
            regular_heat_size=4,
            men_championship_size=1,
            women_championship_size=1,
        )
        coed_assignments = [
            assignment for assignment in assignments if assignment.heat_type == "Co-ed"
        ]

        heat_sizes = {}
        for assignment in coed_assignments:
            heat_sizes.setdefault(assignment.heat_number, 0)
            heat_sizes[assignment.heat_number] += 1

        self.assertEqual(list(heat_sizes.values()), [4, 3, 3])
        self.assertEqual(coed_assignments[0].registrant.seed_time, "14:00")
        self.assertEqual(coed_assignments[-1].registrant.seed_time, "05:00")

    def test_invalid_seed_times_are_slower_than_valid_seed_times(self):
        runners = [
            registrant("InvalidSeed", "male", ""),
            registrant("ValidSeed", "male", "06:00"),
        ]

        assignments = build_heat_assignments(
            runners,
            regular_heat_size=4,
            men_championship_size=1,
            women_championship_size=1,
        )

        championship_assignment = next(
            assignment
            for assignment in assignments
            if assignment.heat_name == "Men's Championship"
        )
        coed_assignment = next(
            assignment for assignment in assignments if assignment.heat_type == "Co-ed"
        )

        self.assertEqual(championship_assignment.registrant.first_name, "ValidSeed")
        self.assertEqual(coed_assignment.registrant.first_name, "InvalidSeed")

    def test_printable_workbook_contains_heat_sections_and_print_settings(self):
        assignments = build_heat_assignments(
            [
                registrant("FastMan", "male", "04:40"),
                registrant("FastWoman", "female", "04:50"),
                registrant("CoedRunner", "non-binary", "07:00"),
            ],
            regular_heat_size=4,
            men_championship_size=1,
            women_championship_size=1,
        )

        workbook_bytes = build_printable_heat_workbook(assignments, 2026)

        with ZipFile(BytesIO(workbook_bytes)) as workbook:
            sheet_xml = workbook.read("xl/worksheets/sheet1.xml").decode()
            workbook_xml = workbook.read("xl/workbook.xml").decode()

        self.assertIn('name="Printable Heats"', workbook_xml)
        self.assertIn("Guinea Pig Mile 2026 Heats", sheet_xml)
        self.assertIn("Co-ed", sheet_xml)
        self.assertIn("Men's Championship", sheet_xml)
        self.assertIn("Women's Championship", sheet_xml)
        self.assertIn('orientation="landscape"', sheet_xml)
        self.assertIn("<rowBreaks", sheet_xml)


class HeatBuilderAdminTests(TestCase):
    def test_admin_can_download_heat_csv(self):
        user = User.objects.create_superuser(
            username="admin",
            email="admin@example.com",
            password="password",
        )
        self.client.force_login(user)
        year = current_year()

        Registrant.objects.create(
            first_name="Fast",
            last_name="Man",
            email="fast-man@example.com",
            date_of_birth="1990-01-01",
            gender="male",
            seed_time="04:30",
            year=year,
        )
        Registrant.objects.create(
            first_name="Fast",
            last_name="Woman",
            email="fast-woman@example.com",
            date_of_birth="1990-01-01",
            gender="female",
            seed_time="04:45",
            year=year,
        )
        Registrant.objects.create(
            first_name="Coed",
            last_name="Runner",
            email="coed@example.com",
            date_of_birth="1990-01-01",
            gender="non-binary",
            seed_time="04:20",
            year=year,
        )

        index_response = self.client.get("/admin/")
        form_response = self.client.get("/admin/heats/")
        csv_response = self.client.post(
            "/admin/heats/",
            {
                "regular_heat_size": "4",
                "men_championship_size": "1",
                "women_championship_size": "1",
                "format": "csv",
            },
        )
        xlsx_response = self.client.post(
            "/admin/heats/",
            {
                "regular_heat_size": "4",
                "men_championship_size": "1",
                "women_championship_size": "1",
                "format": "xlsx",
            },
        )

        self.assertContains(index_response, "Build heat CSV")
        self.assertContains(form_response, "Build Heats")
        self.assertEqual(csv_response["Content-Type"], "text/csv")
        self.assertIn("heats_", csv_response["Content-Disposition"])
        self.assertContains(csv_response, "Co-ed")
        self.assertContains(csv_response, "Men's Championship")
        self.assertContains(csv_response, "Women's Championship")
        self.assertEqual(
            xlsx_response["Content-Type"],
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        self.assertIn("heats_", xlsx_response["Content-Disposition"])
        self.assertTrue(xlsx_response.content.startswith(b"PK"))
