# assets/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q, Max
from django.http import JsonResponse
from django.core.exceptions import PermissionDenied
from .forms import MaterielForm, ClientForm, AttributionForm
from .models import Materiel, Departement, Categorie, Attribution, Client, Alerte
from .forms import CheckInForm
from django.utils import timezone
from django.contrib import messages
from .models import HistoriqueAttribution
from users.permissions import role_required, can_view_department, can_manage_department, can_perform_checkout
from .services import AlerteService

@login_required
def materiel_create(request):
    # récupère département injecté par votre middleware si présent
    departement = getattr(request, 'departement', None)

    if request.method == 'POST':
        form = MaterielForm(request.POST, request.FILES, departement=departement)
        if form.is_valid():
            materiel = form.save(commit=False)
            
            # Assigner le département (doit être fait en premier)
            if departement and (not getattr(materiel, 'departement_id', None)):
                materiel.departement = departement
            
            # S'assurer que le département est assigné avant de générer les IDs
            if not materiel.departement and departement:
                materiel.departement = departement
            
            # Générer automatiquement asset_id (toujours pour les nouvelles créations)
            # Si asset_id est vide, 'NEW', ou ne commence pas par 'OKP-', on génère un nouveau
            asset_id_value = getattr(materiel, 'asset_id', '') or ''
            if (not asset_id_value or 
                asset_id_value.strip() == '' or 
                asset_id_value == 'NEW' or 
                (asset_id_value and not asset_id_value.startswith('OKP-'))):
                
                # Trouver le dernier asset_id pour ce département
                if materiel.departement:
                    dernier_asset = Materiel.objects.filter(
                        departement=materiel.departement,
                        asset_id__startswith='OKP-'
                    ).order_by('-asset_id').first()
                    
                    if dernier_asset and dernier_asset.asset_id:
                        try:
                            # Extraire le numéro et incrémenter
                            dernier_num = int(dernier_asset.asset_id.split('-')[1])
                            nouveau_num = dernier_num + 1
                        except (ValueError, IndexError):
                            nouveau_num = 1
                    else:
                        nouveau_num = 1
                    
                    materiel.asset_id = f"OKP-{nouveau_num:06d}"
                else:
                    # Si pas de département, utiliser une valeur par défaut
                    materiel.asset_id = "OKP-000001"
            
            # Générer automatiquement numero_inventaire (toujours pour les nouvelles créations)
            numero_inv_value = getattr(materiel, 'numero_inventaire', '') or ''
            if (not numero_inv_value or 
                numero_inv_value.strip() == '' or
                (numero_inv_value and not numero_inv_value.startswith('RAD-'))):
                
                # Trouver le dernier numero_inventaire pour ce département
                if materiel.departement:
                    dernier_inv = Materiel.objects.filter(
                        departement=materiel.departement,
                        numero_inventaire__startswith='RAD-'
                    ).order_by('-numero_inventaire').first()
                    
                    if dernier_inv and dernier_inv.numero_inventaire:
                        try:
                            # Extraire le numéro et incrémenter
                            dernier_num = int(dernier_inv.numero_inventaire.split('-')[1])
                            nouveau_num = dernier_num + 1
                        except (ValueError, IndexError):
                            nouveau_num = 1
                    else:
                        nouveau_num = 1
                    
                    materiel.numero_inventaire = f"RAD-{nouveau_num:06d}"
                else:
                    # Si pas de département, utiliser une valeur par défaut
                    materiel.numero_inventaire = "RAD-000001"
            
            materiel.save()
            # form.save_m2m() si champs M2M présents
            try:
                form.save_m2m()
            except Exception:
                pass
            return redirect('assets:materiel_detail', pk=materiel.pk)
        else:
            # utile pour debug : vérifiez form.errors dans la console serveur
            print("Materiel create errors:", form.errors)
    else:
        initial = {}
        if departement:
            initial['departement'] = departement
        form = MaterielForm(initial=initial, departement=departement)
    
    # Récupérer les noms de matériels existants pour le département
    noms_existants = Materiel.objects.filter(departement=departement).values_list('nom', flat=True).distinct().order_by('nom')
    categories = Categorie.objects.filter(departement=departement).order_by('nom')
    
    # Générer les valeurs par défaut pour asset_id et numero_inventaire
    if departement:
        # Trouver le dernier asset_id
        dernier_asset = Materiel.objects.filter(
            departement=departement,
            asset_id__startswith='OKP-'
        ).order_by('-asset_id').first()
        
        if dernier_asset and dernier_asset.asset_id:
            try:
                dernier_num = int(dernier_asset.asset_id.split('-')[1])
                nouveau_num = dernier_num + 1
            except (ValueError, IndexError):
                nouveau_num = 1
        else:
            nouveau_num = 1
        asset_id_default = f"OKP-{nouveau_num:06d}"
        
        # Trouver le dernier numero_inventaire
        dernier_inv = Materiel.objects.filter(
            departement=departement,
            numero_inventaire__startswith='RAD-'
        ).order_by('-numero_inventaire').first()
        
        if dernier_inv and dernier_inv.numero_inventaire:
            try:
                dernier_num = int(dernier_inv.numero_inventaire.split('-')[1])
                nouveau_num = dernier_num + 1
            except (ValueError, IndexError):
                nouveau_num = 1
        else:
            nouveau_num = 1
        numero_inv_default = f"RAD-{nouveau_num:06d}"
    else:
        asset_id_default = "OKP-000001"
        numero_inv_default = "RAD-000001"

    return render(request, 'assets/materiel_form.html', {
        'form': form,
        'title': 'Ajouter du matériel',
        'materiel': None,
        'noms_existants': noms_existants,
        'categories': categories,
        'asset_id_default': asset_id_default,
        'numero_inv_default': numero_inv_default,
    })

@login_required
def api_noms_materiels(request):
    """API pour récupérer les noms de matériels existants"""
    departement = getattr(request, 'departement', None)
    if not departement:
        return JsonResponse({'error': 'Département non trouvé'}, status=400)
    
    categorie_id = request.GET.get('categorie_id')
    query = request.GET.get('q', '')
    
    materiels = Materiel.objects.filter(departement=departement)
    
    if categorie_id:
        materiels = materiels.filter(categorie_id=categorie_id)
    
    if query:
        materiels = materiels.filter(nom__icontains=query)
    
    noms = materiels.values_list('nom', flat=True).distinct().order_by('nom')
    
    return JsonResponse({'noms': list(noms)})

@login_required
def api_creer_nom_materiel(request):
    """API pour créer un nouveau nom de matériel"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Méthode non autorisée'}, status=405)
    
    departement = getattr(request, 'departement', None)
    if not departement:
        return JsonResponse({'error': 'Département non trouvé'}, status=400)
    
    nom = request.POST.get('nom', '').strip()
    categorie_id = request.POST.get('categorie_id')
    
    if not nom:
        return JsonResponse({'error': 'Le nom est requis'}, status=400)
    
    # Vérifier si le nom existe déjà
    if Materiel.objects.filter(departement=departement, nom=nom).exists():
        return JsonResponse({'error': 'Ce nom de matériel existe déjà'}, status=400)
    
    # Vérifier la catégorie
    if categorie_id:
        try:
            categorie = Categorie.objects.get(id=categorie_id, departement=departement)
        except Categorie.DoesNotExist:
            return JsonResponse({'error': 'Catégorie non trouvée'}, status=400)
    else:
        categorie = None
    
    return JsonResponse({
        'success': True,
        'nom': nom,
        'categorie_id': categorie_id,
        'message': 'Nom de matériel créé avec succès'
    })

@login_required
def api_creer_categorie(request):
    """API pour créer une nouvelle catégorie"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Méthode non autorisée'}, status=405)
    
    departement = getattr(request, 'departement', None)
    if not departement:
        return JsonResponse({'error': 'Département non trouvé'}, status=400)
    
    nom = request.POST.get('nom', '').strip()
    description = request.POST.get('description', '').strip()
    
    if not nom:
        return JsonResponse({'error': 'Le nom est requis'}, status=400)
    
    # Vérifier si la catégorie existe déjà pour ce département
    if Categorie.objects.filter(departement=departement, nom=nom).exists():
        return JsonResponse({'error': 'Cette catégorie existe déjà'}, status=400)
    
    # Créer la catégorie
    try:
        categorie = Categorie.objects.create(
            nom=nom,
            departement=departement,
            description=description or f'Catégorie {nom}'
        )
        return JsonResponse({
            'success': True,
            'categorie_id': categorie.id,
            'nom': categorie.nom,
            'message': 'Catégorie créée avec succès'
        })
    except Exception as e:
        return JsonResponse({'error': f'Erreur lors de la création: {str(e)}'}, status=500)

@login_required
def dashboard(request):
    """Tableau de bord avec données filtrées selon le rôle"""
    profil = getattr(request, 'profil_utilisateur', None)
    
    # Super Admin: voir tous les données
    if profil and profil.role == 'SUPER_ADMIN':
        total_materiel = Materiel.objects.count()
        materiel_disponible = Materiel.objects.filter(statut_disponibilite='DISPONIBLE').count()
        materiel_attribue = Materiel.objects.filter(statut_disponibilite='ATTRIBUE').count()
        materiel_defectueux = Materiel.objects.filter(etat_technique='DEFECTUEUX').count()
        materiel_recent = Materiel.objects.select_related('categorie', 'departement')\
                            .order_by('-date_creation')[:3]
        departements_list = Departement.objects.all()
    else:
        # Utilisateur du département: voir seulement son département
        departement = getattr(request, 'departement', None)
        if not departement:
            departement, _ = Departement.objects.get_or_create(
                code='DEF',
                defaults={'nom': 'Département par défaut'}
            )
        
        total_materiel = Materiel.objects.filter(departement=departement).count()
        materiel_disponible = Materiel.objects.filter(departement=departement, statut_disponibilite='DISPONIBLE').count()
        materiel_attribue = Materiel.objects.filter(departement=departement, statut_disponibilite='ATTRIBUE').count()
        materiel_defectueux = Materiel.objects.filter(departement=departement, etat_technique='DEFECTUEUX').count()
        materiel_recent = Materiel.objects.filter(departement=departement)\
                            .select_related('categorie', 'departement')\
                            .order_by('-date_creation')[:3]
        departements_list = [departement]

    # Statistiques par département
    departements = []
    for dept in departements_list:
        total = Materiel.objects.filter(departement=dept).count()
        disponible = Materiel.objects.filter(departement=dept, statut_disponibilite='DISPONIBLE').count()
        attribue = Materiel.objects.filter(departement=dept, statut_disponibilite='ATTRIBUE').count()
        departements.append({
            'nom': dept.nom,
            'total': total,
            'disponible': disponible,
            'attribue': attribue,
        })
    
    # Récupérer les alertes non réglées (limité à 3 pour le dashboard)
    departement = getattr(request, 'departement', None)
    alertes_recentes = AlerteService.get_alertes_non_reglementees(departement)[:3]
    nombre_alertes_critiques = AlerteService.get_nombre_alertes_critiques(departement)

    context = {
        'total_materiel': total_materiel,
        'materiel_disponible': materiel_disponible,
        'materiel_attribue': materiel_attribue,
        'materiel_defectueux': materiel_defectueux,
        'materiel_recent': materiel_recent,
        'departements': departements,
        'alertes_recentes': alertes_recentes,
        'nombre_alertes_critiques': nombre_alertes_critiques,
    }
    return render(request, 'assets/dashboard.html', context)

@login_required
def materiel_list(request):
    """Liste tous les matériels groupés par nom d'équipement avec quantités."""
    departement = getattr(request, 'departement', None)
    if not departement:
        departement, _ = Departement.objects.get_or_create(
            code='DEF',
            defaults={'nom': 'Département par défaut'}
        )
    
    query = request.GET.get('q', '')
    categorie_filter = request.GET.get('categorie', '')
    
    # Base QuerySet filtré par département
    materiels_base = Materiel.objects.filter(departement=departement).select_related('categorie', 'departement')
    
    # Filtres de recherche
    if query:
        materiels_base = materiels_base.filter(
            Q(nom__icontains=query) |
            Q(numero_inventaire__icontains=query) |
            Q(numero_serie__icontains=query) |
            Q(modele__icontains=query) |
            Q(marque__icontains=query) |
            Q(asset_id__icontains=query)
        )
    
    if categorie_filter:
        materiels_base = materiels_base.filter(categorie_id=categorie_filter)
    
    # Grouper par nom d'équipement
    groupes_materiels = materiels_base.values('nom', 'categorie').annotate(
        quantite=Count('id'),
        date_modification_max=Max('date_modification')
    ).order_by('nom')
    
    # Enrichir avec les informations de catégorie
    groupes_enrichis = []
    for groupe in groupes_materiels:
        nom = groupe['nom']
        categorie_id = groupe.get('categorie')
        
        # Récupérer un exemple de matériel pour obtenir la catégorie
        materiel_exemple = materiels_base.filter(nom=nom).first()
        
        # Compter les statuts
        total = materiels_base.filter(nom=nom).count()
        disponible = materiels_base.filter(nom=nom, statut_disponibilite='DISPONIBLE', etat_technique='FONCTIONNEL').count()
        attribue = materiels_base.filter(nom=nom, statut_disponibilite='ATTRIBUE').count()
        maintenance = materiels_base.filter(nom=nom, statut_disponibilite='MAINTENANCE').count()
        
        groupes_enrichis.append({
            'nom': nom,
            'categorie': materiel_exemple.categorie if materiel_exemple else None,
            'quantite': total,
            'disponible': disponible,
            'attribue': attribue,
            'maintenance': maintenance,
            'date_modification': groupe['date_modification_max'],
        })
    
    # Statistiques pour les filtres
    total_materiels = Materiel.objects.filter(departement=departement).count()
    stats = {
        'total': total_materiels,
        'disponible': Materiel.objects.filter(departement=departement, statut_disponibilite='DISPONIBLE').count(),
        'attribue': Materiel.objects.filter(departement=departement, statut_disponibilite='ATTRIBUE').count(),
        'maintenance': Materiel.objects.filter(departement=departement, statut_disponibilite='MAINTENANCE').count(),
        'hors_service': Materiel.objects.filter(departement=departement, statut_disponibilite='HORS_SERVICE').count(),
    }
    
    # Catégories disponibles pour les filtres
    categories = Categorie.objects.filter(departement=departement)
    
    context = {
        'groupes_materiels': groupes_enrichis,
        'query': query,
        'categorie_filter': categorie_filter,
        'stats': stats,
        'categories': categories,
    }
    
    return render(request, 'assets/materiel_list.html', context)

@login_required
def materiel_group_detail(request, nom):
    """Affiche tous les matériels d'un groupe (même nom d'équipement)"""
    departement = getattr(request, 'departement', None)
    if not departement:
        departement, _ = Departement.objects.get_or_create(
            code='DEF',
            defaults={'nom': 'Département par défaut'}
        )
    
    # Récupérer tous les matériels avec ce nom
    materiels = Materiel.objects.filter(
        nom=nom,
        departement=departement
    ).select_related('categorie', 'departement').order_by('asset_id')
    
    if not materiels.exists():
        messages.error(request, f'Aucun matériel trouvé avec le nom "{nom}".')
        return redirect('assets:materiel_list')
    
    # Statistiques du groupe
    stats_groupe = {
        'total': materiels.count(),
        'disponible': materiels.filter(statut_disponibilite='DISPONIBLE', etat_technique='FONCTIONNEL').count(),
        'attribue': materiels.filter(statut_disponibilite='ATTRIBUE').count(),
        'maintenance': materiels.filter(statut_disponibilite='MAINTENANCE').count(),
        'defectueux': materiels.filter(etat_technique='DEFECTUEUX').count(),
    }
    
    # Catégorie (tous les matériels du groupe ont la même catégorie normalement)
    categorie = materiels.first().categorie if materiels.exists() else None
    
    context = {
        'nom_equipement': nom,
        'materiels': materiels,
        'stats_groupe': stats_groupe,
        'categorie': categorie,
    }
    
    return render(request, 'assets/materiel_group_detail.html', context)

@login_required
def materiel_detail(request, pk):
    """Affiche les détails d'un matériel."""
    # Permettre l'accès à tous les matériels (Phase 1 MVP)
    # Phase 2: implémenter les permissions par département
    materiel = get_object_or_404(Materiel, pk=pk)
    
    # Attribution active
    attribution_active = Attribution.objects.filter(
        materiel=materiel, 
        date_retour_effective__isnull=True
    ).select_related('client', 'employe_responsable').first()
    
    # Historique des attributions
    historique = Attribution.objects.filter(
        materiel=materiel
    ).select_related('client', 'employe_responsable').order_by('-date_attribution')[:10]
    
    # Alertes liées à ce matériel
    alertes = Alerte.objects.filter(
        materiel=materiel,
        reglementee=False
    ).order_by('-date_creation')[:5]
    
    context = {
        'materiel': materiel,
        'attribution_active': attribution_active,
        'historique': historique,
        'alertes': alertes,
    }
    
    return render(request, 'assets/materiel_detail.html', context)


@login_required
def materiel_update(request, pk):
    """Met à jour un matériel existant."""
    materiel = get_object_or_404(Materiel, pk=pk)
    departement = materiel.departement
    
    if request.method == 'POST':
        form = MaterielForm(request.POST, request.FILES, instance=materiel, departement=departement)
        if form.is_valid():
            form.save()
            return redirect('assets:materiel_detail', pk=materiel.pk)
    else:
        form = MaterielForm(instance=materiel, departement=departement)
    
    # Récupérer les noms de matériels existants pour le département
    noms_existants = Materiel.objects.filter(departement=departement).values_list('nom', flat=True).distinct().order_by('nom')
    categories = Categorie.objects.filter(departement=departement).order_by('nom')
    
    return render(request, 'assets/materiel_form.html', {
        'form': form, 
        'materiel': materiel,
        'title': 'Modifier le matériel',
        'noms_existants': noms_existants,
        'categories': categories,
        'asset_id_default': None,
        'numero_inv_default': None,
    })


@login_required
def materiel_delete(request, pk):
    """Supprime un matériel."""
    materiel = get_object_or_404(Materiel, pk=pk)
    
    if request.method == 'POST':
        materiel.delete()
        return redirect('assets:materiel_list')
    
    return render(request, 'assets/materiel_confirm_delete.html', {'materiel': materiel})

# Vues temporaires pour les autres fonctionnalités
@login_required
def scan_qr(request):
    """Affiche la page de scan de code QR."""
    return render(request, 'assets/scan_qr.html')


@login_required
def scan_result(request, asset_id):
    """Affiche le résultat du scan QR."""
    try:
        materiel = Materiel.objects.get(asset_id=asset_id)
        return render(request, 'assets/scan_result.html', {'materiel': materiel})
    except Materiel.DoesNotExist:
        messages.error(request, 'Matériel non trouvé.')
        return redirect('assets:scan_qr')


@login_required
def checkout(request, asset_id):
    """Check-out (attribution) pour le matériel identifié par `asset_id`."""
    from .forms import QuickClientForm
    
    materiel = get_object_or_404(Materiel, asset_id=asset_id)
    profil = getattr(request, 'profil_utilisateur', None)
    
    # Vérifier les permissions: l'utilisateur doit avoir accès au département
    if profil and profil.role not in ['SUPER_ADMIN', 'DEPT_MANAGER', 'DEPT_USER']:
        raise PermissionDenied("Vous n'avez pas les permissions pour effectuer un check-out.")
    
    if profil and profil.role != 'SUPER_ADMIN' and profil.departement_id != materiel.departement_id:
        raise PermissionDenied("Vous n'avez accès qu'à votre département.")

    if materiel.statut_disponibilite != Materiel.STATUT_DISPONIBLE:
        messages.error(request, 'Ce matériel n\'est pas disponible pour attribution.')
        return redirect('assets:materiel_detail', pk=materiel.pk)

    # Initialiser les formulaires
    form = None
    quick_form = QuickClientForm()

    # Gérer la création rapide d'un client (AJAX ou POST)
    if request.method == 'POST' and request.POST.get('action') == 'create_client':
        quick_form = QuickClientForm(request.POST)
        if quick_form.is_valid():
            client = quick_form.save()
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                # Réponse AJAX
                return JsonResponse({'success': True, 'client_id': client.id, 'client_name': client.nom})
            else:
                # Redirection standard
                messages.success(request, f'Client "{client.nom}" créé avec succès.')
                return redirect('assets:materiel_checkout', asset_id=asset_id)
        else:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'errors': quick_form.errors}, status=400)
            form = AttributionForm(initial={'materiel': materiel.pk})
    # Traiter le formulaire d'attribution
    elif request.method == 'POST':
        form = AttributionForm(request.POST)
        if form.is_valid():
            attribution = form.save(commit=False)
            attribution.employe_responsable = request.user
            attribution.departement = materiel.departement
            attribution.materiel = materiel
            attribution.save()

            # Historique
            HistoriqueAttribution.objects.create(
                attribution=attribution,
                action=HistoriqueAttribution.ACTION_CHECK_OUT,
                utilisateur=request.user,
                etat_avant=Materiel.STATUT_DISPONIBLE,
                etat_apres=Materiel.STATUT_ATTRIBUE,
                notes=attribution.notes
            )

            messages.success(request, 'Attribution enregistrée.')
            return redirect('assets:materiel_detail', pk=materiel.pk)
    else:
        # Préremplir le formulaire pour ce matériel (GET)
        form = AttributionForm(initial={'materiel': materiel.pk})

    return render(request, 'assets/check_out.html', {
        'form': form, 
        'quick_form': quick_form,
        'materiel': materiel
    })


@login_required
def checkin(request, asset_id):
    """Check-in (retour) pour le matériel identifié par `asset_id`."""
    materiel = get_object_or_404(Materiel, asset_id=asset_id)
    attribution = Attribution.objects.filter(materiel=materiel, date_retour_effective__isnull=True).select_related('client').first()

    if not attribution:
        messages.error(request, 'Aucune attribution active trouvée pour ce matériel.')
        return redirect('assets:materiel_detail', pk=materiel.pk)

    if request.method == 'POST':
        form = CheckInForm(request.POST)
        if form.is_valid():
            date_retour = form.cleaned_data.get('date_retour_effective') or timezone.now().date()
            raison_non_retour = form.cleaned_data.get('raison_non_retour')
            description_damage = form.cleaned_data.get('description_damage')
            notes = form.cleaned_data.get('notes')
            maintenance = form.cleaned_data.get('mettre_en_maintenance')

            attribution.date_retour_effective = date_retour
            if notes:
                attribution.notes = (attribution.notes or '') + '\n' + notes
            attribution.save()

            # Mettre à jour le matériel
            etat_avant = materiel.statut_disponibilite
            if maintenance or raison_non_retour in ['DAMAGE', 'OTHER']:
                materiel.statut_disponibilite = Materiel.STATUT_MAINTENANCE
                materiel.etat_technique = Materiel.ETAT_EN_MAINTENANCE
            else:
                materiel.statut_disponibilite = Materiel.STATUT_DISPONIBLE
            materiel.save()

            # Historique
            historique_notes = notes or ''
            if raison_non_retour != 'NORMAL':
                historique_notes += f'\n[Raison: {dict(CheckInForm.RAISON_CHOICES).get(raison_non_retour)}]'
                if description_damage:
                    historique_notes += f'\n[Détails: {description_damage}]'
            
            HistoriqueAttribution.objects.create(
                attribution=attribution,
                action=HistoriqueAttribution.ACTION_CHECK_IN,
                utilisateur=request.user,
                etat_avant=etat_avant,
                etat_apres=materiel.statut_disponibilite,
                notes=historique_notes
            )

            # Auto-créer une Alerte si matériel perdu ou endommagé
            alerte_created = None
            if raison_non_retour == 'LOST':
                alerte_created = Alerte.objects.create(
                    type_alerte=Alerte.TYPE_PERDU,
                    severite=Alerte.SEVERITE_CRITICAL,
                    materiel=materiel,
                    attribution=attribution,
                    departement=materiel.departement,
                    description=f"Matériel perdu lors de l'attribution à {attribution.client.nom}\n{description_damage or ''}"
                )
            elif raison_non_retour == 'DAMAGE':
                alerte_created = Alerte.objects.create(
                    type_alerte=Alerte.TYPE_DEFECTUEUX,
                    severite=Alerte.SEVERITE_CRITICAL,
                    materiel=materiel,
                    attribution=attribution,
                    departement=materiel.departement,
                    description=f"Matériel endommagé lors de l'attribution à {attribution.client.nom}\nDégâts: {description_damage or 'Non spécifiés'}"
                )

            # Stocker les données dans la session pour la page de confirmation
            request.session['checkin_data'] = {
                'materiel_asset_id': materiel.asset_id,
                'materiel_nom': materiel.nom,
                'materiel_pk': materiel.pk,
                'materiel_statut': materiel.get_statut_disponibilite_display(),
                'client_nom': attribution.client.nom,
                'date_attribution': attribution.date_attribution.isoformat(),
                'date_retour': date_retour.isoformat(),
                'raison': raison_non_retour,
                'description_damage': description_damage,
                'notes': notes,
                'maintenance': maintenance,
                'alerte_id': alerte_created.id if alerte_created else None,
                'statut_color': 'warning' if maintenance else 'success',
            }

            return redirect('assets:checkin_success')
    else:
        form = CheckInForm(initial={'date_retour_effective': timezone.now().date()})

    return render(request, 'assets/check_in.html', {'form': form, 'materiel': materiel, 'attribution': attribution})

@login_required
def checkin_success(request):
    """Page de confirmation du check-in avec détails."""
    # Récupérer les données de la session
    checkin_data = request.session.pop('checkin_data', None)
    
    if not checkin_data:
        return redirect('assets:materiel_list')
    
    # Récupérer l'alerte si créée
    alerte = None
    if checkin_data.get('alerte_id'):
        alerte = Alerte.objects.filter(id=checkin_data['alerte_id']).first()
    
    context = {
        **checkin_data,
        'alerte': alerte,
    }
    
    return render(request, 'assets/check_in_success.html', context)

# ========== CLIENT VIEWS ===========
@login_required
def client_list(request):
    clients = Client.objects.all()
    search = request.GET.get('search', '')
    type_filter = request.GET.get('type', '')
    
    if search:
        clients = clients.filter(nom__icontains=search)
    if type_filter:
        clients = clients.filter(type=type_filter)
    
    return render(request, 'assets/client_list.html', {'clients': clients})

@login_required
def client_create(request):
    if request.method == 'POST':
        form = ClientForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('assets:client_list')
    else:
        form = ClientForm()
    return render(request, 'assets/client_form.html', {'form': form})

@login_required
def client_detail(request, pk):
    client = get_object_or_404(Client, pk=pk)
    # Utiliser une requête explicite au lieu de l'attribut related_name
    # (utile si le FK dans Attribution n'a pas related_name='attribution_set')
    attributions = Attribution.objects.filter(client=client).order_by('-date_attribution')
    return render(request, 'assets/client_detail.html', {
        'client': client,
        'attributions': attributions
    })

@login_required
def client_update(request, pk):
    client = get_object_or_404(Client, pk=pk)
    if request.method == 'POST':
        form = ClientForm(request.POST, instance=client)
        if form.is_valid():
            form.save()
            return redirect('assets:client_detail', pk=client.pk)
    else:
        form = ClientForm(instance=client)
    return render(request, 'assets/client_form.html', {'form': form, 'client': client})

@login_required
def client_delete(request, pk):
    client = get_object_or_404(Client, pk=pk)
    if request.method == 'POST':
        client.delete()
        return redirect('assets:client_list')
    return render(request, 'assets/client_confirm_delete.html', {'client': client})

# ========== ATTRIBUTION VIEWS ==========
@login_required
def attribution_list(request):
    attributions = Attribution.objects.all().order_by('-date_attribution')
    status = request.GET.get('status', 'ACTIF')
    
    # Filtrer par statut (actif = date_retour_effective null)
    if status == 'ACTIF':
        attributions = attributions.filter(date_retour_effective__isnull=True)
    elif status == 'COMPLETED':
        attributions = attributions.filter(date_retour_effective__isnull=False)
    
    return render(request, 'assets/attribution_list.html', {
        'attributions': attributions,
        'status': status
    })

@login_required
def attribution_update(request, pk):
    attribution = get_object_or_404(Attribution, pk=pk)
    if request.method == 'POST':
        form = AttributionForm(request.POST, instance=attribution)
        if form.is_valid():
            form.save()
            return redirect('assets:attribution_list')
    else:
        form = AttributionForm(instance=attribution)
    return render(request, 'assets/attribution_form.html', {
        'form': form,
        'attribution': attribution
    })

# ========== ALERTES VIEWS ==========
@login_required
def alerte_list(request):
    """Liste toutes les alertes non réglées"""
    departement = getattr(request, 'departement', None)
    profil = getattr(request, 'profil_utilisateur', None)
    
    # Super Admin peut voir toutes les alertes
    if profil and profil.role == 'SUPER_ADMIN':
        alertes = AlerteService.get_alertes_non_reglementees()
    else:
        alertes = AlerteService.get_alertes_non_reglementees(departement)
    
    # Filtres
    type_filter = request.GET.get('type', '')
    severite_filter = request.GET.get('severite', '')
    
    if type_filter:
        alertes = alertes.filter(type_alerte=type_filter)
    
    if severite_filter:
        alertes = alertes.filter(severite=severite_filter)
    
    # Statistiques
    stats = {
        'total': alertes.count(),
        'critique': alertes.filter(severite=Alerte.SEVERITE_CRITICAL).count(),
        'warning': alertes.filter(severite=Alerte.SEVERITE_WARNING).count(),
        'info': alertes.filter(severite=Alerte.SEVERITE_INFO).count(),
        'retard': alertes.filter(type_alerte=Alerte.TYPE_RETARD).count(),
        'defectueux': alertes.filter(type_alerte=Alerte.TYPE_DEFECTUEUX).count(),
        'stock_critique': alertes.filter(type_alerte=Alerte.TYPE_STOCK_CRITIQUE).count(),
        'perdu': alertes.filter(type_alerte=Alerte.TYPE_PERDU).count(),
    }
    
    context = {
        'alertes': alertes,
        'stats': stats,
        'type_filter': type_filter,
        'severite_filter': severite_filter,
        'type_choices': Alerte.TYPE_CHOICES,
        'severite_choices': Alerte.SEVERITE_CHOICES,
    }
    
    return render(request, 'assets/alerte_list.html', context)


@login_required
def alerte_detail(request, pk):
    """Affiche les détails d'une alerte"""
    alerte = get_object_or_404(Alerte, pk=pk)
    
    # Vérifier les permissions
    departement = getattr(request, 'departement', None)
    profil = getattr(request, 'profil_utilisateur', None)
    
    if profil and profil.role != 'SUPER_ADMIN' and departement and alerte.departement != departement:
        raise PermissionDenied("Vous n'avez pas accès à cette alerte.")
    
    context = {
        'alerte': alerte,
    }
    
    return render(request, 'assets/alerte_detail.html', context)


@login_required
def alerte_marquer_reglementee(request, pk):
    """Marque une alerte comme réglée"""
    alerte = get_object_or_404(Alerte, pk=pk)
    
    # Vérifier les permissions
    departement = getattr(request, 'departement', None)
    profil = getattr(request, 'profil_utilisateur', None)
    
    if profil and profil.role != 'SUPER_ADMIN' and departement and alerte.departement != departement:
        raise PermissionDenied("Vous n'avez pas accès à cette alerte.")
    
    if request.method == 'POST':
        alerte.reglementee = True
        alerte.save()
        messages.success(request, 'Alerte marquée comme réglée.')
        return redirect('assets:alerte_list')
    
    return render(request, 'assets/alerte_confirm_reglementee.html', {'alerte': alerte})


@login_required
def alerte_detecter(request):
    """Déclenche manuellement la détection de toutes les alertes"""
    profil = getattr(request, 'profil_utilisateur', None)
    
    # Seuls les managers et super admins peuvent déclencher la détection
    if not profil or profil.role not in ['SUPER_ADMIN', 'DEPT_MANAGER']:
        raise PermissionDenied("Vous n'avez pas les permissions pour cette action.")
    
    resultats = AlerteService.detecter_toutes_alertes()
    
    messages.success(
        request,
        f"Détection terminée: {resultats['total']} nouvelle(s) alerte(s) créée(s) "
        f"(Retards: {len(resultats['retards'])}, "
        f"Défectueux: {len(resultats['defectueux'])}, "
        f"Stock critique: {len(resultats['stock_critique'])}, "
        f"Perdus: {len(resultats['perdus'])})"
    )
    
    return redirect('assets:alerte_list')
