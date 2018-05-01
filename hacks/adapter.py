from allauth.account.adapter import DefaultAccountAdapter
from allauth.utils import build_absolute_uri
from django.http import HttpResponseRedirect

class MyAccountAdapter(DefaultAccountAdapter):

    def respond_email_verification_sent(self, request, user):
        return HttpResponseRedirect('')