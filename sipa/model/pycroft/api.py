import logging

from functools import partial
import requests

logger = logging.getLogger(__name__)


class PycroftApi():
    def __init__(self, endpoint, api_key):
        self._endpoint = endpoint
        self._api_key = api_key

    def get_user(self, username):
        return self._do_api_call('user/{}'.format(username))

    def get_user_from_ip(self, ip):
        return self._do_api_call('/user/from-ip', method='get', params={'ip': ip})

    def authenticate(self, username, password):
        return self._do_api_call('user/authenticate', 'post',
                                 data={'login': username, 'password': password})

    def change_password(self, user_id, old_password, new_password):
        return self._do_api_call('user/{}/change-password'.format(user_id), 'post',
                                 data={'password': old_password,
                                       'new_password': new_password})

    def change_mail(self, user_id, password, new_mail):
        return self._do_api_call('user/{}/change-email'.format(user_id), 'post',
                                 data={'password': password, 'new_email': new_mail})

    def change_cache_usage(self, user_id, use_cache):
        return self._do_api_call('user/{}/change-cache-usage'.format(user_id), 'post',
                                 data={'use_cache': use_cache})

    def _do_api_call(self, request, method='get', params=None, data=None):
        """Send a request to the Pycroft api
        """

        if method == 'get':
            request_function = partial(requests.get, params=params)
        elif method == 'post':
            request_function = partial(requests.post, data=data)
        else:
            raise ValueError("`method` must be one of ['get', 'post']!")

        try:
            response = request_function(
                self._endpoint + request,
                verify=False,
                headers={'Authorization': 'ApiKey {}'.format(self._api_key)},
            )
        except ConnectionError as e:
            logger.error("Caught a ConnectionError when accessing Pycroft API",
                         extra={'data': {'endpoint': self._endpoint + request}})
            raise ConnectionError("Pycroft API unreachable") from e

        if response.status_code not in [200, 400, 401, 403, 404]:
            response.raise_for_status()

        return response.status_code, response.json()
