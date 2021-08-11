# -*- coding: utf-8 -*-
from .case import MockTestCase
from plone.dexterity.factory import DexterityFactory
from plone.dexterity.fti import DexterityFTI
from plone.dexterity.interfaces import IDexterityFTI
from zope.interface import Interface


try:
    from unittest.mock import Mock
except ImportError:
    from mock import Mock


class IDummy(Interface):
    pass


class TestFactory(MockTestCase):
    def test_title(self):
        fti_mock = Mock(spec=DexterityFTI, title="Mock type")
        self.mock_utility(fti_mock, IDexterityFTI, name=u"testtype")

        factory = DexterityFactory(portal_type=u"testtype")
        self.assertEqual("Mock type", factory.title)

    def test_description(self):
        fti_mock = Mock(spec=DexterityFTI, description="Mock type description")
        self.mock_utility(fti_mock, IDexterityFTI, name=u"testtype")

        factory = DexterityFactory(portal_type=u"testtype")
        self.assertEqual("Mock type description", factory.description)

    def test_get_interfaces(self):
        fti_mock = Mock(spec=DexterityFTI)
        fti_mock.lookupSchema = Mock(return_value=IDummy)
        self.mock_utility(fti_mock, IDexterityFTI, name=u"testtype")

        factory = DexterityFactory(portal_type=u"testtype")
        spec = factory.getInterfaces()

        self.assertEqual(u"testtype", spec.__name__)
        self.assertEqual([IDummy, Interface], list(spec.flattened()))

    # We expect the following when creating an object from the factory:
    #
    #   - FTI's klass attribute is asked for a class name
    #   - name is resolved to a callable
    #   - callable is called to get an object
    #   - portal_type is set if not set already

    def test_create_with_schema_already_provided_and_portal_type_set(self):

        # Object returned by class
        obj_mock = Mock(portal_type=u"testtype")

        # Class set by factory
        klass_mock = Mock(return_value=obj_mock)

        # Resolver
        from plone.dexterity.utils import resolveDottedName

        self.patch_global(resolveDottedName, return_value=klass_mock)

        # FTI
        fti_mock = Mock(spec=DexterityFTI, klass="my.mocked.ContentTypeClass")
        self.mock_utility(fti_mock, IDexterityFTI, name=u"testtype")

        factory = DexterityFactory(portal_type=u"testtype")
        self.assertEqual(obj_mock, factory())

    def test_create_sets_portal_type_if_not_set(self):

        # Object returned by class
        obj_mock = Mock()

        # Class set by factory
        klass_mock = Mock(return_value=obj_mock)

        # Resolver
        from plone.dexterity.utils import resolveDottedName

        self.patch_global(resolveDottedName, return_value=klass_mock)

        # FTI
        fti_mock = Mock(spec=DexterityFTI)
        fti_mock.klass = "my.mocked.ContentTypeClass"
        self.mock_utility(fti_mock, IDexterityFTI, name=u"testtype")

        factory = DexterityFactory(portal_type=u"testtype")
        self.assertEqual(obj_mock, factory())
        self.assertEqual(obj_mock.portal_type, u"testtype")

    def test_create_sets_portal_type_if_wrong(self):

        # Object returned by class
        obj_mock = Mock(portal_type="othertype")

        # Class set by factory
        klass_mock = Mock(return_value=obj_mock)

        # Resolver
        from plone.dexterity.utils import resolveDottedName

        self.patch_global(resolveDottedName, return_value=klass_mock)

        # FTI
        fti_mock = Mock(spec=DexterityFTI)
        fti_mock.klass = "my.mocked.ContentTypeClass"
        self.mock_utility(fti_mock, IDexterityFTI, name=u"testtype")

        factory = DexterityFactory(portal_type=u"testtype")
        self.assertEqual(obj_mock, factory())
        self.assertEqual(obj_mock.portal_type, u"testtype")

    def test_create_initialises_schema_if_not_provided(self):

        # Object returned by class
        obj_mock = Mock(portal_type=u"testtype")

        # Class set by factory
        klass_mock = Mock(return_value=obj_mock)

        # Resolver
        from plone.dexterity.utils import resolveDottedName

        self.patch_global(resolveDottedName, return_value=klass_mock)

        # FTI
        fti_mock = Mock(spec=DexterityFTI)
        fti_mock.klass = "my.mocked.ContentTypeClass"
        self.mock_utility(fti_mock, IDexterityFTI, name=u"testtype")

        factory = DexterityFactory(portal_type=u"testtype")
        self.assertEqual(obj_mock, factory())

    def test_factory_passes_args_and_kwargs(self):

        # Object returned by class
        obj_mock = Mock(portal_type=u"testtype")

        # Class set by factory
        klass_mock = Mock(return_value=obj_mock)

        # Resolver
        from plone.dexterity.utils import resolveDottedName

        self.patch_global(resolveDottedName, return_value=klass_mock)

        # FTI
        fti_mock = Mock(spec=DexterityFTI)
        fti_mock.klass = "my.mocked.ContentTypeClass"
        self.mock_utility(fti_mock, IDexterityFTI, name=u"testtype")

        factory = DexterityFactory(portal_type=u"testtype")
        self.assertEqual(obj_mock, factory(u"id", title=u"title"))
        klass_mock.assert_called_once_with(u"id", title=u"title")
