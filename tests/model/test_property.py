from unittest import TestCase
from sipa.model.fancy_property import Capabilities


class TestCapabilitiies(TestCase):
    def test_default_capabilities(self):
        capabilities = Capabilities()

        assert (
            capabilities.displayable
            and not capabilities.copyable
            and not capabilities.edit
            and not capabilities.delete
        )

        capabilities = Capabilities.edit_if(True)
        assert (
            capabilities.displayable
            and not capabilities.copyable
            and capabilities.edit
            and not capabilities.delete
        )

        capabilities = Capabilities.edit_delete_if(True)
        assert (
            not capabilities.displayable
            and not capabilities.copyable
            and capabilities.edit
            and capabilities.delete
        )
