import re
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth import get_user_model

from rest_framework import serializers
from rest_auth.registration.serializers import RegisterSerializer as RS
from rest_auth.serializers import PasswordResetSerializer as PRS
from allauth.account.forms import ResetPasswordForm


class RegisterSerializer(RS):
    name = serializers.CharField(
        max_length=100,
        min_length=5,
        required=True
    )

    def validate_name(self, name):
        pattern = re.compile("^[\w]+ [\w]+[\w ]*")
        if not pattern.match(name):
            raise serializers.ValidationError(
                _("Make sure that you passed your Full Name and that it contains only letters."))
        pattern2 = re.compile("^.*\d.*")
        if pattern2.match(name):
            raise serializers.ValidationError(
                _("Make sure that you passed your Full Name and that it contains only letters."))

        return name

    def get_cleaned_data(self):
        return {
            'username': self.validated_data.get('username', ''),
            'password1': self.validated_data.get('password1', ''),
            'email': self.validated_data.get('email', ''),
            'first_name': self.validated_data.get('name', '')
        }


UserModel = get_user_model()


class UserDetailsSerializer(serializers.ModelSerializer):

    class Meta:
        model = UserModel
        fields = ('username', 'email', 'first_name')
        read_only_fields = ('email', )


class PasswordResetSerializer(PRS):
    password_reset_form_class = ResetPasswordForm

    def save(self):
        request = self.context.get('request')
        self.reset_form.save(request)