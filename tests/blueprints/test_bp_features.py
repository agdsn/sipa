from flask import url_for

from tests.prepare import AppInitialized


class BpFeaturesTestCase(AppInitialized):
    def test_bustimes_reachable(self):
        self.assert200(self.client.get(url_for('features.bustimes')))
        self.assertTemplateUsed("bustimes.html")
