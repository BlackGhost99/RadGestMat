from django.urls import path
from . import views, account_admin

app_name = 'users'

urlpatterns = [
    path('', views.index, name='index'),
    path('utilisateurs/', views.user_list, name='user_list'),
    path('utilisateurs/<int:pk>/', views.user_detail, name='user_detail'),
    path('utilisateurs/creer/', views.user_create, name='user_create'),
    path('utilisateurs/<int:pk>/modifier/', views.user_update, name='user_update'),
    path('utilisateurs/<int:pk>/supprimer/', views.user_delete, name='user_delete'),
    path('utilisateurs/<int:pk>/mot-de-passe/', account_admin.user_password, name='user_password'),
    path('utilisateurs/<int:pk>/envoyer-lien/', account_admin.user_send_reset, name='user_send_reset'),
    path('reinitialisation/<uidb64>/<token>/', account_admin.AccountResetConfirm.as_view(), name='password_reset_confirm'),
    path('reinitialisation-terminee/', account_admin.auth_views.PasswordResetCompleteView.as_view(template_name='users/reset_complete.html'), name='password_reset_complete'),
    path('settings/', views.user_settings, name='user_settings'),
    path('api/toggle-theme/', views.toggle_dark_mode, name='toggle_dark_mode'),
]
