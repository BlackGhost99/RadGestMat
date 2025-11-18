from django.core.management.base import BaseCommand
from assets.models import Materiel

class Command(BaseCommand):
    help = 'Régénère tous les QR codes avec URL check-in'

    def add_arguments(self, parser):
        parser.add_argument('--domain', type=str, default='http://localhost:8000', 
                          help='Domaine pour les URLs QR (ex: https://radgestmat.com)')

    def handle(self, *args, **options):
        domain = options['domain']
        materiels = Materiel.objects.all()
        
        import qrcode
        from django.core.files.base import ContentFile
        import io
        
        count = 0
        for materiel in materiels:
            try:
                # Générer nouveau QR code avec URL
                checkin_url = f"{domain}/materiel/{materiel.asset_id}/checkin/"
                
                qr = qrcode.QRCode(version=1, box_size=10, border=5)
                qr.add_data(checkin_url)
                qr.make(fit=True)
                img = qr.make_image(fill_color="black", back_color="white")
                qr_io = io.BytesIO()
                img.save(qr_io, format='PNG')
                qr_io.seek(0)
                filename = f"qr_{materiel.departement.code}_{materiel.asset_id}.png"
                
                # Sauvegarder
                materiel.qr_code.save(filename, ContentFile(qr_io.read()), save=False)
                materiel.save(update_fields=['qr_code'])
                count += 1
                self.stdout.write(self.style.SUCCESS(f'✓ {materiel.asset_id}'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'✗ {materiel.asset_id}: {e}'))
        
        self.stdout.write(self.style.SUCCESS(f'\n{count} QR codes régénérés avec succès !'))
        self.stdout.write(f'Domaine utilisé: {domain}')
