import pytest

from sipa.model.fancy_property import (ActiveProperty, Capabilities,
                                       UnsupportedProperty, NO_CAPABILITIES)
from sipa.model.sample.user import User, SampleUserData

from ..fixture_helpers import make_testing_app


@pytest.fixture(scope="module")
def app():
    return make_testing_app(config={"BACKENDS": ["sample"]})


@pytest.fixture(scope="module")
def app_context(app):
    with app.app_context():
        yield


@pytest.fixture(scope="module")
def user(app_context) -> User:
    return User("test")


@pytest.fixture(scope="module")
def sample_users(app) -> dict[str, SampleUserData]:
    return app.extensions["sample_users"]  # type: ignore


EXPECTED_RESULT: dict[str, tuple[str, Capabilities]] = {
    # 'attr_name': ('key_in_sample_dict', Capabilities())
    "realname": ("name", NO_CAPABILITIES),
    "login": ("uid", NO_CAPABILITIES),
    "mac": ("mac", Capabilities(edit=True, delete=False)),
    "mail": ("mail", Capabilities(edit=True, delete=False)),
    "address": ("address", NO_CAPABILITIES),
    "ips": ("ip", NO_CAPABILITIES),
    "status": ("status", NO_CAPABILITIES),
    "id": ("id", NO_CAPABILITIES),
    "hostname": ("hostname", NO_CAPABILITIES),
    "hostalias": ("hostalias", NO_CAPABILITIES),
}


@pytest.mark.usefixtures("app_context")
def test_uid_not_accepted(app):
    with pytest.raises(KeyError):
        User(0)


class TestSampleUser:
    """Test that the sample user class has the correct properties."""

    @pytest.fixture(scope="class", autouse=True)
    def request_context(self, app, app_context):
        with app.test_request_context():
            yield

    def test_uid_correct(self, user, sample_users):
        assert user.uid == sample_users["test"]["uid"]

    @pytest.mark.parametrize("key,val", EXPECTED_RESULT.items())
    def test_row_getters(
        self, user, sample_users, key: str, val: tuple[str, Capabilities]
    ):
        """Test if the basic properties have been implemented accordingly."""
        if val:
            key_in_sample_dict, capabilities = val
            assert getattr(user, key) == ActiveProperty(
                name=key,
                value=sample_users["test"][key_in_sample_dict],
                capabilities=capabilities,
            )
        else:
            assert getattr(user, key) == UnsupportedProperty(key)

    @pytest.mark.parametrize("attr", EXPECTED_RESULT.keys())
    def test_row_setters(self, user, attr):
        class_attr = getattr(user.__class__, attr)

        if class_attr.fset:
            value = "given_value"
            setattr(user, attr, value)
            assert getattr(user, attr) == value

    @pytest.mark.parametrize("attr", EXPECTED_RESULT.keys())
    def test_row_deleters(self, user, attr):
        class_attr = getattr(user.__class__, attr)

        if class_attr.fdel:
            with pytest.raises(NotImplementedError):
                delattr(user, attr)

    def test_correct_password(self, user, sample_users):
        user.re_authenticate(sample_users["test"]["password"])

    def test_traffic_history(self, user):
        for day in user.traffic_history:
            assert 0 <= day["day"] <= 6
            assert 0 <= day["input"]
            assert 0 <= day["output"]
            assert day["throughput"] == day["input"] + day["output"]
