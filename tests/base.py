from .prepare import AppInitialized


def dynamic_frontend_base(backend):
    class cls(AppInitialized):
        def create_app(self, *a, **kw):
            config = {
                **kw.pop('additional_config', {}),
                'BACKENDS': [backend],
            }
            return super().create_app(additional_config=config)

    return cls


SampleFrontendTestBase = dynamic_frontend_base('sample')
WuFrontendTestBase = dynamic_frontend_base('wu')
HssFrontendTestBase = dynamic_frontend_base('hss')
GerokFrontendTestBase = dynamic_frontend_base('gerok')
