from .case import MockTestCase
from plone.dexterity import schema
from plone.dexterity.fti import DexterityFTI
from plone.dexterity.interfaces import IContentType
from plone.dexterity.interfaces import IDexterityFTI
from plone.dexterity.interfaces import IDexteritySchema
from plone.dexterity.schema import invalidate_cache
from plone.dexterity.schema import SCHEMA_CACHE
from plone.supermodel.model import Model
from Products.CMFCore.interfaces import ISiteRoot
from unittest.mock import Mock
from zope.interface import Interface
from zope.interface.interface import InterfaceClass

import zope.schema


class TestSchemaModuleFactory(MockTestCase):
    def test_transient_schema(self):

        # No IDexterityFTI registered
        factory = schema.SchemaModuleFactory()
        schemaName = schema.portalTypeToSchemaName("testtype", prefix="site")
        klass = factory(schemaName, schema.generated)

        self.assertTrue(isinstance(klass, InterfaceClass))
        self.assertTrue(klass.isOrExtends(IDexteritySchema))
        self.assertTrue(IContentType.providedBy(klass))
        self.assertEqual(schemaName, klass.__name__)
        self.assertEqual("plone.dexterity.schema.generated", klass.__module__)
        self.assertEqual((), tuple(zope.schema.getFields(klass)))

    def test_concrete_default_schema(self):

        # Mock schema model
        class IDummy(Interface):
            dummy = zope.schema.TextLine(title="Dummy")

        mock_model = Model({"": IDummy})

        # Mock FTI
        fti_mock = Mock(spec=DexterityFTI)
        fti_mock.lookupModel = Mock(return_value=mock_model)
        self.mock_utility(fti_mock, IDexterityFTI, "testtype")

        factory = schema.SchemaModuleFactory()

        schemaName = schema.portalTypeToSchemaName("testtype", prefix="site")
        klass = factory(schemaName, schema.generated)

        self.assertTrue(isinstance(klass, InterfaceClass))
        self.assertTrue(klass.isOrExtends(IDexteritySchema))
        self.assertTrue(IContentType.providedBy(klass))
        self.assertEqual(schemaName, klass.__name__)
        self.assertEqual("plone.dexterity.schema.generated", klass.__module__)
        self.assertEqual(("dummy",), tuple(zope.schema.getFieldNames(klass)))

    def test_named_schema(self):

        # Mock schema model
        class IDummy(Interface):
            dummy = zope.schema.TextLine(title="Dummy")

        class INamedDummy(Interface):
            named = zope.schema.TextLine(title="Named")

        mock_model = Model({"": IDummy, "named": INamedDummy})

        # Mock FTI
        fti_mock = Mock(spec=DexterityFTI)
        fti_mock.lookupModel = Mock(return_value=mock_model)
        self.mock_utility(fti_mock, IDexterityFTI, "testtype")

        factory = schema.SchemaModuleFactory()

        schemaName = schema.portalTypeToSchemaName(
            "testtype", schema="named", prefix="site"
        )
        klass = factory(schemaName, schema.generated)

        self.assertTrue(isinstance(klass, InterfaceClass))

        # only default schema gets this:
        self.assertFalse(klass.isOrExtends(IDexteritySchema))

        self.assertFalse(IContentType.providedBy(klass))
        self.assertEqual(schemaName, klass.__name__)
        self.assertEqual("plone.dexterity.schema.generated", klass.__module__)
        self.assertEqual(("named",), tuple(zope.schema.getFieldNames(klass)))

    def test_transient_schema_made_concrete(self):

        factory = schema.SchemaModuleFactory()
        schemaName = schema.portalTypeToSchemaName("testtype", prefix="site")

        # No IDexterityFTI registered

        klass = factory(schemaName, schema.generated)
        self.assertTrue(isinstance(klass, InterfaceClass))
        self.assertTrue(klass.isOrExtends(IDexteritySchema))
        self.assertTrue(IContentType.providedBy(klass))
        self.assertEqual(schemaName, klass.__name__)
        self.assertEqual("plone.dexterity.schema.generated", klass.__module__)
        self.assertEqual((), tuple(zope.schema.getFields(klass)))

        # Calling it again gives the same result

        klass = factory(schemaName, schema.generated)
        self.assertTrue(isinstance(klass, InterfaceClass))
        self.assertTrue(klass.isOrExtends(IDexteritySchema))
        self.assertTrue(IContentType.providedBy(klass))
        self.assertEqual(schemaName, klass.__name__)
        self.assertEqual("plone.dexterity.schema.generated", klass.__module__)
        self.assertEqual((), tuple(zope.schema.getFields(klass)))

        # Now register a mock FTI and try again

        class IDummy(Interface):
            dummy = zope.schema.TextLine(title="Dummy")

        mock_model = Model({"": IDummy})

        fti_mock = Mock(spec=DexterityFTI)
        fti_mock.lookupModel = Mock(return_value=mock_model)
        self.mock_utility(fti_mock, IDexterityFTI, "testtype")

        klass = factory(schemaName, schema.generated)

        self.assertTrue(isinstance(klass, InterfaceClass))
        self.assertTrue(klass.isOrExtends(IDexteritySchema))
        self.assertTrue(IContentType.providedBy(klass))
        self.assertEqual(schemaName, klass.__name__)
        self.assertEqual("plone.dexterity.schema.generated", klass.__module__)

        # Now we get the fields from the FTI's model
        self.assertEqual(("dummy",), tuple(zope.schema.getFieldNames(klass)))

    def test_portalTypeToSchemaName_with_schema_and_prefix(self):
        self.assertEqual(
            "prefix_0_type_0_schema",
            schema.portalTypeToSchemaName("type", "schema", "prefix"),
        )
        self.assertEqual(
            "prefix_0_type", schema.portalTypeToSchemaName("type", "", "prefix")
        )
        self.assertEqual(
            "prefix_0_type_1_one_2_two",
            schema.portalTypeToSchemaName("type one.two", "", "prefix"),
        )

    def test_portalTypeToSchemaName_looks_up_portal_for_prefix(self):
        portal_mock = Mock()
        portal_mock.getPhysicalPath = Mock(return_value=["", "foo", "portalid"])
        self.mock_utility(portal_mock, ISiteRoot)

        self.assertEqual("foo_4_portalid_0_type", schema.portalTypeToSchemaName("type"))

    def test_schemaNameToPortalType(self):
        self.assertEqual(
            "type", schema.schemaNameToPortalType("prefix_0_type_0_schema")
        )
        self.assertEqual("type", schema.schemaNameToPortalType("prefix_0_type"))
        self.assertEqual(
            "type one.two", schema.schemaNameToPortalType("prefix_0_type_1_one_2_two")
        )

    def test_splitSchemaName(self):
        self.assertEqual(
            (
                "prefix",
                "type",
                "schema",
            ),
            schema.splitSchemaName("prefix_0_type_0_schema"),
        )
        self.assertEqual(
            (
                "prefix",
                "type",
                "",
            ),
            schema.splitSchemaName("prefix_0_type"),
        )
        self.assertEqual(
            (
                "prefix",
                "type one.two",
                "",
            ),
            schema.splitSchemaName("prefix_0_type_1_one_2_two"),
        )

    def test_invalidate_cache(self):
        portal_type = "testtype"
        fti = DexterityFTI(portal_type)
        SCHEMA_CACHE.get(portal_type)
        SCHEMA_CACHE.behavior_schema_interfaces(fti)
        self.assertIn("_v_schema_behavior_schema_interfaces", fti.__dict__.keys())

        invalidate_cache(fti)
        self.assertNotIn("_v_schema_behavior_schema_interfaces", fti.__dict__.keys())
