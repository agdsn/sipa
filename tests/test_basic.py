from flask import url_for
from prepare import AppInitialized


class TestSipaFrontendCase(AppInitialized):
    """A minimal first test case to build upon."""

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def login(self, username, password):
        return self.client.post('/login', data=dict(
            username=username,
            password=password
        ), follow_redirects=True)

    def logout(self):
        return self.client.get('/logout', follow_redirects=True)

    def test_root_redirect(self):
        response = self.client.get('/')
        self.assert_redirects(response, url_for('news.display'))
