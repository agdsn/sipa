import json
from functools import partial
from itertools import chain, product
from unittest.mock import MagicMock, patch
from urllib.parse import parse_qs, urlparse

from flask.ext.login import AnonymousUserMixin
from requests import Response

from sipa.model.gerok.user import (User, do_api_call, date_from_delta,
                                   date_str_from_delta)
from sipa.utils.exceptions import PasswordInvalid, UserNotFound
from tests.prepare import AppInitialized


def mocked_gerok_api(status_code=200, response=b""):
    get = MagicMock()

    get.return_value = Response()
    get().status_code = status_code
    get()._content = response

    return get


class TestGerokApiCall(AppInitialized):
    get = mocked_gerok_api()
    post = mocked_gerok_api()
    url = "supersecret.onion"

    def setUp(self):
        self.set_token("")
        self.app.extensions['gerok_api']['endpoint'] = self.url
        self.get.reset_mock()
        self.post.reset_mock()

    def set_token(self, token):
        self.app.extensions['gerok_api']['token'] = token

    @patch('requests.get', get)
    def test_empty_request(self):
        self.assertEqual(do_api_call(""), "")
        assert self.get.called

    @patch('requests.get', get)
    def test_not_200_ValueError(self):
        # loop over a lot of status codes except 200
        for status in chain(range(0, 200, 20), range(201, 600, 20)):
            self.get.reset_mock()
            self.get().status_code = status

            with self.assertRaises(ValueError):
                do_api_call("")

            assert self.get.called

    @patch('requests.get', get)
    def test_correct_url_called(self):
        do_api_call("")

        # assert that the call only got the positional args `(self.url,)`
        self.assertEqual(self.get.call_args[0], (self.url,))

    @patch('requests.get', get)
    def test_json_parsed(self):
        sample_dicts = [
            {},
            {'foo': 'bar'},
            {'foo': 'bar', 'dict': {'baz': 'shizzle'}, 'int': 2},
        ]
        for d in sample_dicts:
            self.get()._content = json.dumps(d).encode()
            self.assertEqual(do_api_call(""), d)

    @patch('requests.get', get)
    @patch('requests.post', post)
    def test_post_called(self):
        do_api_call("", method='post', postdata=None)
        self.get.assert_not_called()
        self.assertEqual(self.post.called, True)

    @patch('requests.get', get)
    @patch('requests.post', post)
    def test_invalid_method(self):
        for method in ['GET', 'POST', 'nothing_of_both', 'something_else']:
            with self.assertRaises(ValueError):
                do_api_call("", method=method, postdata=None)
            self.get.assert_not_called()
            self.post.assert_not_called()

    @patch('requests.post', post)
    def test_postdata_passed(self):
        postdata = {'foo': "bar"}
        do_api_call("", method='post', postdata=postdata)
        self.assertEqual(self.post.call_args[1]['data'], postdata)

    def assert_token_passed(self, tokens, method):
        for token in tokens:
            self.set_token(token)
            expected_header = {'Authorization': "Token token={}".format(token)}
            do_api_call("", method=method)
            if method == 'get':
                self.assertEqual(self.get.call_args[1]['headers'],
                                 expected_header)
            elif method == 'post':
                self.assertEqual(self.post.call_args[1]['headers'],
                                 expected_header)
            else:
                raise ValueError("`method` must be one of ['get', 'post']!")

    @patch('requests.get', get)
    def test_auth_string_passed_get(self):
        tokens = ["", "foobar123", "dtrndturiaehc",
                  "54TRNEDr:-)/nyUfeg n:s lvℕΓΦ∃Δ∂ℝ⇐⊂6"]
        self.assert_token_passed(tokens, method='get')

    @patch('requests.post', post)
    def test_auth_string_passed_post(self):
        tokens = ["", "foobar123", "dtrndturiaehc",
                  "54TRNEDr:-)/nyUfeg n:s lvℕΓΦ∃Δ∂ℝ⇐⊂6"]
        self.assert_token_passed(tokens, method='post')


def fake_api(users_dict, request, method='get', postdata=None):
    """A fake gerok api, replacing `do_api_call` for testing.

    The API trusts on an empty api_url in the config, so that the
    request string is effectively the desired API path.  This is not
    beautiful, but sufficient for testing purposes.
    """
    parsed = urlparse(request)
    path_components = parsed.path.split('/')
    if path_components[0] == '':
        path_components = path_components[1:]
    action = path_components[0]

    if action == "find":
        query_args = parse_qs(parsed.query, keep_blank_values=True)
        if 'ip' in query_args.keys():
            ip = query_args['ip'][0]
            for user_id, value in users_dict.items():
                if ip in [h['ip'] for h in value['hosts']]:
                    break
            else:
                return
        elif 'login' in query_args.keys():
            login = query_args['login'][0]
            for user_id, value in users_dict.items():
                if value['login'] == login:
                    break
        else:
            raise NotImplementedError
    elif action == "auth":
        for user_id, value in users_dict.items():
            if value['login'] == postdata['login']:
                break
        else:
            return "NoAccount"
        if postdata['pass'] != users_dict[user_id].get('password'):
            return
        # else: password was correct, leave `user_id` as is
    else:
        user_id = action
        if len(path_components) == 2:
            action = path_components[1]
            user = users_dict[user_id]
            if action == 'credit':
                return ([{'credit': user['credit']}]
                        if 'credit' in user.keys()
                        else "")
            elif action == 'traffic':
                traffic_entries = [
                    {
                        'date': date_str_from_delta(entry['relative_date']),
                        'in': entry['in'] * 1024,
                        'out': entry['out'] * 1024,
                        'credit': entry['credit'] * 1024,
                    }
                    for entry in user.get('traffic_entries', [])
                ]

                return [{'traffic': traffic_entries}]
            else:
                raise NotImplementedError

    # Everything else: return user_data for an initialized `user_id`
    try:
        return {
            'id': user_id,
            **users_dict[user_id]
        }
    except KeyError:
        raise ValueError("no user with id {} exists in `self.users`. "
                         "Is the request string '{}' correct?"
                         .format(user_id, request))


def iter_traffic_entries(relative_dates, input, output, credit):
    return [{'relative_date': date, 'credit': credit,
             'in': input, 'out': output}
            for date in relative_dates]


def get_possible_traffic_entry_lists():
    entry_lists = []
    day_masks = [
        [],
        *(list(range(i, 1)) for i in range(-10, 1)),
        *(list(range(-6, i)) for i in range(-5, 0)),
    ]

    for mask in day_masks:
        entry_lists.append(
            iter_traffic_entries(
                relative_dates=mask,
                input=20202,
                output=202020,
                credit=2048,
            )
        )

    return entry_lists


def generate_host(i):
    string_rep = str(i)
    if len(string_rep) > 4:
        raise ValueError("`i` may not have more than 4 digits.")
    string_rep = "{0:0>4}".format(string_rep)  # rfill string_rep with 0s
    return {
        'ip': ".".join(string_rep),
        'mac': "00:{0:0>2x}:00:{1:0>2x}:00:00".format(i % 13, i % 3),
        'hostname': "host{}".format(i),
        'alias': "alias{}".format(i),
    }


def get_possible_users():
    traffic_entries_delegates = get_possible_traffic_entry_lists()
    mail_delegates = ["foo@bar.baz", "", "foobar"]
    credit_delegates = [2048, 0, 1024]

    premature_users = [
        {
            'traffic_entries': x[0],
            'mail': x[1],
            'credit': x[2],
        }
        for x in product(
                traffic_entries_delegates,
                mail_delegates,
                credit_delegates,
        )
    ]

    users = {}
    for i, user in enumerate(premature_users, start=1):
        users[str(i)] = {
            'login': "user{}".format(i),
            'password': "".join(reversed(str(i))),
            'name': "User {}".format(i),
            'status': "OK",
            'address': "Gerokstraße 38",
            'hosts': [
                generate_host(3*i + j)
                for j in range(i % 3)
            ],
            **user,
        }

    return users


class TestGerokUser(AppInitialized):
    api_mock = MagicMock()

    def setUp(self):
        self.users = get_possible_users()
        self.api_mock.reset_mock()
        self.api_mock.side_effect = partial(fake_api, self.users)

    def get_example_user(self, user_id):
        try:
            return {
                'id': user_id,
                **self.users.get(user_id)
            }
        except KeyError:
            raise ValueError("Id {} not in `users` dict".format(user_id))

    def iter_user_ip_pairs(self):
        for user_id in self.users.keys():
            for host in self.users[user_id]['hosts']:
                yield (user_id, host['ip'])

    def iter_user_login_password(self):
        for user_id, value in self.users.items():
            yield user_id, value['login'], value['password']

    def get_corresponding_entry(self, static_entries, user_entry):
        """Find the matching sample traffic entry of `self.users`

        Return None if the entry is nonexistent or `user_data`
        contains none at all
        """
        try:
            for entry in static_entries:
                if (date_from_delta(entry['relative_date']).weekday() ==
                        user_entry['day']):
                    return entry
                    break
            else:
                return
        except KeyError:
            return

    def assert_userdata_passed(self, user, user_data):
        """Test if contents of `user_data` fully appear in the `user` object
        """
        self.assertEqual(user.uid, user_data['login'])
        self.assertEqual(user.id.value, user_data['id'])
        self.assertEqual(user.login.value, user_data['login'])
        self.assertEqual(user.address.value, user_data['address'])
        if user_data['mail']:
            self.assertEqual(user.mail.value, user_data['mail'])
        else:
            self.assertIn(user_data['login'], user.mail.value)
        self.assertEqual(user.status.value, user_data['status'])
        self.assertEqual(user.realname.value, user_data['name'])
        for host in user_data['hosts']:
            # using `assertIn` allows agnosticism regarding the chosen
            # string concatenation method
            self.assertIn(host['ip'], user.ips.value)
            self.assertIn(host['mac'], user.mac.value)
            self.assertIn(host['hostname'], user.hostname.value)
            self.assertIn(host['alias'], user.hostalias.value)
        self.assertEqual(user.credit, user_data.get('credit', 0) / 1024)

    @patch('sipa.model.gerok.user.do_api_call', api_mock)
    def test_explicit_init(self):
        for user_id in ['1', '2']:
            user_data = self.get_example_user(user_id)
            user = User(user_data)
            self.assert_userdata_passed(user=user, user_data=user_data)

    @patch('sipa.model.gerok.user.do_api_call', api_mock)
    def test_ip_constructor(self):
        for user_id, ip in self.iter_user_ip_pairs():
            user_data = self.get_example_user(user_id)
            user = User.from_ip(ip)
            self.assert_userdata_passed(user=user, user_data=user_data)

    @patch('sipa.model.gerok.user.do_api_call', api_mock)
    def test_ip_constructor_foreign_ip(self):
        for ip in ["0.0.0.0", "foobarrc", ""]:
            user = User.from_ip(ip)
            self.assertIsInstance(user, AnonymousUserMixin)

    @patch('sipa.model.gerok.user.do_api_call', api_mock)
    def test_get_constructor(self):
        for user_id, login, _ in self.iter_user_login_password():
            user_data = self.get_example_user(user_id)
            user = User.get(login)
            self.assert_userdata_passed(user=user, user_data=user_data)

    @patch('sipa.model.gerok.user.do_api_call', api_mock)
    def test_authentication_correct(self):
        for user_id, login, password in self.iter_user_login_password():
            user_data = self.get_example_user(user_id)
            user = User.authenticate(login, password)
            self.assert_userdata_passed(user=user, user_data=user_data)

    @patch('sipa.model.gerok.user.do_api_call', api_mock)
    def test_authentication_user_inexistent(self):
        for not_a_login in ["foo", "bar"]:
            with self.assertRaises(UserNotFound):
                User.authenticate(not_a_login, password="")

    @patch('sipa.model.gerok.user.do_api_call', api_mock)
    def test_authentication_wrong_password(self):
        for user_id, login, password in self.iter_user_login_password():
            password = password + "wrong"
            with self.assertRaises(PasswordInvalid):
                User.authenticate(login, password)

    @patch('sipa.model.gerok.user.do_api_call', api_mock)
    def test_traffic_data_passed(self):
        for user_id in self.users.keys():
            user_data = self.get_example_user(user_id)
            user = User(user_data)
            for entry in user.traffic_history:
                try:
                    corresponding = self.get_corresponding_entry(
                        user_data['traffic_entries'],
                        entry,
                    )
                except KeyError:
                    corresponding = None

                if corresponding is not None:
                    self.assertAlmostEqual(
                        corresponding['in'] + corresponding['out'],
                        entry['throughput'],
                        delta=5,
                    )
                    self.assertAlmostEqual(
                        corresponding['credit'],
                        entry['credit'],
                        delta=5,
                    )
                else:
                    self.assertEqual(entry['input'], 0)
                    self.assertEqual(entry['output'], 0)
                    self.assertEqual(entry['throughput'], 0)
                    self.assertEqual(entry['credit'], 0)
