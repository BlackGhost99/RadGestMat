from django.core.management.base import BaseCommand

from assets.models import Salle

ROOM_NAMES = [
    "Grand Libreville",
    "Libreville 1",
    "Libreville 2",
    "Mayumba",
    "Oyem",
    "Lambaréné",
    "Franceville",
    "Portgentil",
    "Okoumé",
    "Ozigo",
    "Ebène",
    "Accajou",
    "La Marquise",
    "La pallette",
    "Olatano",
    "Salle de formation",
]

class Command(BaseCommand):
    help = 'Create conference rooms (salles) predefined list'

    def handle(self, *args, **options):
        created = 0
        for name in ROOM_NAMES:
            obj, was_created = Salle.objects.get_or_create(nom=name)
            if was_created:
                created += 1
                self.stdout.write(self.style.SUCCESS(f'Created salle: {name}'))
            else:
                self.stdout.write(f'Already exists: {name}')

        self.stdout.write(self.style.SUCCESS(f'Done. {created} salles created.'))
