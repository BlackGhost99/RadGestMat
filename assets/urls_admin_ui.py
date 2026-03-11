"""Admin-like UI URL shim for backwards compatibility.

The project references `assets.urls_admin_ui` from the root URLconf.
This module simply forwards to `assets.urls` under the `admin-ui/` prefix
so the include() in `radgestmat.urls` resolves without changing behavior.

To avoid namespace conflict, we import the urlpatterns directly without
using include() with namespace, which prevents the duplicate 'assets' namespace warning.
"""
from assets.urls import urlpatterns

# No app_name here to avoid namespace conflict
# The URLs will be accessible but reverse() won't use 'assets:' namespace for these
