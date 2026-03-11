# radgestmat/urls.py
import sys
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.contrib.auth import views as auth_views
from users.views import logout_view
from radgestmat.admin_debug_views import custom_app_index

# Override app_index for assets app to add debugging
admin.site.app_index = custom_app_index

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # API routes (uncomment when rest_framework is installed)
    # path('api/v1/', include('assets.api.urls')),
    
    # Application routes
    path('', include('assets.urls')),
    # Admin-like application UI (parity with Django admin)
    # Note: urls_admin_ui doesn't use namespace to avoid duplicate 'assets' namespace warning
    path('admin-ui/', include('assets.urls_admin_ui')),
    path('users/', include('users.urls')),
    
    # Authentification
    path('login/', auth_views.LoginView.as_view(template_name='users/login.html'), name='login'),
    path('logout/', logout_view, name='logout'),
]

# Admin customization
admin.site.site_header = "RadGestMat Administration"
admin.site.site_title = "RadGestMat Admin"
admin.site.index_title = "Gestion de Matériel"

# Serve static and media files in development
# Always serve static files (even if DEBUG=False in some configs for local development)
# This ensures static files work during development regardless of DEBUG setting
# #region agent log
import json, time
try:
    with open(r's:\Brice\RadGestMat\.cursor\debug.log', 'a', encoding='utf-8') as f:
        f.write(json.dumps({"sessionId":"debug-session","runId":"run2","hypothesisId":"F","location":"radgestmat/urls.py:38","message":"Static files config check","data":{"DEBUG":settings.DEBUG,"STATIC_URL":settings.STATIC_URL,"has_staticfiles_dir":hasattr(settings,'STATICFILES_DIRS')},"timestamp":int(time.time()*1000)}) + '\n')
except:
    pass
# #endregion

# Always serve static files in development - force enable regardless of DEBUG
# This is safe because this code only runs during development (runserver)
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
urlpatterns += staticfiles_urlpatterns()

# #region agent log
try:
    with open(r's:\Brice\RadGestMat\.cursor\debug.log', 'a', encoding='utf-8') as f:
        f.write(json.dumps({"sessionId":"debug-session","runId":"run2","hypothesisId":"F","location":"radgestmat/urls.py:50","message":"Static files URLs added","data":{"urlpatterns_count":len(urlpatterns)},"timestamp":int(time.time()*1000)}) + '\n')
except:
    pass
# #endregion
