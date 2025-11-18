# radgestmat/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from users.views import logout_view

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # API routes (uncomment when rest_framework is installed)
    # path('api/v1/', include('assets.api.urls')),
    
    # Application routes
    path('', include('assets.urls')),
    path('users/', include('users.urls')),
    
    # Authentification
    path('login/', auth_views.LoginView.as_view(template_name='users/login.html'), name='login'),
    path('logout/', logout_view, name='logout'),
]

# Admin customization
admin.site.site_header = "RadGestMat Administration"
admin.site.site_title = "RadGestMat Admin"
admin.site.index_title = "Gestion de Matériel"

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
