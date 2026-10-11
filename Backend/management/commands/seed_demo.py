from django.core.management import call_command
from django.core.management.base import BaseCommand

from Backend.models import Deptdb


class Command(BaseCommand):
    help = "Load demo departments, doctors and patient stories into an empty database."

    def add_arguments(self, parser):
        parser.add_argument("--force", action="store_true", help="Load even if departments already exist.")

    def handle(self, *args, force=False, **options):
        verbosity = options.get("verbosity", 1)
        if Deptdb.objects.exists() and not force:
            if verbosity:
                self.stdout.write("Database already has data; skipping demo seed.")
            return
        call_command("loaddata", "demo_data", verbosity=verbosity)
        if verbosity:
            self.stdout.write(self.style.SUCCESS("Demo data loaded."))
