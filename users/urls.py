from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
    path('', views.index, name='index'),
    path('utilisateurs/', views.user_list, name='user_list'),
    path('utilisateurs/<int:pk>/', views.user_detail, name='user_detail'),
    path('utilisateurs/creer/', views.user_create, name='user_create'),
    path('utilisateurs/<int:pk>/modifier/', views.user_update, name='user_update'),
    path('utilisateurs/<int:pk>/supprimer/', views.user_delete, name='user_delete'),
    path('settings/', views.user_settings, name='user_settings'),
    path('api/toggle-theme/', views.toggle_dark_mode, name='toggle_dark_mode'),
]
