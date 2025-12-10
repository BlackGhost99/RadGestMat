"""Admin-like UI URL shim for backwards compatibility.

The project references `assets.urls_admin_ui` from the root URLconf.
This module simply forwards to `assets.urls` under the `admin-ui/` prefix
so the include() in `radgestmat.urls` resolves without changing behavior.
"""
from django.urls import include, path

urlpatterns = [
    path('', include('assets.urls')),
]
