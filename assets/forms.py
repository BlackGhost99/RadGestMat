# assets/forms.py
from django import forms
from .models import Materiel, Attribution, Client

class MaterielForm(forms.ModelForm):
    nom_materiel = forms.CharField(
        label='Nom du matériel',
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'id': 'id_nom_materiel',
            'list': 'noms_materiels_list',
            'autocomplete': 'off',
            'placeholder': 'Sélectionnez ou entrez un nom'
        }),
        help_text='Sélectionnez un nom existant ou entrez un nouveau nom'
    )
    
    nom_categorie = forms.CharField(
        label='Catégorie',
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'id': 'id_nom_categorie',
            'list': 'categories_list',
            'autocomplete': 'off',
            'placeholder': 'Sélectionnez ou créez une catégorie'
        }),
        help_text='Sélectionnez une catégorie existante ou créez-en une nouvelle'
    )
    
    class Meta:
        model = Materiel
        fields = [
            'asset_id', 'numero_inventaire', 'description',
            'marque', 'modele', 'numero_serie', 'etat_technique', 'statut_disponibilite',
            'date_achat', 'prix', 'notes'
        ]
        widgets = {
            'asset_id': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Généré automatiquement'}),
            'numero_inventaire': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Généré automatiquement'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'marque': forms.TextInput(attrs={'class': 'form-control'}),
            'modele': forms.TextInput(attrs={'class': 'form-control'}),
            'numero_serie': forms.TextInput(attrs={'class': 'form-control'}),
            'etat_technique': forms.Select(attrs={'class': 'form-select'}),
            'statut_disponibilite': forms.Select(attrs={'class': 'form-select'}),
            'date_achat': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'prix': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        self.departement = kwargs.pop('departement', None)
        super().__init__(*args, **kwargs)
        
        # Si c'est une modification, préremplir le nom et la catégorie
        if self.instance and self.instance.pk:
            self.fields['nom_materiel'].initial = self.instance.nom
            if self.instance.categorie:
                self.fields['nom_categorie'].initial = self.instance.categorie.nom
            # Utiliser le département du matériel existant
            if not self.departement and self.instance.departement:
                self.departement = self.instance.departement
        
        # Rendre asset_id et numero_inventaire non requis pour la création (générés automatiquement)
        if not (self.instance and self.instance.pk):
            self.fields['asset_id'].required = False
            self.fields['numero_inventaire'].required = False
            # Rendre les champs readonly en création
            self.fields['asset_id'].widget.attrs['readonly'] = True
            self.fields['numero_inventaire'].widget.attrs['readonly'] = True
            # Permettre les valeurs vides ou 'NEW' pour la génération automatique
            self.fields['asset_id'].widget.attrs['value'] = ''
            self.fields['numero_inventaire'].widget.attrs['value'] = ''
    
    def save(self, commit=True):
        from .models import Categorie
        
        materiel = super().save(commit=False)
        
        # Assigner le département si fourni et non déjà assigné
        if self.departement and not materiel.departement_id:
            materiel.departement = self.departement
        
        # Utiliser le nom du champ personnalisé
        materiel.nom = self.cleaned_data.get('nom_materiel', '')
        
        # Gérer la catégorie
        nom_categorie = self.cleaned_data.get('nom_categorie', '').strip()
        if nom_categorie:
            # Utiliser le département du formulaire ou du matériel
            departement = self.departement or materiel.departement
            if departement:
                categorie, created = Categorie.objects.get_or_create(
                    nom=nom_categorie,
                    departement=departement,
                    defaults={'description': f'Catégorie créée automatiquement pour {nom_categorie}'}
                )
                materiel.categorie = categorie
        
        if commit:
            materiel.save()
        return materiel

class ClientForm(forms.ModelForm):
    date_creation = forms.DateTimeField(label='Date création', required=False, disabled=True, widget=forms.DateTimeInput(attrs={'class': 'form-control'}))
    date_modification = forms.DateTimeField(label='Date modification', required=False, disabled=True, widget=forms.DateTimeInput(attrs={'class': 'form-control'}))
    
    class Meta:
        model = Client
        fields = ['nom', 'type_client', 'email', 'telephone', 'numero_chambre', 'date_arrivee', 'date_depart', 'nom_evenement', 'departement', 'notes']
        widgets = {
            'nom': forms.TextInput(attrs={'class': 'form-control', 'required': True}),
            'type_client': forms.Select(attrs={'class': 'form-select', 'required': True, 'id': 'type_client'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'telephone': forms.TextInput(attrs={'class': 'form-control'}),
            'numero_chambre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: 42, 305, etc.'}),
            'date_arrivee': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'date_depart': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'nom_evenement': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Conférence Django 2025'}),
            'departement': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
        labels = {
            'nom': 'Nom *',
            'type_client': 'Type client *',
            'email': 'Email',
            'telephone': 'Téléphone',
            'numero_chambre': 'Numéro chambre',
            'date_arrivee': 'Date arrivée',
            'date_depart': 'Date départ',
            'nom_evenement': 'Nom événement',
            'departement': 'Département',
            'notes': 'Notes',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields['date_creation'].initial = self.instance.date_creation
            self.fields['date_modification'].initial = self.instance.date_modification

class QuickClientForm(forms.ModelForm):
    """Formulaire pour créer rapidement un client lors du check-out"""
    class Meta:
        model = Client
        fields = ['nom', 'type_client', 'email', 'telephone']
        widgets = {
            'nom': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nom du client', 'required': True}),
            'type_client': forms.Select(attrs={'class': 'form-select', 'required': True}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email'}),
            'telephone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Téléphone'}),
        }
        labels = {
            'nom': 'Nom *',
            'type_client': 'Type client *',
            'email': 'Email',
            'telephone': 'Téléphone',
        }


class AttributionForm(forms.ModelForm):
    class Meta:
        model = Attribution
        fields = ['materiel', 'client', 'date_retour_prevue', 'notes']
        widgets = {
            'materiel': forms.HiddenInput(),
            'client': forms.Select(attrs={'class': 'form-select', 'id': 'client_select'}),
            'date_retour_prevue': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class CheckInForm(forms.Form):
    RAISON_NORMAL = 'NORMAL'
    RAISON_DAMAGE = 'DAMAGE'
    RAISON_LOST = 'LOST'
    RAISON_OTHER = 'OTHER'
    
    RAISON_CHOICES = [
        (RAISON_NORMAL, 'Retour normal'),
        (RAISON_DAMAGE, 'Matériel endommagé'),
        (RAISON_LOST, 'Matériel perdu'),
        (RAISON_OTHER, 'Autre raison'),
    ]
    
    date_retour_effective = forms.DateField(
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}), 
        required=False,
        label='Date de retour'
    )
    raison_non_retour = forms.ChoiceField(
        choices=RAISON_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'raison_non_retour'}),
        initial=RAISON_NORMAL,
        label='Raison du retour'
    )
    description_damage = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        required=False,
        label='Description des dégâts',
        help_text='Décrivez les dégâts ou les circonstances si applicable'
    )
    notes = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}), 
        required=False,
        label='Notes supplémentaires'
    )
    mettre_en_maintenance = forms.BooleanField(
        required=False, 
        initial=False, 
        label='Mettre en maintenance après le retour'
    )