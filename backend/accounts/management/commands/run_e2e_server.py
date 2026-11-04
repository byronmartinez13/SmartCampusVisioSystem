"""Test-only server: keep the dispatcher in the same process for reliable teardown."""
import threading
from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from django.db import close_old_connections
from video_analysis.client import VisionClient
from video_analysis.models import VideoJob
from video_analysis.services import ACTIVE, synchronize


class Command(BaseCommand):
    def handle(self, *args, **options):
        if settings.SETTINGS_MODULE != "config.e2e":
            raise CommandError("Solo se permite con config.e2e.")
        stop = threading.Event()

        def dispatch():
            client = VisionClient()
            try:
                while not stop.wait(1):
                    close_old_connections()
                    for job in VideoJob.objects.filter(status__in=ACTIVE):
                        synchronize(job, client)
            finally:
                client.close()
                close_old_connections()

        thread = threading.Thread(target=dispatch, daemon=True)
        thread.start()
        try:
            call_command("runserver", "127.0.0.1:8001", use_reloader=False)
        finally:
            stop.set()
            thread.join(timeout=5)
