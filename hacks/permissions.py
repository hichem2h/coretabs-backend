from rest_framework import permissions


class SecretKeyPermission(permissions.BasePermission):
    message = 'Bad API Key'

    def has_permission(self, request, view):
        permit = False
        secret = request.META.get('HTTP_API_KEY', '')

        if secret == '1234':
            permit = True

        return permit