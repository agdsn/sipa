from unittest.mock import patch, MagicMock

from flask import url_for

from tests.base import SampleFrontendTestBase


class BpFeaturesTestCase(SampleFrontendTestBase):
    def test_bustimes_reachable(self):
        mock = MagicMock()
        with patch('sipa.blueprints.features.get_bustimes', mock):
            resp = self.client.get(url_for('features.bustimes'))

        self.assert200(resp)
        self.assertTemplateUsed("bustimes.html")
        assert mock.called
