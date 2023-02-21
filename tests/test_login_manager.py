from flask import Flask, Blueprint, url_for
from flask_login import current_user, login_user

from sipa.login_manager import SipaLoginManager

from .base import TestCase


class AuthenticatedUser:
    def __init__(self, uid):
        self.uid = uid

    def get_id(self):
        return self.uid
    is_authenticated = True
    is_active = True
    is_anonymous = False


class SipaLoginManagerTest(TestCase):
    def create_app(self):
        app = Flask('test')
        app.testing = True
        app.config['SECRET_KEY'] = "foobar"*9
        login_manager = SipaLoginManager(app)

        @app.route('/login')
        def login():
            user = AuthenticatedUser(uid="test_user")
            login_user(user)
            return "OK"

        @app.route('/restricted')
        def restricted():
            return current_user.uid if current_user.is_authenticated else ""

        @login_manager.user_loader
        def load_user(uid):
            return AuthenticatedUser(uid=uid)

        self.mgr = login_manager
        return app

    def login(self):
        response = self.client.get(url_for("login"))
        assert response.data.decode() == "OK"
        from flask import g
        del g._login_user  # cached for this request context


class SipaLoginManagerAuthenticationTest(SipaLoginManagerTest):
    def test_authentication_works(self):
        self.login()
        response = self.client.get(url_for("restricted"))
        assert response.data.decode() == "test_user"

    def test_decorator_called_without_parameter(self):
        with self.assertRaises(TypeError):
            @self.app.route('/view')
            @self.mgr.disable_user_loading  # note that `()` is missing
            def view():
                return False


class AppLevelUserLoadingDisabledTest(SipaLoginManagerTest):
    def create_app(self):
        app = super().create_app()

        @app.route('/images')
        @self.mgr.disable_user_loading()
        def show_images():
            # We don't take kindly to your types around here!
            assert not current_user.is_authenticated
            return "Images :-)"

        return app

    def test_login_manager(self):
        assert self.mgr.ignored_endpoints == {'show_images'}
        self.login()
        response = self.client.get(url_for("show_images"))
        assert response.data.decode() == "Images :-)"
        assert "show_images" in self.mgr.ignored_endpoints


class BlueprintLevelUserLoadingDisabledTest(SipaLoginManagerTest):
    def create_app(self):
        app = super().create_app()
        bp = Blueprint(name='documents', import_name='documents')

        @bp.route('/documents')
        @self.mgr.disable_user_loading(bp)
        def show_documents():
            assert not current_user.is_authenticated
            return "Documents :-)"

        @bp.route('/images')
        def show_images_as_well():
            assert not current_user.is_authenticated
            return "Images :-)"
        self.mgr.ignore_endpoint('documents.show_images_as_well')

        app.register_blueprint(bp)
        return app

    def test_documents_no_user(self):
        self.login()
        response = self.client.get(url_for("documents.show_documents"))
        assert response.data.decode() == "Documents :-)"
        assert "documents.show_documents" in self.mgr.ignored_endpoints

    def test_images_no_user(self):
        self.login()
        response = self.client.get(url_for("documents.show_images_as_well"))
        assert response.data.decode() == "Images :-)"
        assert "documents.show_images_as_well" in self.mgr.ignored_endpoints
