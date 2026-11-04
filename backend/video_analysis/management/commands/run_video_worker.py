import time
from django.core.management.base import BaseCommand
from django.db import close_old_connections
from video_analysis.client import VisionClient
from video_analysis.models import VideoJob
from video_analysis.services import ACTIVE, synchronize


class Command(BaseCommand):
    help = "Despacha y sincroniza videos. Ejecutar una sola instancia."

    def add_arguments(self, parser):
        parser.add_argument("--once", action="store_true")

    def handle(self, *args, **options):
        client = VisionClient()
        self.stdout.write("Sincronizador de videos iniciado.")
        try:
            while True:
                close_old_connections()
                for job in VideoJob.objects.filter(status__in=ACTIVE, source='video').order_by("created_at"):
                    synchronize(job, client)
                if options["once"]:
                    break
                time.sleep(3)
        except KeyboardInterrupt:
            pass
        finally:
            client.close()
