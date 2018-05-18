import os, requests

from allauth.account.views import PasswordResetFromKeyView as PRV
from django.urls import reverse_lazy

from .utils import sync_sso

from rest_auth.views import LogoutView as LV
from rest_auth.views import UserDetailsView as UDV
from rest_framework import status
from rest_framework.response import Response
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth import logout as django_logout
from django.utils.translation import ugettext_lazy as _
from django.views.decorators.debug import sensitive_post_parameters


from .serializers import ResendConfirmSerializer, ChangeEmailSerializer
from rest_framework.generics import GenericAPIView


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


class UserDetailsView(UDV):
    def put(self, request, *args, **kwargs):
        response = self.update(request, *args, **kwargs)
        sync_sso(request.user)
        return response


user_details_view = UserDetailsView.as_view()


class ResendConfirmView(GenericAPIView):
    """
    Calls Django Auth PasswordResetForm save method.

    Accepts the following POST parameters: email
    Returns the success/fail message.
    """
    serializer_class = ResendConfirmSerializer

    def post(self, request, *args, **kwargs):
        # Create a serializer with request.data
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        serializer.save()
        # Return the success message with OK HTTP status
        return Response(
            {"detail": _("Confirmation e-mail has been sent.")},
            status=status.HTTP_200_OK
        )


resend_confirmation_view = ResendConfirmView.as_view()


class ChangeEmailView(GenericAPIView):

    serializer_class = ChangeEmailSerializer

    def post(self, request, *args, **kwargs):
        # Create a serializer with request.data
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        serializer.save(request)
        # Return the success message with OK HTTP status
        return Response(
            {"detail": _("Verification e-mail sent.")},
            status=status.HTTP_200_OK
        )


change_email_view = ChangeEmailView.as_view()