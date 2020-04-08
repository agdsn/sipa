import logging

from functools import partial
from typing import Callable, Tuple, Any

import requests
from requests import ConnectionError, HTTPError

from sipa.backends.exceptions import InvalidConfiguration
from .exc import PycroftBackendError

logger = logging.getLogger(__name__)


class PycroftApi():
    def __init__(self, endpoint: str, api_key: str):
        if not endpoint.endswith("/"):
            raise InvalidConfiguration("API endpoint must end with a '/'")
        self._endpoint = endpoint
        self._api_key = api_key

    def get_user(self, username: str) -> Tuple[int, dict]:
        return self.get('user/{}'.format(username))

    def get_user_from_ip(self, ip):
        return self.get('user/from-ip', params={'ip': ip})

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

    def change_mac(self, user_id, password, interface_id, new_mac, host_name):
        return self.post('user/{}/change-mac/{}'.format(user_id, interface_id),
                         data={'password': password, 'mac': new_mac, 'host_name': host_name})

    def activate_network_access(self, user_id, password, mac, birthdate, host_name):
        return self.post('user/{}/activate-network-access'.format(user_id),
                         data={'password': password, 'mac': mac,
                               'birthdate': birthdate, 'host_name': host_name})

    def estimate_balance_at_end_of_membership(self, user_id, end_date):
        return self.get("user/{}/terminate-membership".format(user_id),
                        params={'end_date': end_date})

    def terminate_membership(self, user_id, end_date):
        return self.post("user/{}/terminate-membership".format(user_id),
                         data={'end_date': end_date,
                               'comment': 'Move-out by SIPA'})

    def continue_membership(self, user_id):
        return self.delete("user/{}/terminate-membership".format(user_id))

    def reset_wifi_password(self, user_id):
        return self.patch("user/{}/reset-wifi-password".format(user_id))

    def get(self, url, params=None):
        request_function = partial(requests.get, params=params or {})
        return self._do_api_call(request_function, url)

    def post(self, url, data=None):
        request_function = partial(requests.post, data=data or {})
        return self._do_api_call(request_function, url)

    def delete(self, url, data=None):
        request_function = partial(requests.delete, data=data or {})
        return self._do_api_call(request_function, url)

    def patch(self, url, data=None):
        request_function = partial(requests.patch, data=data or {})
        return self._do_api_call(request_function, url)

    def _do_api_call(self, request_function: Callable, url: str) -> Tuple[int, Any]:
        try:
            response = request_function(
                self._endpoint + url,
                headers={'Authorization': 'ApiKey {}'.format(self._api_key)},
            )
        except ConnectionError as e:
            logger.error("Caught a ConnectionError when accessing Pycroft API",
                         extra={'data': {'endpoint': self._endpoint + url}})
            raise PycroftBackendError("Pycroft API unreachable") from e

        if response.status_code not in [200, 400, 401, 403, 404, 412]:
            try:
                response.raise_for_status()
            except HTTPError as e:
                raise PycroftBackendError(f"Pycroft API returned status"
                                          f" {response.status_code}") from e

        return response.status_code, response.json()
