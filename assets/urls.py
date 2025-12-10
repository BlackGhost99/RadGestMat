# assets/urls.py
from django.urls import path
from . import views

app_name = 'assets'

urlpatterns = [
    # Dashboard
    path('', views.dashboard, name='dashboard'),

    # Materiel CRUD
    path('materiel/', views.materiel_list, name='materiel_list'),
    path('materiel/ajouter/', views.materiel_create, name='materiel_create'),
    path('materiel/groupe/<str:nom>/', views.materiel_group_detail, name='materiel_group_detail'),
    path('materiel/<int:pk>/', views.materiel_detail, name='materiel_detail'),
    path('materiel/<int:pk>/modifier/', views.materiel_update, name='materiel_update'),
    path('materiel/<int:pk>/supprimer/', views.materiel_delete, name='materiel_delete'),
    path('api/noms-materiels/', views.api_noms_materiels, name='api_noms_materiels'),
    path('api/creer-nom-materiel/', views.api_creer_nom_materiel, name='api_creer_nom_materiel'),
    path('api/creer-categorie/', views.api_creer_categorie, name='api_creer_categorie'),

    # Scan
    path('scan/', views.scan_qr, name='scan_qr'),
    path('scan/<str:asset_id>/', views.scan_result, name='scan_result'),

    # Check-out / Check-in
    path('materiel/<str:asset_id>/checkout/', views.checkout, name='materiel_checkout'),
    path('materiel/<str:asset_id>/checkin/', views.checkin, name='materiel_checkin'),
    path('checkin/success/', views.checkin_success, name='checkin_success'),

    # Clients CRUD
    path('clients/', views.client_list, name='client_list'),
    path('clients/ajouter/', views.client_create, name='client_create'),
    path('clients/<int:pk>/', views.client_detail, name='client_detail'),
    path('clients/<int:pk>/modifier/', views.client_update, name='client_update'),
    path('clients/<int:pk>/supprimer/', views.client_delete, name='client_delete'),

    # Attributions
    path('attributions/', views.attribution_list, name='attribution_list'),
    path('attributions/<int:pk>/modifier/', views.attribution_update, name='attribution_update'),
    
    # Alertes
    path('alertes/', views.alerte_list, name='alerte_list'),
    path('alertes/<int:pk>/', views.alerte_detail, name='alerte_detail'),
    path('alertes/<int:pk>/regler/', views.alerte_marquer_reglementee, name='alerte_marquer_reglementee'),
    path('alertes/detecter/', views.alerte_detecter, name='alerte_detecter'),
    
    # Notifications (Phase 6)
    path('notifications/dashboard/', views.notifications_dashboard, name='notifications_dashboard'),
    path('notifications/preferences/', views.notification_preferences, name='notification_preferences'),
    
    # Rapports / Audit
    path('rapports/', views.report_list, name='report_list'),
    path('rapports/<int:pk>/', views.report_detail, name='report_detail'),
    path('rapports/<int:pk>/pdf/', views.report_pdf, name='report_pdf'),
]