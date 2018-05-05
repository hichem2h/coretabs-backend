import base64
import hmac
import hashlib
from urllib import parse

import requests
import os


def sync_sso(user):
    params = {
        'email': user.email,
        'external_id': user.id,
        'username': user.username,
        'name': user.first_name
    }

    key = bytes(os.environ.get('DISCOURSE_SSO_SECRET'), encoding='utf-8')
    return_payload = base64.b64encode(bytes(parse.urlencode(params), 'utf-8'))
    h = hmac.new(key, return_payload, digestmod=hashlib.sha256)
    query_string = parse.urlencode({'sso': return_payload, 'sig': h.hexdigest()})

    data = {"api_key": os.environ.get('DISCOURSE_API_KEY'),
            "api_username": os.environ.get('DISCOURSE_API_USERNAME')}

    url = '{}/admin/users/sync_sso/?{}'.format(os.environ.get('DISCOURSE_HOST'), query_string)

    r = requests.post(url, data=data)