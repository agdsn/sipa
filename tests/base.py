from .prepare import AppInitialized


class SampleFrontendTestBase(AppInitialized):
    def create_app(self):
        config = {'BACKENDS': ['sample']}
        return super().create_app(additional_config=config)
