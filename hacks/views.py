from allauth.account.views import PasswordResetFromKeyView as PRV
from django.urls import reverse_lazy

import os, requests
from rest_auth.views import LogoutView as LV
from rest_framework import status
from rest_framework.response import Response
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth import logout as django_logout
from django.utils.translation import ugettext_lazy as _


class PasswordResetFromKeyView(PRV):
    success_url = reverse_lazy("home")


password_reset_from_key = PasswordResetFromKeyView.as_view()


class LogoutView(LV):
    def logout(self, request):
        try:
            request.user.auth_token.delete()
        except (AttributeError, ObjectDoesNotExist):
            pass
        if request.user.id:
            self.discourse_logout(request)

        django_logout(request)

        return Response({"detail": _("Successfully logged out.")},
                        status=status.HTTP_200_OK)

    def discourse_logout(self, request):
        data = {"api_key": os.environ.get('DISCOURSE_API_KEY'),
                     "api_username": os.environ.get('DISCOURSE_API_USERNAME')}

        user = requests.get( os.environ.get('DISCOURSE_HOST') + '/users/by-external/{}.json'.format(request.user.id), data=data)

        user = user.json()
        user_id = user['user']['id']

        url = os.environ.get('DISCOURSE_HOST') + '/admin/users/{}/log_out/'.format(user_id)

        r = requests.post(url, data=data)


logout_view = LogoutView.as_view()