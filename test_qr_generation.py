import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'radgestmat.settings')
django.setup()

from assets.models import Departement, Categorie, Materiel

# Supprimer ancien
Materiel.objects.filter(asset_id='QR_TEST_001').delete()

# Créer un test matériel
dept, _ = Departement.objects.get_or_create(
    code='TEST', 
    defaults={'nom': 'Test'}
)
cat, _ = Categorie.objects.get_or_create(
    nom='Électronique', 
    defaults={'departement': dept}
)

# Créer matériel
mat = Materiel.objects.create(
    asset_id='QR_TEST_001',
    numero_inventaire='INV-QR-001',
    nom='Test QR Code',
    categorie=cat,
    departement=dept,
    etat_technique='FONCTIONNEL'
)

print(f"✓ Matériel créé: {mat.asset_id}")
print(f"✓ PK: {mat.pk}")
print(f"✓ QR Code path: {mat.qr_code.name if mat.qr_code else 'Pas de fichier'}")
print(f"✓ QR Code bool: {bool(mat.qr_code)}")
print(f"✓ QR Code url: {mat.qr_code.url if mat.qr_code else 'N/A'}")

# Vérifier le fichier
import os.path
if mat.qr_code:
    full_path = mat.qr_code.path
    exists = os.path.exists(full_path)
    print(f"✓ Fichier existe: {exists}")
    print(f"✓ Path complet: {full_path}")

