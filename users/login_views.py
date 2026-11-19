"""Login redirects that respect account administration privileges."""
from urllib.parse import unquote, urlsplit

from django.contrib import messages
from django.contrib.auth.views import LoginView
from django.urls import Resolver404, resolve, reverse

from .account_admin import can_administer_accounts


class RadGestMatLoginView(LoginView):
    template_name = 'users/login.html'

    def get_success_url(self):
        destination = super().get_success_url()
        try:
            match = resolve(unquote(urlsplit(destination).path))
        except (Resolver404, ValueError):
            return destination
        if (match.namespace == 'users' and match.url_name in {
            'user_list', 'user_detail', 'user_create', 'user_update',
            'user_delete', 'user_password', 'user_send_reset',
        } and not can_administer_accounts(self.request.user)):
            messages.info(self.request, 'Vous êtes connecté. Cette page est réservée aux administrateurs.')
            return reverse('assets:dashboard')
        return destination
