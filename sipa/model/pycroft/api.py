import logging

from dataclasses import dataclass
from datetime import date
from functools import partial
from typing import Tuple, Any, Optional
from collections.abc import Callable

import requests
from requests import ConnectionError, HTTPError

from sipa.backends.exceptions import InvalidConfiguration
from .exc import PycroftBackendError

from sipa.utils import dataclass_from_dict

logger = logging.getLogger(__name__)


class PycroftApiError(RuntimeError):
    def __init__(self, code: str, message: str, *a, **kw):
        self.code = code
        self.message = message
        super().__init__(*a, **kw)


@dataclass
class MatchPersonResult:
    begin: date
    end: date
    room_id: int
    building: str
    room: str

    def __post_init__(self):
        if isinstance(self.begin, str):
            self.begin = date.fromisoformat(self.begin)
        if isinstance(self.end, str):
            self.end = date.fromisoformat(self.end)

    @classmethod
    def from_json(cls, json: dict):
        return dataclass_from_dict(MatchPersonResult, json)


class PycroftApi():
    def __init__(self, endpoint: str, api_key: str):
        if not endpoint.endswith("/"):
            raise InvalidConfiguration("API endpoint must end with a '/'")
        self._endpoint = endpoint
        self._api_key = api_key

    def get_user(self, username: str) -> tuple[int, dict]:
        return self.get(f'user/{username}')

    def get_user_from_ip(self, ip):
        return self.get('user/from-ip', params={'ip': ip}, no_raise=True)

    def authenticate(self, username, password):
        return self.post('user/authenticate',
                         data={'login': username, 'password': password})

    def change_password(self, user_id, old_password, new_password):
        return self.post(f'user/{user_id}/change-password',
                         data={'password': old_password,
                               'new_password': new_password})

    def change_mail(self, user_id, password, new_mail, forwarded):
        return self.post(f'user/{user_id}/change-email',
                         data={'password': password, 'new_email': new_mail, 'forwarded': forwarded})

    def change_mac(self, user_id, password, interface_id, new_mac, host_name):
        return self.post(f'user/{user_id}/change-mac/{interface_id}',
                         data={'password': password, 'mac': new_mac, 'host_name': host_name})

    def activate_network_access(self, user_id, password, mac, birthdate, host_name):
        return self.post(f'user/{user_id}/activate-network-access',
                         data={'password': password, 'mac': mac,
                               'birthdate': birthdate, 'host_name': host_name})

    def estimate_balance_at_end_of_membership(self, user_id, end_date):
        return self.get(f"user/{user_id}/terminate-membership",
                        params={'end_date': end_date})

    def terminate_membership(self, user_id, end_date):
        return self.post(f"user/{user_id}/terminate-membership",
                         data={'end_date': end_date,
                               'comment': 'Move-out by SIPA'})

    def continue_membership(self, user_id):
        return self.delete(f"user/{user_id}/terminate-membership")

    def reset_wifi_password(self, user_id):
        return self.patch(f"user/{user_id}/reset-wifi-password")

    def request_password_reset(self, user_ident: str, email: str):
        return self.post("user/reset-password", data={
            'ident': user_ident,
            'email': email,
        })

    def reset_password(self, token, new_password):
        return self.patch("user/reset-password", data={
            'token':  token,
            'password': new_password,
        })

    def match_person(self, first_name: str, last_name: str, birthdate: date, tenant_number: int,
                     previous_dorm: str | None) -> MatchPersonResult:
        """
        Get the newest tenancy for the supplied user data.

        :raises PycroftApiError: if the matching was unsuccessful
        :return: the match result
        """
        # if first_name == 's':
        #     status, result = 200, {
        #         'building': 'Zw 41',
        #         'room': 'Room 407',
        #         'room_id': 1337,
        #         'begin': '2020-10-01',
        #         'end': '2021-10-01',
        #     }
        # else:
        #     status, result = 404, {
        #         'code': 'user_exists',
        #         'message': 'No tenancies found for this data',
        #     }

        params = {'first_name': first_name, 'last_name': last_name,
                  'birthdate': birthdate, 'person_id': tenant_number}

        if previous_dorm is not None:
            params['previous_dorm'] = previous_dorm

        status, result = self.get("register", params)

        if status != 200:
            raise PycroftApiError(result['code'], result['message'])

        return MatchPersonResult.from_json(result)

    def member_request(self, email: str, login: str, password: str,
                       first_name: str, last_name: str, birthdate: date,
                       move_in_date: date, tenant_number: int | None,
                       room_id: int | None, previous_dorm: str | None) -> None:
        """
        Creates a member request in pycroft.

        :raises PycroftApiError: if the member request was unsuccessful
        """
        # if login == 's':
        #     status, result = 200, None
        # else:
        #     status, result = 404, {
        #         'code': 'user_exists',
        #         'message': 'User already exists',
        #     }

        data = {
            'first_name': first_name, 'last_name': last_name, 'birthdate': birthdate,
            'email': email, 'login': login, 'password': password,
            'move_in_date': move_in_date.isoformat()
        }

        # Verification was not skipped
        if tenant_number is not None:
            data['person_id'] = tenant_number

        # Room was not rejected
        if room_id is not None:
            data['room_id'] = room_id

        if previous_dorm is not None:
            data['previous_dorm'] = previous_dorm

        status, result = self.post("register", data=data)

        if status != 200:
            raise PycroftApiError(result['code'], result['message'])
        else:
            return

    def resend_confirm_email(self, user_id: int) -> bool:
        status, _ = self.get("register/confirm", params={'user_id': user_id})
        return status == 200

    def confirm_email(self, token: str):
        """
        Confirms a member request.

        :raises PycroftApiError: if the confirmation was unsuccessful
        :return: the confirmation type, either `user` or `pre_member`
        """

        # if token == 's':
        #     status, result = 200, None
        # else:
        #     status, result = 404, {
        #         'code': 'bad_key',
        #         'message': 'Bad key',
        #     }

        status, result = self.post("register/confirm", data={'key': token})

        if status != 200:
            raise PycroftApiError(result['code'], result['message'])

        return result

    def get(self, url, params=None, no_raise=False):
        request_function = partial(requests.get, params=params or {})
        return self._do_api_call(request_function, url)

    def post(self, url, data=None, no_raise=False):
        request_function = partial(requests.post, data=data or {})
        return self._do_api_call(request_function, url)

    def delete(self, url, data=None, no_raise=False):
        request_function = partial(requests.delete, data=data or {})
        return self._do_api_call(request_function, url)

    def patch(self, url, data=None, no_raise=False):
        request_function = partial(requests.patch, data=data or {})
        return self._do_api_call(request_function, url)

    def _do_api_call(self, request_function: Callable, url: str, no_raise: bool = False) -> tuple[int, Any]:
        try:
            response = request_function(
                self._endpoint + url,
                headers={'Authorization': f'ApiKey {self._api_key}'},
            )
        except ConnectionError as e:
            if no_raise:
                return 0, None

            logger.error("Caught a ConnectionError when accessing Pycroft API",
                         extra={'data': {'endpoint': self._endpoint + url}})
            raise PycroftBackendError("Pycroft API unreachable") from e

        if response.status_code not in [200, 400, 401, 403, 404, 412, 422] and not no_raise:
            try:
                response.raise_for_status()
            except HTTPError as e:
                raise PycroftBackendError(f"Pycroft API returned status"
                                          f" {response.status_code}") from e

        return response.status_code, response.json()
