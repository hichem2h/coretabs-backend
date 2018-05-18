import re
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth import get_user_model

from .utils import sync_sso

from rest_framework import serializers
from rest_auth.registration.serializers import RegisterSerializer as RS
from rest_auth.serializers import PasswordResetSerializer as PRS
from allauth.account.forms import ResetPasswordForm

from allauth.account.utils import send_email_confirmation


class RegisterSerializer(RS):
    name = serializers.CharField(
        max_length=100,
        min_length=5,
        required=True
    )

    def validate_name(self, name):
        pattern = "^[a-zA-ZàáâäãåąčćęèéêëėįìíîïłńòóôöõøùúûüųūÿýżźñçčšžÀÁÂÄÃÅĄĆČĖĘÈÉÊËÌÍÎÏĮŁŃÒÓÔÖÕØÙÚÛÜŲŪŸÝŻŹÑßÇŒÆČŠŽ∂ðء-ي]+ [a-zA-ZàáâäãåąčćęèéêëėįìíîïłńòóôöõøùúûüųūÿýżźñçčšžÀÁÂÄÃÅĄĆČĖĘÈÉÊËÌÍÎÏĮŁŃÒÓÔÖÕØÙÚÛÜŲŪŸÝŻŹÑßÇŒÆČŠŽ∂ðء-ي]+[a-zA-ZàáâäãåąčćęèéêëėįìíîïłńòóôöõøùúûüųūÿýżźñçčšžÀÁÂÄÃÅĄĆČĖĘÈÉÊËÌÍÎÏĮŁŃÒÓÔÖÕØÙÚÛÜŲŪŸÝŻŹÑßÇŒÆČŠŽ∂ðء-ي ]*$"
        compiler = re.compile(pattern)
        if not compiler.match(name):
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

    def custom_signup(self, request, user):
        sync_sso(user)


UserModel = get_user_model()


class UserDetailsSerializer(serializers.ModelSerializer):

    class Meta:
        model = UserModel
        fields = ('username', 'email', 'first_name')
        read_only_fields = ('email', )

    def validate_first_name(self, first_name):
        pattern = "^[a-zA-ZàáâäãåąčćęèéêëėįìíîïłńòóôöõøùúûüųūÿýżźñçčšžÀÁÂÄÃÅĄĆČĖĘÈÉÊËÌÍÎÏĮŁŃÒÓÔÖÕØÙÚÛÜŲŪŸÝŻŹÑßÇŒÆČŠŽ∂ðء-ي]+ [a-zA-ZàáâäãåąčćęèéêëėįìíîïłńòóôöõøùúûüųūÿýżźñçčšžÀÁÂÄÃÅĄĆČĖĘÈÉÊËÌÍÎÏĮŁŃÒÓÔÖÕØÙÚÛÜŲŪŸÝŻŹÑßÇŒÆČŠŽ∂ðء-ي]+[a-zA-ZàáâäãåąčćęèéêëėįìíîïłńòóôöõøùúûüųūÿýżźñçčšžÀÁÂÄÃÅĄĆČĖĘÈÉÊËÌÍÎÏĮŁŃÒÓÔÖÕØÙÚÛÜŲŪŸÝŻŹÑßÇŒÆČŠŽ∂ðء-ي ]*$"
        compiler = re.compile(pattern)
        if not compiler.match(first_name):
            raise serializers.ValidationError(
                _("Make sure that you passed your Full Name and that it contains only letters."))

        return first_name


class PasswordResetSerializer(PRS):
    password_reset_form_class = ResetPasswordForm

    def save(self):
        request = self.context.get('request')
        self.reset_form.save(request)

    def validate_email(self, email):
        return email

    def validate(self, attrs):
        # Create PasswordResetForm with the serializer
        self.reset_form = self.password_reset_form_class(data=self.initial_data)
        if not self.reset_form.is_valid():
            raise serializers.ValidationError(self.reset_form.errors)

        return attrs


class ResendConfirmSerializer(serializers.Serializer):
    email = serializers.EmailField()

    password_reset_form_class = ResetPasswordForm

    def validate(self, attrs):
        self.reset_form = self.password_reset_form_class(data=self.initial_data)
        if not self.reset_form.is_valid():
            raise serializers.ValidationError(self.reset_form.errors)

        return attrs

    def save(self):
        request = self.context.get('request')
        User = get_user_model()
        email = self.reset_form.cleaned_data["email"]
        user = User.objects.get(email=email)
        send_email_confirmation(request, user, True)
        return email


from allauth.account.forms import UserTokenForm
from allauth.account.adapter import get_adapter


class PasswordResetConfirmSerializer(serializers.Serializer):
    new_password1 = serializers.CharField(max_length=128)
    new_password2 = serializers.CharField(max_length=128)
    uid = serializers.CharField()
    key = serializers.CharField()

    def validate_new_password1(self, password):
        return get_adapter().clean_password(password)

    def validate(self, attrs):
        self.user_token_form = UserTokenForm(data={'uidb36': attrs['uid'], 'key': attrs['key']})

        if not self.user_token_form.is_valid():
            raise serializers.ValidationError(_("Invalid Token"))

        if attrs['new_password1'] != attrs['new_password2']:
            raise serializers.ValidationError(_("The two password fields didn't match."))

        self.password = attrs['new_password1']

        return attrs

    def save(self):
        user = self.user_token_form.reset_user
        get_adapter().set_password(user, self.password)
        return user


from allauth.utils import email_address_exists
from allauth.account.models import EmailAddress


class ChangeEmailSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)

    def validate_email(self, email):
        email = get_adapter().clean_email(email)
        if email and email_address_exists(email):
            raise serializers.ValidationError(_("A user is already registered with this e-mail address."))
        return email

    def save(self, request):
        user = request.user
        adapter = get_adapter()
        adapter.send_mail('account/email/email_change', user.email, {})

        email = EmailAddress.objects.get(user=user, verified=True)
        email.change(request, self.validated_data['email'], True)
        return user
