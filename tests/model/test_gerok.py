import json
from functools import partial
from itertools import chain
from unittest.mock import MagicMock, patch
from urllib.parse import parse_qs, urlparse

from flask.ext.login import AnonymousUserMixin
from requests import Response

from sipa.model.gerok.user import User, do_api_call
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
    """A fake gerok api, replacing `do_api_call` for testing."""
    parsed = urlparse(request)
    action = parsed.path.rsplit('/')[-1]  # the bit after the last '/'

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


class TestGerokUser(AppInitialized):
    users = {
        '1': {
            'login': "test",
            'password': "123",
            'name': "Günther Schulz",
            'address': "Gerokstraße 38, 00-0",
            'mail': "test@test.de",
            'status': "OK",
            'hosts': [
                {'ip': "141.30.0.0", 'mac': "aa-bb-cc-dd-ee-ff",
                 'hostname': "foobar", 'alias': "mein_laptop"},
                {'ip': "141.30.0.1", 'mac': "aa-bb-cc-dd-ee-fe",
                 'hostname': "baz", 'alias': "mein_neuer_laptop"},
            ],
        },
        '2': {  # empty mail address
            'login': "test2",
            'password': "1234",
            'name': "Nicht Günther Schulz",
            'address': "Gerokstraße 38, 00-1",
            'mail': "",
            'status': "OK",
            'hosts': [
                {'ip': "141.30.0.2", 'mac': "aa-bb-cc-dd-ee-fd",
                 'hostname': "shizzle", 'alias': "mein_alter_dell"},
            ],
        },
    }
    api_mock = MagicMock()

    def setUp(self):
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
