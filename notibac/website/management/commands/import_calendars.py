"""
Management command to import collection calendar data from JSON files.

Usage:
    python manage.py import_calendars 2026
"""

import json
from datetime import datetime
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from website.models import Calendar, CollectionDate, Sector


class Command(BaseCommand):
    help = "Import collection calendar data from JSON files"

    def add_arguments(self, parser):
        parser.add_argument(
            "year",
            type=int,
            help="The year to import calendars for (e.g., 2026)",
        )
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Clear existing data for this year before importing",
        )

    def handle(self, *args, **options):
        year = options["year"]
        clear = options["clear"]

        # Find JSON directory
        json_dir = Path("calendars") / str(year) / "json"
        if not json_dir.exists():
            raise CommandError(f"Directory {json_dir} does not exist")

        json_files = sorted(json_dir.glob("*.json"))
        if not json_files:
            raise CommandError(f"No JSON files found in {json_dir}")

        self.stdout.write(f"Found {len(json_files)} JSON files in {json_dir}")

        if clear:
            self.stdout.write(f"Clearing existing data for year {year}...")
            calendars = Calendar.objects.filter(year=year)
            CollectionDate.objects.filter(calendar__in=calendars).delete()
            calendars.delete()
            self.stdout.write(self.style.SUCCESS("Cleared existing data"))

        sectors_created = 0
        sectors_updated = 0
        calendars_created = 0
        calendars_updated = 0
        dates_created = 0

        with transaction.atomic():
            for json_file in json_files:
                self.stdout.write(f"Processing: {json_file.name}")

                with open(json_file, "r", encoding="utf-8") as f:
                    data = json.load(f)

                # Create or update sector
                sector, created = Sector.objects.update_or_create(
                    code=data["sector"],
                    defaults={"name": data["sector_name"]},
                )
                if created:
                    sectors_created += 1
                else:
                    sectors_updated += 1

                # Create or update calendar
                calendar, created = Calendar.objects.update_or_create(
                    sector=sector,
                    year=data["year"],
                    has_compost=data["has_compost"],
                )
                if created:
                    calendars_created += 1
                else:
                    calendars_updated += 1
                    # Clear existing dates for this calendar if updating
                    CollectionDate.objects.filter(calendar=calendar).delete()

                # Import collection dates
                collections = data.get("collections", {})
                for collection_type, dates in collections.items():
                    for date_str in dates:
                        date = datetime.strptime(date_str, "%Y-%m-%d").date()
                        CollectionDate.objects.create(
                            calendar=calendar,
                            collection_type=collection_type,
                            date=date,
                        )
                        dates_created += 1

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("Import complete!"))
        self.stdout.write(f"  Sectors: {sectors_created} created, {sectors_updated} updated")
        self.stdout.write(f"  Calendars: {calendars_created} created, {calendars_updated} updated")
        self.stdout.write(f"  Collection dates: {dates_created} created")
