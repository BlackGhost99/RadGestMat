#!/usr/bin/env python
"""
Script pour créer des données de test
"""
import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'radgestmat.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from assets.models import Departement, Categorie, Materiel, Client
from django.contrib.auth.models import User
from django.utils import timezone

def create_test_data():
    """Crée des données de test"""
    
    # Créer un département
    dept, created = Departement.objects.get_or_create(
        code='FRONT',
        defaults={'nom': 'Front Office', 'description': 'Réception et Accueil'}
    )
    print(f"✓ Département: {dept.nom}")
    
    # Créer des catégories
    categories_data = [
        ('Informatique', 'Ordinateurs et équipements informatiques'),
        ('Mobilier', 'Chaises, tables, meubles'),
        ('Électroménager', 'Réfrigérateurs, fours, cuisines'),
        ('Décoration', 'Peintures, cadres, objets de décoration'),
    ]
    
    categories = {}
    for nom, desc in categories_data:
        cat, _ = Categorie.objects.get_or_create(
            nom=nom,
            departement=dept,
            defaults={'description': desc}
        )
        categories[nom] = cat
        print(f"✓ Catégorie: {nom}")
    
    # Créer du matériel
    materials_data = [
        {
            'asset_id': 'ADAPT001',
            'numero_inventaire': 'INV-001-2024',
            'nom': 'Ordinateur Réception',
            'categorie': categories['Informatique'],
            'marque': 'Dell',
            'modele': 'OptiPlex 7090',
            'numero_serie': 'SN123456',
            'etat_technique': 'FONCTIONNEL',
            'statut_disponibilite': 'DISPONIBLE',
            'date_achat': '2023-06-15',
            'prix': 1200.00,
            'description': 'Ordinateur de bureau pour la réception'
        },
        {
            'asset_id': 'ADAPT002',
            'numero_inventaire': 'INV-002-2024',
            'nom': 'Chaise de Bureau',
            'categorie': categories['Mobilier'],
            'marque': 'Steelcase',
            'modele': 'Leap',
            'numero_serie': 'SN789012',
            'etat_technique': 'FONCTIONNEL',
            'statut_disponibilite': 'DISPONIBLE',
            'date_achat': '2022-01-10',
            'prix': 800.00,
            'description': 'Chaise ergonomique pour le bureau'
        },
        {
            'asset_id': 'ADAPT003',
            'numero_inventaire': 'INV-003-2024',
            'nom': 'Imprimante Réseau',
            'categorie': categories['Informatique'],
            'marque': 'HP',
            'modele': 'LaserJet Pro M428',
            'numero_serie': 'SN345678',
            'etat_technique': 'FONCTIONNEL',
            'statut_disponibilite': 'DISPONIBLE',
            'date_achat': '2023-03-20',
            'prix': 500.00,
            'description': 'Imprimante réseau A4/A3'
        },
        {
            'asset_id': 'ADAPT004',
            'numero_inventaire': 'INV-004-2024',
            'nom': 'Réfrigérateur Cuisine',
            'categorie': categories['Électroménager'],
            'marque': 'Electrolux',
            'modele': 'ERF2404',
            'numero_serie': 'SN901234',
            'etat_technique': 'FONCTIONNEL',
            'statut_disponibilite': 'DISPONIBLE',
            'date_achat': '2021-12-05',
            'prix': 2500.00,
            'description': 'Réfrigérateur professionnel'
        },
        {
            'asset_id': 'ADAPT005',
            'numero_inventaire': 'INV-005-2024',
            'nom': 'Tableau de Décoration',
            'categorie': categories['Décoration'],
            'marque': 'Artiste Inconnu',
            'modele': 'Abstrait Bleu',
            'numero_serie': '',
            'etat_technique': 'FONCTIONNEL',
            'statut_disponibilite': 'DISPONIBLE',
            'date_achat': '2023-05-12',
            'prix': 300.00,
            'description': 'Tableau abstrait pour la décoration murale'
        },
    ]
    
    for data in materials_data:
        materiel, created = Materiel.objects.get_or_create(
            asset_id=data['asset_id'],
            defaults={**data, 'departement': dept}
        )
        if created:
            print(f"✓ Matériel: {materiel.nom} ({materiel.asset_id})")
        else:
            print(f"  Matériel existant: {materiel.nom}")
    
    # Créer des clients de test
    clients_data = [
        {
            'nom': 'Chambre 101',
            'type_client': 'HEBERGEMENT',
            'email': 'client101@example.com',
            'telephone': '01234567890',
            'numero_chambre': '101',
        },
        {
            'nom': 'Salle de Conférence A',
            'type_client': 'CONFERENCE',
            'email': 'conf@example.com',
            'telephone': '01234567891',
            'nom_evenement': 'Réunion Annuelle',
        },
        {
            'nom': 'Service Ménage',
            'type_client': 'INTERNE',
            'email': 'menage@hotel.com',
            'telephone': '01234567892',
        },
    ]
    
    for data in clients_data:
        client, created = Client.objects.get_or_create(
            nom=data['nom'],
            defaults={**data, 'departement': dept}
        )
        if created:
            print(f"✓ Client: {client.nom}")
        else:
            print(f"  Client existant: {client.nom}")
    
    print("\n✅ Données de test créées avec succès!")

if __name__ == '__main__':
    create_test_data()
