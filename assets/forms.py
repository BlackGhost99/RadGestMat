# assets/forms.py

from django import forms

from .models import Materiel, Attribution, Client, Departement, Categorie

from .models import Salle



class MaterielForm(forms.ModelForm):

    departement = forms.ModelChoiceField(

        queryset=Departement.objects.all(),

        required=False,

        widget=forms.Select(attrs={'class': 'form-select'}),

        label='Département'

    )

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

    

    categorie = forms.ModelChoiceField(

        queryset=Categorie.objects.all(),

        required=False,

        widget=forms.Select(attrs={'class': 'form-select'}),

        label='Catégorie',

        help_text='Sélectionnez une catégorie existante'

    )

    

    # Champ location personnalisé avec datalist (permet sélection ou saisie libre)

    location = forms.CharField(

        required=False,

        widget=forms.TextInput(attrs={

            'class': 'form-control',

            'list': 'locations_list',

            'autocomplete': 'off',

            'placeholder': 'Sélectionnez ou entrez une localisation'

        }),

        label='Localisation',

        help_text='Sélectionnez une localisation existante ou entrez une nouvelle'

    )

    

    class Meta:

        model = Materiel

        fields = [

            'asset_id', 'numero_inventaire', 'description',

            'marque', 'modele', 'numero_serie', 'etat_technique', 'statut_disponibilite',

            'date_achat', 'prix', 'location', 'salle', 'notes'

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



    # Exposer le choix de salle (optionnel)

    salle = forms.ModelChoiceField(

        queryset=Salle.objects.all(),

        required=False,

        widget=forms.Select(attrs={'class': 'form-select'}),

        label='Salle (optionnel)'

    )



    def __init__(self, *args, **kwargs):

        self.allow_all_categories = kwargs.pop('allow_all_categories', False)
        self.departement = kwargs.pop('departement', None)

        self.user = kwargs.pop('user', None)

        super().__init__(*args, **kwargs)

        

        # Filtrer les categories selon le departement (ou tout afficher si demande)
        if self.allow_all_categories:
            self.fields['categorie'].queryset = Categorie.objects.all().order_by('nom')
        else:
            departement = self.departement
            if self.instance and self.instance.pk and self.instance.departement:
                departement = self.instance.departement
            if departement:
                self.fields['categorie'].queryset = Categorie.objects.filter(departement=departement)
            elif self.user:
                # Si pas de departement, filtrer selon le profil utilisateur
                profil = getattr(self.user, "profilutilisateur", None)
                if profil and profil.role != "SUPER_ADMIN" and profil.departement:
                    self.fields['categorie'].queryset = Categorie.objects.filter(departement=profil.departement)
        # Si c'est une modification, préremplir le nom, la catégorie et la location

        if self.instance and self.instance.pk:

            self.fields['nom_materiel'].initial = self.instance.nom

            if self.instance.categorie:

                self.fields['categorie'].initial = self.instance.categorie

            # Préremplir la location si elle existe

            if self.instance.location:

                self.fields['location'].initial = self.instance.location

            # Utiliser le département du matériel existant

            if not self.departement and self.instance.departement:

                self.departement = self.instance.departement

            # Préremplir le champ departement si présent

            if 'departement' in self.fields:

                self.fields['departement'].initial = self.instance.departement

        

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

    

    def clean(self):

        cleaned = super().clean()

        departement = cleaned.get('departement')

        categorie = cleaned.get('categorie')

        if categorie:

            cleaned['departement'] = categorie.departement

            departement = cleaned.get('departement')

        if not departement and self.instance and self.instance.pk and self.instance.departement:

            cleaned['departement'] = self.instance.departement

            departement = cleaned.get('departement')

        if not departement:

            self.add_error('categorie', 'Selectionnez une categorie (ou un departement).')

        return cleaned

    def save(self, commit=True):

        # #region agent log

        import json, time

        with open(r's:\Brice\RadGestMat\.cursor\debug.log', 'a', encoding='utf-8') as f:

            f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"D","location":"assets/forms.py:119","message":"MaterielForm.save entry","data":{"has_location_in_cleaned":'location' in self.cleaned_data,"location_value":self.cleaned_data.get('location','NOT_IN_CLEANED') if hasattr(self,'cleaned_data') else 'NO_CLEANED_DATA'},"timestamp":int(time.time()*1000)}) + '\n')

        # #endregion

        from .models import Categorie

        

        materiel = super().save(commit=False)

        

        # Assigner le département si fourni via le formulaire (super-admin) ou via le middleware

        if 'departement' in self.cleaned_data and self.cleaned_data.get('departement'):

            materiel.departement = self.cleaned_data.get('departement')

        elif self.departement and not materiel.departement_id:

            materiel.departement = self.departement

        

        # Utiliser le nom du champ personnalisé

        materiel.nom = self.cleaned_data.get('nom_materiel', '')

        

        # Assigner la catégorie si fournie

        if 'categorie' in self.cleaned_data:

            materiel.categorie = self.cleaned_data.get('categorie')

            if materiel.categorie and (not materiel.departement_id or materiel.departement_id != materiel.categorie.departement_id):

                materiel.departement = materiel.categorie.departement

        

        # Assigner la location si fournie (le champ personnalisé location)

        if 'location' in self.cleaned_data:

            location_value = self.cleaned_data.get('location', '').strip()

            materiel.location = location_value if location_value else None

            # #region agent log

            with open(r's:\Brice\RadGestMat\.cursor\debug.log', 'a', encoding='utf-8') as f:

                f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"D","location":"assets/forms.py:141","message":"Location assigned","data":{"location_value":location_value,"materiel_location":getattr(materiel,'location',None)},"timestamp":int(time.time()*1000)}) + '\n')

            # #endregion

        

        if commit:

            materiel.save()

        return materiel



class CategorieForm(forms.ModelForm):

    class Meta:

        model = Categorie

        fields = ['nom', 'description', 'departement']

        widgets = {

            'nom': forms.TextInput(attrs={'class': 'form-control', 'required': True}),

            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),

            'departement': forms.Select(attrs={'class': 'form-select'}),

        }

        labels = {

            'nom': 'Nom *',

            'description': 'Description',

            'departement': 'Département *',

        }

    

    def __init__(self, *args, **kwargs):

        self.user = kwargs.pop('user', None)

        super().__init__(*args, **kwargs)

        

        # Filtrer les départements selon les permissions

        profil = getattr(self.user, 'profilutilisateur', None) if self.user else None

        if profil and profil.role == 'SUPER_ADMIN':

            # SUPER_ADMIN peut voir tous les départements

            self.fields['departement'].queryset = Departement.objects.all()

        elif profil and profil.departement:

            # Autres utilisateurs voient uniquement leur département

            self.fields['departement'].queryset = Departement.objects.filter(id=profil.departement.id)

            # Préremplir le département

            if not self.instance.pk:

                self.fields['departement'].initial = profil.departement

        else:

            # Par défaut, tous les départements (pour les superusers Django)

            self.fields['departement'].queryset = Departement.objects.all()



class ClientForm(forms.ModelForm):

    date_creation = forms.DateTimeField(label='Date création', required=False, disabled=True, widget=forms.DateTimeInput(attrs={'class': 'form-control'}))

    date_modification = forms.DateTimeField(label='Date modification', required=False, disabled=True, widget=forms.DateTimeInput(attrs={'class': 'form-control'}))

    

    # Exposer la sélection de salle. Par défaut optionnelle; validation ci-dessous la rendra

    # obligatoire pour les clients externes.

    salle = forms.ModelChoiceField(

        queryset=Salle.objects.all(),

        required=False,

        widget=forms.Select(attrs={'class': 'form-select'}),

        label='Salle (pour client externe)'

    )



    class Meta:

        model = Client

        fields = ['nom', 'type_client', 'email', 'telephone', 'numero_chambre', 'date_arrivee', 'date_depart', 'nom_evenement', 'departement', 'salle', 'notes']

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

            # Préremplir le champ salle si existant

            if hasattr(self.instance, 'salle') and self.instance.salle:

                self.fields['salle'].initial = self.instance.salle



    def clean(self):

        cleaned = super().clean()

        type_client = cleaned.get('type_client')

        salle = cleaned.get('salle')

        nom_evenement = cleaned.get('nom_evenement')

        numero_chambre = cleaned.get('numero_chambre')

        date_arrivee = cleaned.get('date_arrivee')

        departement = cleaned.get('departement')



        # Pour un client externe (CONFERENCE), le nom événement est requis, mais la salle est optionnelle

        if type_client == Client.TYPE_CONFERENCE:

            if not nom_evenement:

                self.add_error('nom_evenement', "Le nom de l'événement est requis.")

        

        # Pour Hébergement : chambre et date arrivée requises

        if type_client == Client.TYPE_HEBERGEMENT:

            if not numero_chambre:

                self.add_error('numero_chambre', 'Le numéro de chambre est requis.')

            if not date_arrivee:

                self.add_error('date_arrivee', "La date d'arrivée est requise.")



        # Pour Interne : département requis

        if type_client == Client.TYPE_INTERNE and not departement:

            self.add_error('departement', 'Le département est requis pour un client interne.')



        return cleaned



class QuickClientForm(forms.ModelForm):

    """Formulaire pour créer rapidement un client lors du check-out"""
    salle = forms.ModelChoiceField(
        queryset=Salle.objects.all(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Salle (pour client externe)'
    )

    class Meta:

        model = Client

        fields = ['nom', 'type_client', 'email', 'telephone', 'numero_chambre', 'date_arrivee', 'date_depart',
                  'nom_evenement', 'departement', 'salle', 'notes']

        widgets = {

            'nom': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nom du client', 'required': True}),

            'type_client': forms.Select(attrs={'class': 'form-select', 'required': True, 'id': 'quick_type_client'}),

            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email'}),

            'telephone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Téléphone'}),
            'numero_chambre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: 42, 305, etc.'}),
            'date_arrivee': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'date_depart': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'nom_evenement': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Conférence 2025'}),
            'departement': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),

        }

        labels = {

            'nom': 'Nom *',

            'type_client': 'Type client *',

            'email': 'Email',

            'telephone': 'Téléphone',
            'numero_chambre': 'Numéro chambre',
            'date_arrivee': "Date arrivée",
            'date_depart': 'Date départ',
            'nom_evenement': 'Nom événement',
            'departement': 'Département',
            'notes': 'Notes',

        }

    def clean(self):
        cleaned = super().clean()
        type_client = cleaned.get('type_client')
        salle = cleaned.get('salle')
        nom_evenement = cleaned.get('nom_evenement')
        numero_chambre = cleaned.get('numero_chambre')
        date_arrivee = cleaned.get('date_arrivee')
        departement = cleaned.get('departement')

        if type_client == Client.TYPE_CONFERENCE:
            if not nom_evenement:
                self.add_error('nom_evenement', "Le nom de l'événement est requis.")

        if type_client == Client.TYPE_HEBERGEMENT:
            if not numero_chambre:
                self.add_error('numero_chambre', 'Le numéro de chambre est requis.')
            if not date_arrivee:
                self.add_error('date_arrivee', "La date d'arrivée est requise.")

        if type_client == Client.TYPE_INTERNE and not departement:
            self.add_error('departement', 'Le département est requis pour un client interne.')

        return cleaned





class AttributionForm(forms.ModelForm):
    DEST_CHOICES = [

        ('client', 'Client'),

        ('salle', 'Salle de conférence'),

    ]



    # Permettre de choisir la destination (client ou salle)
    destination_type = forms.ChoiceField(choices=DEST_CHOICES, widget=forms.RadioSelect, initial='client', required=False)
    salle = forms.ModelChoiceField(queryset=Salle.objects.all(), required=False, widget=forms.Select(attrs={'class': 'form-select'}))
    type_attribution = forms.ChoiceField(
        choices=Attribution.TYPE_ATTRIBUTION_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label="Type d'attribution"
    )

    class Meta:
        model = Attribution
        fields = ['materiel', 'client', 'salle', 'type_attribution', 'date_retour_prevue', 'notes']
        widgets = {
            'materiel': forms.HiddenInput(),
            'client': forms.Select(attrs={'class': 'form-select', 'id': 'client_select'}),
            'date_retour_prevue': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }



    def clean(self):

        cleaned = super().clean()

        dest = cleaned.get('destination_type')
        client = cleaned.get('client')
        salle = cleaned.get('salle')
        type_attribution = cleaned.get('type_attribution') or Attribution.TYPE_TEMPORAIRE
        if not dest:
            dest = 'salle' if salle else 'client'
            cleaned['destination_type'] = dest
        if dest == 'client' and not client and self.instance and self.instance.pk and self.instance.client:
            cleaned['client'] = self.instance.client
            client = self.instance.client
        if dest == 'salle' and not salle and self.instance and self.instance.pk and self.instance.salle:
            cleaned['salle'] = self.instance.salle
            salle = self.instance.salle

        if dest == 'client' and not client:
            raise forms.ValidationError({'client': 'Veuillez sélectionner un client ou en créer un.'})
        if dest == 'salle' and not salle:
            raise forms.ValidationError({'salle': 'Veuillez sélectionner une salle de conférence.'})
        if type_attribution == Attribution.TYPE_INDEFINIE:
            if dest != 'client':
                raise forms.ValidationError({'destination_type': "L'attribution indéfinie est réservée aux clients internes."})
            if client and client.type_client != Client.TYPE_INTERNE:
                raise forms.ValidationError({'client': "L'attribution indéfinie est réservée aux clients internes."})

        # Validate that the planned return date is not before the attribution date
        date_retour_prevue = cleaned.get('date_retour_prevue')
        if type_attribution == Attribution.TYPE_TEMPORAIRE and not date_retour_prevue:
            raise forms.ValidationError({'date_retour_prevue': "La date de retour prévue est requise pour une attribution temporaire."})
        if type_attribution != Attribution.TYPE_TEMPORAIRE:
            cleaned['date_retour_prevue'] = None

        if date_retour_prevue:
            from django.utils import timezone
            # If editing an existing attribution, use its date_attribution; otherwise use today
            if self.instance and self.instance.pk and getattr(self.instance, 'date_attribution', None):
                base_date = self.instance.date_attribution

                try:

                    if hasattr(base_date, 'date'):

                        base_date = base_date.date()

                except Exception:

                    pass

            else:

                base_date = timezone.now().date()



            if date_retour_prevue < base_date:

                raise forms.ValidationError({'date_retour_prevue': "La date de retour prévue ne peut pas être antérieure à la date d'attribution."})



        return cleaned





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



    def __init__(self, *args, **kwargs):

        # Accept optional 'attribution' kwarg to validate return date consistency

        self.attribution = kwargs.pop('attribution', None)

        super().__init__(*args, **kwargs)



    def clean(self):

        cleaned = super().clean()

        date_retour_effective = cleaned.get('date_retour_effective')

        from django.utils import timezone



        # Default to today if not provided

        if not date_retour_effective:

            date_retour_effective = timezone.now().date()

            cleaned['date_retour_effective'] = date_retour_effective



        # If an attribution was provided, ensure return date is not before attribution date

        if self.attribution and getattr(self.attribution, 'date_attribution', None):

            base_date = self.attribution.date_attribution

            try:

                if hasattr(base_date, 'date'):

                    base_date = base_date.date()

            except Exception:

                pass

            if date_retour_effective < base_date:

                raise forms.ValidationError({'date_retour_effective': "La date de retour ne peut pas être antérieure à la date d'attribution."})



        return cleaned
