from flask import url_for

from tests.base import SampleFrontendTestBase


class BpFeaturesTestCase(SampleFrontendTestBase):
    def test_bustimes_reachable(self):
        self.assert200(self.client.get(url_for('features.bustimes')))
        self.assertTemplateUsed("bustimes.html")
