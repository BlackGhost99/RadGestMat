from django.core.management.base import BaseCommand
from django.core.exceptions import ValidationError

from assets.models import Client


class Command(BaseCommand):
    help = 'Test Client.salle model validation for CONFERENCE clients'

    def handle(self, *args, **options):
        c = Client(nom='TestClientCmd', type_client=Client.TYPE_CONFERENCE)
        try:
            c.full_clean()
            self.stdout.write(self.style.SUCCESS('MODEL VALIDATION PASSED: no ValidationError raised'))
        except ValidationError as e:
            self.stdout.write(self.style.ERROR(f'MODEL VALIDATION ERROR: {e.message_dict}'))
