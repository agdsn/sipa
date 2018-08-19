import logging

from functools import partial
import requests

logger = logging.getLogger(__name__)


class PycroftApi():
    def __init__(self, endpoint, api_key):
        self._endpoint = endpoint
        self._api_key = api_key

    def get_user(self, username):
        return self.get('user/{}'.format(username))

    def get_user_from_ip(self, ip):
        return self.get('/user/from-ip', params={'ip': ip})

    def authenticate(self, username, password):
        return self.post('user/authenticate',
                         data={'login': username, 'password': password})

    def change_password(self, user_id, old_password, new_password):
        return self.post('user/{}/change-password'.format(user_id),
                         data={'password': old_password,
                               'new_password': new_password})

    def change_mail(self, user_id, password, new_mail):
        return self.post('user/{}/change-email'.format(user_id),
                         data={'password': password, 'new_email': new_mail})

    def change_cache_usage(self, user_id, use_cache):
        return self.post('user/{}/change-cache-usage'.format(user_id),
                         data={'use_cache': use_cache})

    def get(self, url, params=None):
        request_function = partial(requests.get, params=params or {})
        return self._do_api_call(request_function, url)

    def post(self, url, data=None):
        request_function = partial(requests.post, data=data or {})
        return self._do_api_call(request_function, url)

    def _do_api_call(self, request_function, url):
        try:
            response = request_function(
                self._endpoint + url,
                verify=False,
                headers={'Authorization': 'ApiKey {}'.format(self._api_key)},
            )
        except ConnectionError as e:
            logger.error("Caught a ConnectionError when accessing Pycroft API",
                         extra={'data': {'endpoint': self._endpoint + url}})
            raise ConnectionError("Pycroft API unreachable") from e

        if response.status_code not in [200, 400, 401, 403, 404]:
            response.raise_for_status()

        return response.status_code, response.json()
