#!/usr/bin/env python
"""
Script pour importer l'inventaire IT depuis le fichier Excel
IT_Inventory_V2_Radisson.xlsx
"""
import os
import sys
import django
from decimal import Decimal, InvalidOperation
from datetime import datetime

# Configuration Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "radgestmat.settings.base")
os.environ['DB_ENGINE'] = 'django.db.backends.sqlite3'
os.environ['DB_NAME'] = 'db.sqlite3'

django.setup()

import pandas as pd
from assets.models import Departement, Categorie, Materiel

# Chemin du fichier Excel
EXCEL_FILE = r'S:\Brice\RadGestMat\docs\datasets\IT_Inventory_V2_Radisson.xlsx'


def normalize_column_name(col_name):
    """Normalise le nom de colonne pour gérer les problèmes d'encodage"""
    if not col_name:
        return None
    col_str = str(col_name)
    # Remplacer les caractères mal encodés
    replacements = {
        'Catgorie': 'Catégorie',
        'Dsignation': 'Désignation',
        'Entres': 'Entrées',
        'Numros_de_srie': 'Numéros_de_série',
        'Dtails': 'Détails',
    }
    for old, new in replacements.items():
        if old in col_str:
            col_str = col_str.replace(old, new)
    return col_str


def get_column_value(row, possible_names):
    """Récupère une valeur de colonne en essayant plusieurs noms possibles"""
    for name in possible_names:
        # Essayer le nom exact
        if name in row.index:
            return row[name]
        # Essayer avec normalisation
        normalized = normalize_column_name(name)
        for col in row.index:
            if normalize_column_name(col) == normalized:
                return row[col]
    return None


def clean_string(value):
    """Nettoie une chaîne de caractères (gère NaN, None, etc.)"""
    if pd.isna(value) or value is None:
        return None
    value = str(value).strip()
    return value if value else None


def parse_date(value):
    """Parse une date depuis Excel"""
    if pd.isna(value) or value is None:
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, str):
        try:
            return datetime.strptime(value, '%Y-%m-%d').date()
        except:
            return None
    return None


def map_statut_to_etat_technique(statut):
    """Mappe le statut Excel vers l'état technique"""
    if pd.isna(statut) or statut is None:
        return Materiel.ETAT_FONCTIONNEL
    
    statut_str = str(statut).upper().strip()
    if 'DEFECTUEUX' in statut_str or 'PANNE' in statut_str:
        return Materiel.ETAT_DEFECTUEUX
    elif 'MAINTENANCE' in statut_str:
        return Materiel.ETAT_EN_MAINTENANCE
    else:
        return Materiel.ETAT_FONCTIONNEL


def map_statut_to_disponibilite(statut, stock_actuel):
    """Mappe le statut Excel vers le statut de disponibilité"""
    if pd.isna(statut) or statut is None:
        return Materiel.STATUT_DISPONIBLE
    
    statut_str = str(statut).upper().strip()
    stock = int(stock_actuel) if not pd.isna(stock_actuel) else 0
    
    if stock <= 0:
        return Materiel.STATUT_HORS_SERVICE
    elif 'A_REAPPROVISIONNER' in statut_str:
        return Materiel.STATUT_HORS_SERVICE
    elif 'SURVEILLER' in statut_str:
        return Materiel.STATUT_DISPONIBLE
    else:
        return Materiel.STATUT_DISPONIBLE


def import_inventory():
    """Fonction principale d'import"""
    print("=" * 60)
    print("IMPORT INVENTAIRE IT - RadGestMat")
    print("=" * 60)
    print()
    
    # Vérifier que le fichier existe
    if not os.path.exists(EXCEL_FILE):
        print(f"[ERREUR] Le fichier {EXCEL_FILE} n'existe pas!")
        return
    
    # Récupérer ou créer le département IT
    try:
        dept_it = Departement.objects.get(code='IT')
        print(f"[OK] Departement IT trouve: {dept_it.nom}")
    except Departement.DoesNotExist:
        print("[ERREUR] Le departement IT n'existe pas!")
        print("   Executez d'abord: python insert_departments.py")
        return
    
    # Lire le fichier Excel
    print(f"\n[INFO] Lecture du fichier Excel: {EXCEL_FILE}")
    try:
        df = pd.read_excel(EXCEL_FILE)
        print(f"[OK] {len(df)} lignes trouvees")
    except Exception as e:
        print(f"[ERREUR] Erreur lors de la lecture du fichier: {e}")
        return
    
    # Statistiques
    stats = {
        'created': 0,
        'skipped': 0,
        'errors': 0,
        'errors_list': []
    }
    
    # Traiter chaque ligne
    print("\n[INFO] Traitement des materiels...")
    print("-" * 60)
    
    for index, row in df.iterrows():
        try:
            # Récupérer les valeurs avec gestion d'encodage
            id_materiel = clean_string(get_column_value(row, ['ID_Materiel']))
            categorie_name = clean_string(get_column_value(row, ['Catégorie', 'Catgorie']))
            designation = clean_string(get_column_value(row, ['Désignation', 'Dsignation']))
            localisation = clean_string(get_column_value(row, ['Localisation']))
            stock_actuel = get_column_value(row, ['Stock_Actuel']) or 0
            statut = clean_string(get_column_value(row, ['Statut']))
            numeros_serie = clean_string(get_column_value(row, ['Numéros_de_série', 'Numros_de_srie']))
            details = clean_string(get_column_value(row, ['Détails', 'Dtails']))
            
            # Validation: ID_Materiel est requis
            if not id_materiel:
                stats['errors'] += 1
                error_msg = f"Ligne {index + 2}: ID_Materiel manquant"
                stats['errors_list'].append(error_msg)
                print(f"[ERREUR] {error_msg}")
                continue
            
            # Validation: Désignation est requise
            if not designation:
                stats['errors'] += 1
                error_msg = f"Ligne {index + 2}: Designation manquante (ID: {id_materiel})"
                stats['errors_list'].append(error_msg)
                print(f"[ERREUR] {error_msg}")
                continue
            
            # Validation: asset_id doit être unique (vérification préalable)
            if Materiel.objects.filter(asset_id=id_materiel).exists():
                stats['skipped'] += 1
                print(f"[SKIP] Ignore (existant): {id_materiel} - {designation}")
                continue
            
            # Gérer la catégorie
            if categorie_name:
                categorie, _ = Categorie.objects.get_or_create(
                    nom=categorie_name,
                    departement=dept_it,
                    defaults={'description': f'Catégorie IT: {categorie_name}'}
                )
            else:
                # Catégorie par défaut si absente
                categorie, _ = Categorie.objects.get_or_create(
                    nom='Équipement IT',
                    departement=dept_it,
                    defaults={'description': 'Catégorie par défaut pour équipements IT'}
                )
            
            # Préparer les données du matériel
            # Utiliser ID_Materiel comme asset_id et numero_inventaire
            asset_id = id_materiel
            numero_inventaire = id_materiel  # Peut être modifié si nécessaire
            
            # Le nom est simplement la désignation
            nom = designation
            
            # Construire la description
            description_parts = []
            if details:
                description_parts.append(f"Détails: {details}")
            if not pd.isna(stock_actuel):
                description_parts.append(f"Stock actuel: {int(stock_actuel)}")
            description = " | ".join(description_parts) if description_parts else None
            
            # Mapper les statuts
            try:
                etat_technique = map_statut_to_etat_technique(statut)
                statut_disponibilite = map_statut_to_disponibilite(statut, stock_actuel)
            except Exception as e:
                stats['errors'] += 1
                error_msg = f"Ligne {index + 2}: Erreur mapping statut pour {id_materiel}: {e}"
                stats['errors_list'].append(error_msg)
                print(f"[ERREUR] {error_msg}")
                continue
            
            # Construire les notes
            notes_parts = ["Importé depuis Excel"]
            if statut:
                notes_parts.append(f"Statut original: {statut}")
            if not pd.isna(stock_actuel):
                notes_parts.append(f"Stock: {int(stock_actuel)}")
            notes = " | ".join(notes_parts)
            
            # Créer le matériel
            try:
                materiel = Materiel.objects.create(
                    asset_id=asset_id,
                    numero_inventaire=numero_inventaire,
                    nom=nom,
                    description=description,
                    categorie=categorie,
                    departement=dept_it,
                    numero_serie=numeros_serie,
                    etat_technique=etat_technique,
                    statut_disponibilite=statut_disponibilite,
                    location=localisation,  # Utiliser le nouveau champ location
                    notes=notes
                )
                stats['created'] += 1
                print(f"[OK] Cree: {asset_id} - {nom}")
            except Exception as e:
                stats['errors'] += 1
                error_msg = f"Ligne {index + 2}: Erreur creation materiel {id_materiel}: {e}"
                stats['errors_list'].append(error_msg)
                print(f"[ERREUR] {error_msg}")
                continue
                
        except Exception as e:
            stats['errors'] += 1
            error_msg = f"Ligne {index + 2}: {str(e)}"
            stats['errors_list'].append(error_msg)
            print(f"[ERREUR] Erreur ligne {index + 2}: {e}")
    
    # Afficher le rapport final
    print()
    print("=" * 60)
    print("RAPPORT D'IMPORT")
    print("=" * 60)
    total_processed = stats['created'] + stats['skipped'] + stats['errors']
    print(f"[STATS] Total de lignes traitees: {total_processed}")
    print(f"[OK] Materiels crees: {stats['created']}")
    print(f"[SKIP] Materiels ignores (deja existants): {stats['skipped']}")
    print(f"[ERREUR] Erreurs: {stats['errors']}")
    
    if stats['errors'] > 0 and stats['errors_list']:
        print("\n[WARNING] Details des erreurs:")
        for error in stats['errors_list'][:10]:  # Limiter à 10 erreurs pour la lisibilité
            print(f"  - {error}")
        if len(stats['errors_list']) > 10:
            print(f"  ... et {len(stats['errors_list']) - 10} autres erreurs")
    
    if stats['created'] > 0:
        print(f"\n[SUCCESS] {stats['created']} materiel(s) importe(s) avec succes dans le departement IT!")
    
    print()
    print("=" * 60)


if __name__ == '__main__':
    import_inventory()
