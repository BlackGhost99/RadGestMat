from django.core.management.base import BaseCommand
from django.db import transaction, IntegrityError
from assets.models import Materiel, Departement
import time


class Command(BaseCommand):
    help = 'Backfill asset_id and numero_inventaire for existing Materiel rows and fix missing defaults.'

    def handle(self, *args, **options):
        # Find materiels needing asset_id or numero_inventaire
        qs = Materiel.objects.all()
        count = 0
        for m in qs:
            needs_asset = (not m.asset_id) or m.asset_id == 'NEW'
            needs_num = (not m.numero_inventaire) or m.numero_inventaire.strip() == ''
            if not (needs_asset or needs_num):
                continue

            # try to generate and save with retries on unique collisions
            attempts = 0
            while attempts < 5:
                try:
                    with transaction.atomic():
                        if needs_asset:
                            # reuse the model save logic by setting asset_id to NEW so save generates
                            m.asset_id = 'NEW'
                        if needs_num:
                            m.numero_inventaire = ''
                        m.save()
                    self.stdout.write(self.style.SUCCESS(f'Backfilled Materiel id={m.id} -> {m.asset_id} / {m.numero_inventaire}'))
                    count += 1
                    break
                except IntegrityError as e:
                    attempts += 1
                    self.stdout.write(self.style.WARNING(f'IntegrityError for materiel id={m.id}, attempt {attempts}: {e}'))
                    time.sleep(0.2 * attempts)
                    # reload and retry
                    m.refresh_from_db()

        self.stdout.write(self.style.SUCCESS(f'Done. Backfilled {count} materiel(s).'))
