from .case import MockTestCase
from plone.dexterity.factory import DexterityFactory
from plone.dexterity.fti import DexterityFTI
from plone.dexterity.fti import DexterityFTIModificationDescription
from plone.dexterity.fti import ftiAdded
from plone.dexterity.fti import ftiModified
from plone.dexterity.fti import ftiRemoved
from plone.dexterity.fti import ftiRenamed
from plone.dexterity.interfaces import IDexterityFTI
from plone.dexterity.schema import DexteritySchemaPolicy
from plone.dexterity.schema import portalTypeToSchemaName
from plone.dexterity.tests.schemata import ITestSchema
from plone.supermodel.model import Model
from Products.CMFCore.interfaces import ISiteRoot
from unittest.mock import Mock
from zope.component import getGlobalSiteManager
from zope.component import queryUtility
from zope.component.hooks import setHooks
from zope.component.hooks import setSite
from zope.component.interfaces import IFactory
from zope.component.persistentregistry import PersistentComponents
from zope.container.contained import ObjectAddedEvent
from zope.container.contained import ObjectMovedEvent
from zope.container.contained import ObjectRemovedEvent
from zope.interface import Interface
from zope.lifecycleevent import ObjectModifiedEvent
from zope.lifecycleevent.interfaces import IObjectModifiedEvent
from zope.security.interfaces import IPermission

import os.path
import plone.dexterity.schema.generated
import zope.schema


class TestClass:
    meta_type = "Test Class"


class TestClass2:
    meta_type = "Test Class 2"


class ITestInterface(Interface):
    pass


class DexterityMtimeFTI(DexterityFTI):
    # It was necessary to overwrite the _p_mtime attribute, as it is originally
    # read-only.
    _p_mtime = None


class TestFTI(MockTestCase):
    def test_factory_name_is_fti_id(self):
        fti = DexterityFTI("testtype")
        self.assertEqual("testtype", fti.getId())
        self.assertEqual("testtype", fti.factory)

    def test_hasDynamicSchema(self):
        fti = DexterityFTI("testtype")
        fti.schema = "dummy.schema"
        self.assertEqual(False, fti.hasDynamicSchema)
        fti.schema = None
        self.assertEqual(True, fti.hasDynamicSchema)

    def test_lookupSchema_with_concrete_schema(self):
        fti = DexterityFTI("testtype")
        fti.schema = "plone.dexterity.tests.schemata.ITestSchema"
        self.assertEqual(ITestSchema, fti.lookupSchema())
        # second time uses _v attribute
        self.assertEqual(ITestSchema, fti.lookupSchema())

    def test_lookupSchema_with_dynamic_schema(self):
        fti = DexterityFTI("testtype")
        fti.schema = None  # use dynamic schema

        portal = self.create_dummy(getPhysicalPath=lambda: ("", "site"))
        self.mock_utility(portal, ISiteRoot)

        schemaName = portalTypeToSchemaName(fti.getId())
        setattr(plone.dexterity.schema.generated, schemaName, ITestSchema)

        self.assertEqual(ITestSchema, fti.lookupSchema())

        # cleanup
        delattr(plone.dexterity.schema.generated, schemaName)

    def test_lookupSchema_with_nonexistant_schema(self):
        """Tests the case where a dexterity type is not removed cleanly
        from the fti, but the code has been removed.
        """
        fti = DexterityFTI("testtype")
        fti.schema = "model.wont.be.imported"
        portal = self.create_dummy(getPhysicalPath=lambda: ("", "site"))
        self.mock_utility(portal, ISiteRoot)
        schemaName = portalTypeToSchemaName(fti.getId())
        setattr(plone.dexterity.schema.generated, schemaName, ITestSchema)
        self.assertEqual(ITestSchema, fti.lookupSchema())
        delattr(plone.dexterity.schema.generated, schemaName)

    def test_lookupModel_from_string(self):
        fti = DexterityFTI("testtype")
        fti.schema = None
        fti.model_source = "<model />"
        fti.model_file = None

        model_dummy = Model()

        from plone.supermodel import loadString

        self.patch_global(loadString, return_value=model_dummy)

        model = fti.lookupModel()
        self.assertIs(model_dummy, model)

    def test_lookupModel_from_file_with_package(self):

        fti = DexterityFTI("testtype")
        fti.schema = None
        fti.model_source = None
        fti.model_file = "plone.dexterity.tests:test.xml"

        model_dummy = Model()

        import plone.dexterity.tests

        abs_file = os.path.join(
            os.path.split(plone.dexterity.tests.__file__)[0], "test.xml"
        )

        from plone.supermodel import loadFile

        loadFile_mock = self.patch_global(loadFile, return_value=model_dummy)

        model = fti.lookupModel()
        self.assertIs(model_dummy, model)
        loadFile_mock.assert_called_once_with(abs_file, reload=True, policy="dexterity")

    def test_lookupModel_from_file_with_absolute_path(self):

        import plone.dexterity.tests

        abs_file = os.path.join(
            os.path.split(plone.dexterity.tests.__file__)[0], "test.xml"
        )

        fti = DexterityFTI("testtype")
        fti.schema = None
        fti.model_source = None
        fti.model_file = abs_file

        model_dummy = Model()

        from plone.supermodel import loadFile

        loadFile_mock = self.patch_global(loadFile, return_value=model_dummy)

        model = fti.lookupModel()
        self.assertIs(model_dummy, model)
        loadFile_mock.assert_called_once_with(abs_file, reload=True, policy="dexterity")

    def test_lookupModel_from_file_with_win32_absolute_path(self):

        fti = DexterityFTI("testtype")
        fti.schema = None
        fti.model_source = None
        fti.model_file = r"C:\models\testmodel.xml"

        model_dummy = Model()

        from os.path import isabs
        from os.path import isfile

        self.patch_global(isabs, return_value=True)
        self.patch_global(isfile, return_value=True)

        from plone.supermodel import loadFile

        loadFile_mock = self.patch_global(loadFile, return_value=model_dummy)

        model = fti.lookupModel()
        self.assertIs(model_dummy, model)
        loadFile_mock.assert_called_once_with(
            fti.model_file, reload=True, policy="dexterity"
        )

    def test_lookupModel_with_schema_only(self):
        fti = DexterityFTI("testtype")
        fti.schema = "plone.dexterity.tests.schemata.ITestSchema"
        fti.model_source = None
        fti.model_file = None

        model = fti.lookupModel()
        self.assertEqual(1, len(model.schemata))
        self.assertEqual(ITestSchema, model.schema)

    def test_lookupModel_from_string_with_schema(self):
        fti = DexterityFTI("testtype")
        # effectively ignored:
        fti.schema = "plone.dexterity.tests.schemata.ITestSchema"
        fti.model_source = "<model />"
        fti.model_file = None

        model_dummy = Model()

        from plone.supermodel import loadString

        loadString_mock = self.patch_global(loadString, return_value=model_dummy)

        model = fti.lookupModel()
        self.assertIs(model_dummy, model)
        self.assertIs(ITestSchema, fti.lookupSchema())
        loadString_mock.assert_called_once_with(fti.model_source, policy="dexterity")

    def test_lookupModel_failure(self):
        fti = DexterityFTI("testtype")
        fti.schema = None
        fti.model_source = None
        fti.model_file = None

        self.assertRaises(ValueError, fti.lookupModel)

    def test_fires_modified_event_on_update_property_if_changed(self):
        fti = DexterityFTI("testtype")

        fti.title = "Old title"
        fti.global_allow = False

        from zope.event import notify

        notify_mock = self.patch_global(notify)

        fti._updateProperty("title", "New title")  # fires event caught above
        fti._updateProperty("allow_discussion", False)  # does not fire

        event = notify_mock.call_args[0][0]
        self.assertTrue(IObjectModifiedEvent.providedBy(event))
        self.assertEqual(len(event.descriptions), 1)
        self.assertEqual(event.descriptions[0].attribute, "title")
        self.assertEqual(event.descriptions[0].oldValue, "Old title")

    def test_fires_modified_event_on_change_props_per_changed_property(self):
        fti = DexterityFTI("testtype")
        fti.title = "Old title"
        fti.allow_discussion = False
        fti.global_allow = True

        from zope.event import notify

        notify_mock = self.patch_global(notify)

        fti.manage_changeProperties(
            title="New title", allow_discussion=False, global_allow=False
        )

        self.assertEqual(len(notify_mock.call_args_list), 2)

    def test_checks_permission_in_is_construction_allowed_true(self):
        fti = DexterityFTI("testtype")
        fti.add_permission = "demo.Permission"
        container_dummy = self.create_dummy()

        permission_dummy = self.create_dummy()
        permission_dummy.id = "demo.Permission"
        permission_dummy.title = "Some add permission"

        self.mock_utility(permission_dummy, IPermission, name="demo.Permission")

        security_manager_mock = Mock()
        security_manager_mock.checkPermission = Mock(return_value=True)
        from AccessControl import getSecurityManager

        self.patch_global(getSecurityManager, return_value=security_manager_mock)

        self.assertEqual(True, fti.isConstructionAllowed(container_dummy))
        security_manager_mock.checkPermission.assert_called_once_with(
            "Some add permission", container_dummy
        )

    def test_checks_permission_in_is_construction_allowed_false(self):
        fti = DexterityFTI("testtype")
        fti.add_permission = "demo.Permission"
        container_dummy = self.create_dummy()

        permission_dummy = self.create_dummy()
        permission_dummy.id = "demo.Permission"
        permission_dummy.title = "Some add permission"

        self.mock_utility(permission_dummy, IPermission, name="demo.Permission")

        security_manager_mock = Mock()
        security_manager_mock.checkPermission = Mock(return_value=False)
        from AccessControl import getSecurityManager

        self.patch_global(getSecurityManager, return_value=security_manager_mock)

        self.assertEqual(False, fti.isConstructionAllowed(container_dummy))
        security_manager_mock.checkPermission.assert_called_once_with(
            "Some add permission", container_dummy
        )

    def test_no_permission_utility_means_no_construction(self):
        fti = DexterityFTI("testtype")
        fti.add_permission = "demo.Permission"  # not an IPermission utility
        container_dummy = self.create_dummy()
        self.assertEqual(False, fti.isConstructionAllowed(container_dummy))

    def test_no_permission_means_no_construction(self):
        fti = DexterityFTI("testtype")
        fti.add_permission = None
        container_dummy = self.create_dummy()
        self.assertEqual(False, fti.isConstructionAllowed(container_dummy))

    def test_add_view_url_set_on_creation(self):
        fti = DexterityFTI("testtype")
        self.assertEqual("string:${folder_url}/++add++testtype", fti.add_view_expr)

    def test_factory_set_on_creation(self):
        fti = DexterityFTI("testtype")
        self.assertEqual("testtype", fti.factory)

    def test_addview_and_factory_not_overridden_on_creation(self):
        fti = DexterityFTI(
            "testtype",
            add_view_expr="string:${folder_url}/@@my-addview",
            factory="my.factory",
        )
        self.assertEqual("string:${folder_url}/@@my-addview", fti.add_view_expr)
        self.assertEqual("my.factory", fti.factory)

    def test_meta_type(self):
        fti = DexterityFTI("testtype", klass="plone.dexterity.tests.test_fti.TestClass")
        self.assertEqual(TestClass.meta_type, fti.Metatype())

    def test_meta_type_change_class(self):
        fti = DexterityFTI("testtype", klass="plone.dexterity.tests.test_fti.TestClass")
        fti._updateProperty("klass", "plone.dexterity.tests.test_fti.TestClass2")
        self.assertEqual(TestClass2.meta_type, fti.Metatype())

    def test_title_i18n(self):
        fti = DexterityFTI("testtype", title=b"t\xc3\xa9st")

        # with no i18n domain, we get the UTF8-encoded title
        self.assertEqual(b"t\xc3\xa9st".decode("utf8"), fti.Title())

        # with an i18n domain, we get a Message
        fti.i18n_domain = "test"
        msgid = fti.Title()
        self.assertEqual("t\xe9st", msgid)
        self.assertEqual("test", msgid.domain)

    def test_description_i18n(self):
        fti = DexterityFTI("testtype", description=b"t\xc3\xa9st")

        # with no i18n domain, we get the UTF8-encoded title
        self.assertEqual(b"t\xc3\xa9st".decode("utf8"), fti.Description())

        # with an i18n domain, we get a Message
        fti.i18n_domain = "test"
        msgid = fti.Description()
        self.assertEqual("t\xe9st", msgid)
        self.assertEqual("test", msgid.domain)

    def test_lookupModel_without_schema_policy(self):
        gsm = getGlobalSiteManager()
        gsm.registerUtility(
            DexteritySchemaPolicy(),
            plone.supermodel.interfaces.ISchemaPolicy,
            name="dexterity",
        )

        fti = DexterityFTI("testtype")
        fti.schema = None
        fti.model_source = (
            '<model xmlns="http://namespaces.plone.org/'
            'supermodel/schema"><schema/></model>'
        )
        fti.model_file = None

        model = fti.lookupModel()
        self.assertEqual(False, ITestInterface in model.schemata[""].__bases__)

    def test_lookupModel_with_schema_policy(self):
        class TestSchemaPolicy(DexteritySchemaPolicy):
            def bases(self, schemaName, tree):
                return (ITestInterface,)

        gsm = getGlobalSiteManager()
        policy = TestSchemaPolicy()
        gsm.registerUtility(
            policy, plone.supermodel.interfaces.ISchemaPolicy, name="test"
        )

        fti = DexterityFTI("testtype")
        fti.schema = None
        fti.model_source = (
            '<model xmlns="http://namespaces.plone.org/'
            'supermodel/schema"><schema/></model>'
        )
        fti.model_file = None
        fti.schema_policy = "test"

        model = fti.lookupModel()
        self.assertEqual(True, ITestInterface in model.schemata[""].__bases__)


class TestFTIEvents(MockTestCase):

    # These tests are a bit verbose, but the basic premise is pretty simple.
    # We create a proxy mock of a PersistentComponents() registry, and
    # use this for mock assertions as well as to verify that the right
    # components really do get added/removed (using passthrough).

    def test_components_registered_on_add(self):
        portal_type = "testtype"
        fti = DexterityFTI(portal_type)
        container_dummy = self.create_dummy()

        # Mock the lookup of the site and the site manager at the site root
        dummy_site = self.create_dummy()
        self.mock_utility(dummy_site, ISiteRoot)

        site_manager_mock = Mock(
            wraps=PersistentComponents(bases=(getGlobalSiteManager(),))
        )
        from zope.component.hooks import getSiteManager

        self.patch_global(getSiteManager, return_value=site_manager_mock)

        ftiAdded(fti, ObjectAddedEvent(fti, container_dummy, fti.getId()))

        args1, kwargs1 = site_manager_mock.registerUtility.call_args_list[0]
        self.assertEqual(args1, (fti, IDexterityFTI, portal_type))
        self.assertEqual(kwargs1, {"info": "plone.dexterity.dynamic"})

        args2, kwargs2 = site_manager_mock.registerUtility.call_args_list[1]
        self.assertIsInstance(args2[0], DexterityFactory)
        self.assertEqual(args2[0].portal_type, portal_type)
        self.assertEqual(args2[1:], (IFactory, portal_type))
        self.assertEqual(kwargs2, {"info": "plone.dexterity.dynamic"})

        site_dummy = self.create_dummy(getSiteManager=lambda: site_manager_mock)
        setSite(site_dummy)
        setHooks()

        self.assertNotEqual(None, queryUtility(IDexterityFTI, name=portal_type))
        self.assertNotEqual(None, queryUtility(IFactory, name=portal_type))

    def test_components_not_registered_on_add_if_exist(self):
        portal_type = "testtype"
        fti = DexterityFTI(portal_type)
        container_dummy = self.create_dummy()

        # Mock the lookup of the site and the site manager at the site root
        dummy_site = self.create_dummy()
        self.mock_utility(dummy_site, ISiteRoot)

        site_manager_mock = Mock(
            wraps=PersistentComponents(bases=(getGlobalSiteManager(),))
        )
        from zope.component.hooks import getSiteManager

        self.patch_global(getSiteManager, return_value=site_manager_mock)

        # Register FTI utility and factory utility

        self.mock_utility(fti, IDexterityFTI, name=portal_type)
        self.mock_utility(DexterityFactory(portal_type), IFactory, name=portal_type)

        # We expect that all components are registered, so do not expect any
        # registrations

        ftiAdded(fti, ObjectAddedEvent(fti, container_dummy, fti.getId()))

        self.assertFalse(site_manager_mock.registerUtility.called)

    def test_components_unregistered_on_delete(self):
        portal_type = "testtype"
        fti = DexterityFTI(portal_type)
        container_dummy = self.create_dummy()

        # Mock the lookup of the site and the site manager at the site root
        dummy_site = self.create_dummy()
        self.mock_utility(dummy_site, ISiteRoot)

        site_manager_mock = Mock(
            wraps=PersistentComponents(bases=(getGlobalSiteManager(),))
        )
        from zope.component.hooks import getSiteManager

        self.patch_global(getSiteManager, return_value=site_manager_mock)

        # First add the components
        ftiAdded(fti, ObjectAddedEvent(fti, container_dummy, fti.getId()))

        # Then remove them again
        ftiRemoved(fti, ObjectRemovedEvent(fti, container_dummy, fti.getId()))

        site_dummy = self.create_dummy(getSiteManager=lambda: site_manager_mock)
        setSite(site_dummy)
        setHooks()

        self.assertEqual(None, queryUtility(IDexterityFTI, name=portal_type))
        self.assertEqual(None, queryUtility(IFactory, name=portal_type))

    def test_components_unregistered_on_delete_does_not_error_with_no_components(
        self,
    ):  # noqa
        portal_type = "testtype"
        fti = DexterityFTI(portal_type)
        container_dummy = self.create_dummy()

        # Mock the lookup of the site and the site manager at the site root
        dummy_site = self.create_dummy()
        self.mock_utility(dummy_site, ISiteRoot)

        site_manager_mock = Mock(
            wraps=PersistentComponents(bases=(getGlobalSiteManager(),))
        )
        from zope.component.hooks import getSiteManager

        self.patch_global(getSiteManager, return_value=site_manager_mock)

        # We expect to always be able to unregister without error, even if the
        # components do not exist (as here)

        ftiRemoved(fti, ObjectRemovedEvent(fti, container_dummy, fti.getId()))

        site_manager_mock.unregisterUtility.assert_called_once_with(
            provided=IDexterityFTI, name=portal_type
        )

    def test_global_components_not_unregistered_on_delete(self):
        portal_type = "testtype"
        fti = DexterityFTI(portal_type)
        container_dummy = self.create_dummy()

        # Mock the lookup of the site and the site manager at the site root
        dummy_site = self.create_dummy()
        self.mock_utility(dummy_site, ISiteRoot)

        site_manager_mock = Mock(
            wraps=PersistentComponents(bases=(getGlobalSiteManager(),))
        )
        from zope.component.hooks import getSiteManager

        self.patch_global(getSiteManager, return_value=site_manager_mock)

        # Register FTI utility and factory utility

        self.mock_utility(fti, IDexterityFTI, name=portal_type)
        self.mock_utility(DexterityFactory(portal_type), IFactory, name=portal_type)

        # We expect to always be able to unregister without error, even if the
        # component exists. The factory is only unregistered if it was
        # registered with info='plone.dexterity.dynamic'.

        ftiRemoved(fti, ObjectRemovedEvent(fti, container_dummy, fti.getId()))

        site_dummy = self.create_dummy(getSiteManager=lambda: site_manager_mock)
        setSite(site_dummy)
        setHooks()

        self.assertNotEqual(None, queryUtility(IDexterityFTI, name=portal_type))
        self.assertNotEqual(None, queryUtility(IFactory, name=portal_type))

    def test_components_reregistered_on_rename(self):
        portal_type = "testtype"
        fti = DexterityFTI(portal_type)
        container_dummy = self.create_dummy()

        # Mock the lookup of the site and the site manager at the site root
        dummy_site = self.create_dummy()
        self.mock_utility(dummy_site, ISiteRoot)

        site_manager_mock = Mock(
            wraps=PersistentComponents(bases=(getGlobalSiteManager(),))
        )
        from zope.component.hooks import getSiteManager

        self.patch_global(getSiteManager, return_value=site_manager_mock)

        self.assertEqual("string:${folder_url}/++add++testtype", fti.add_view_expr)

        ftiRenamed(
            fti,
            ObjectMovedEvent(
                fti, container_dummy, fti.getId(), container_dummy, "newtype"
            ),
        )

        # First look for unregistration of all local components
        site_manager_mock.unregisterUtility.assert_called_once_with(
            provided=IDexterityFTI, name=portal_type
        )

        # Then look for re-registration of global components
        self.assertEqual(site_manager_mock.registerUtility.call_count, 2)

        site_dummy = self.create_dummy(getSiteManager=lambda: site_manager_mock)
        setSite(site_dummy)
        setHooks()

        self.assertNotEqual(None, queryUtility(IDexterityFTI, name=portal_type))
        self.assertNotEqual(None, queryUtility(IFactory, name=portal_type))

    def test_dynamic_schema_refreshed_on_modify_model_file(self):
        portal_type = "testtype"
        fti = DexterityFTI(portal_type)

        class INew(Interface):
            title = zope.schema.TextLine(title="title")

        model_dummy = Model({"": INew})

        fti.lookupModel = Mock(return_value=model_dummy)
        self.create_dummy()

        site_dummy = self.create_dummy(getPhysicalPath=lambda: ("", "siteid"))
        self.mock_utility(site_dummy, ISiteRoot)

        class IBlank1(Interface):
            pass

        # Set source interface
        schemaName = portalTypeToSchemaName(fti.getId())
        setattr(plone.dexterity.schema.generated, schemaName, IBlank1)

        # Sync this with schema
        ftiModified(
            fti,
            ObjectModifiedEvent(
                fti, DexterityFTIModificationDescription("model_file", "")
            ),
        )

        self.assertTrue("title" in IBlank1)
        self.assertTrue(IBlank1["title"].title == "title")

    def test_dynamic_schema_refreshed_on_modify_model_source(self):
        portal_type = "testtype"
        fti = DexterityFTI(portal_type)

        class INew(Interface):
            title = zope.schema.TextLine(title="title")

        model_dummy = Model({"": INew})

        fti.lookupModel = Mock(return_value=model_dummy)
        self.create_dummy()

        site_dummy = self.create_dummy(getPhysicalPath=lambda: ("", "siteid"))
        self.mock_utility(site_dummy, ISiteRoot)

        # b/c of zope.interface does not support hashing of the same class multiple times
        # we need to postfix with a unique number
        # see https://github.com/zopefoundation/zope.interface/issues/216#issuecomment-701332380
        class IBlank2(Interface):
            pass

        # Set source interface
        schemaName = portalTypeToSchemaName(fti.getId())
        setattr(plone.dexterity.schema.generated, schemaName, IBlank2)

        # Sync this with schema
        ftiModified(
            fti,
            ObjectModifiedEvent(
                fti, DexterityFTIModificationDescription("model_source", "")
            ),
        )

        self.assertTrue("title" in IBlank2)
        self.assertTrue(IBlank2["title"].title == "title")

    def test_dynamic_schema_refreshed_on_modify_schema_policy(self):
        portal_type = "testtype"
        fti = DexterityFTI(portal_type)

        class INew(Interface):
            title = zope.schema.TextLine(title="title")

        class IBlank3(Interface):
            pass

        class TestSchemaPolicy(DexteritySchemaPolicy):
            def bases(self, schemaName, tree):
                return (INew,)

        gsm = getGlobalSiteManager()
        policy = TestSchemaPolicy()
        gsm.registerUtility(
            policy, plone.supermodel.interfaces.ISchemaPolicy, name="test"
        )

        site_dummy = self.create_dummy(getPhysicalPath=lambda: ("", "siteid"))
        self.mock_utility(site_dummy, ISiteRoot)

        # Set source interface
        schemaName = portalTypeToSchemaName(fti.getId())
        setattr(plone.dexterity.schema.generated, schemaName, IBlank3)
        original = getattr(plone.dexterity.schema.generated, schemaName)
        self.assertNotIn(INew, original.__bases__)
        self.assertNotIn("title", original)

        # Set new schema_policy
        fti.schema_policy = "test"

        # Sync this with schema
        ftiModified(
            fti,
            ObjectModifiedEvent(
                fti, DexterityFTIModificationDescription("schema_policy", "")
            ),
        )
        updated = getattr(plone.dexterity.schema.generated, schemaName)
        self.assertIn("title", updated)
        self.assertIn(INew, updated.__bases__)

    def test_concrete_schema_not_refreshed_on_modify_schema(self):
        portal_type = "testtype"
        fti = DexterityFTI(portal_type)

        class IBlank4(Interface):
            pass

        class INew(Interface):
            title = zope.schema.TextLine(title="title")

        model_dummy = Model({"": INew})
        fti.lookupModel = Mock(return_value=model_dummy)

        site_dummy = self.create_dummy(getPhysicalPath=lambda: ("", "siteid"))
        self.mock_utility(site_dummy, ISiteRoot)

        # Set schema to something so that hasDynamicSchema is false
        fti.schema = IBlank4.__identifier__
        assert not fti.hasDynamicSchema

        # Set source for dynamic FTI - should not be used
        schemaName = portalTypeToSchemaName(fti.getId())
        setattr(plone.dexterity.schema.generated, schemaName, IBlank4)

        # Sync should not happen now

        ftiModified(
            fti,
            ObjectModifiedEvent(fti, DexterityFTIModificationDescription("schema", "")),
        )

        self.assertFalse("title" in IBlank4)

    def test_old_factory_unregistered_after_name_changed_if_dynamic(self):
        portal_type = "testtype"
        fti = DexterityFTI(portal_type)

        # Mock the lookup of the site and the site manager at the site root
        dummy_site = self.create_dummy()
        self.mock_utility(dummy_site, ISiteRoot)

        site_manager_mock = Mock(
            wraps=PersistentComponents(bases=(getGlobalSiteManager(),))
        )
        from zope.component.hooks import getSiteManager

        self.patch_global(getSiteManager, return_value=site_manager_mock)

        # Pretend like we have a utility registered

        reg1 = self.create_dummy()
        reg1.provided = IFactory
        reg1.name = "old-factory"
        reg1.info = "plone.dexterity.dynamic"

        site_manager_mock.registeredUtilities = Mock(return_value=[reg1])

        fti.factory = "new-factory"
        ftiModified(
            fti,
            ObjectModifiedEvent(
                fti, DexterityFTIModificationDescription("factory", "old-factory")
            ),
        )

        # Expect this to get removed
        site_manager_mock.unregisterUtility.assert_called_once_with(
            provided=IFactory, name="old-factory"
        )
        # And a new one to be created with the new factory name
        self.assertEqual(
            site_manager_mock.registerUtility.call_args[0][2], "new-factory"
        )

    def test_new_factory_not_registered_after_name_changed_if_exists(self):
        portal_type = "testtype"
        fti = DexterityFTI(portal_type)

        # Mock the lookup of the site and the site manager at the site root
        dummy_site = self.create_dummy()
        self.mock_utility(dummy_site, ISiteRoot)

        site_manager_mock = Mock(
            wraps=PersistentComponents(bases=(getGlobalSiteManager(),))
        )
        from zope.component.hooks import getSiteManager

        self.patch_global(getSiteManager, return_value=site_manager_mock)

        # Create a global default for the new name
        self.mock_utility(DexterityFactory(portal_type), IFactory, name="new-factory")

        fti.factory = "new-factory"
        ftiModified(
            fti,
            ObjectModifiedEvent(
                fti, DexterityFTIModificationDescription("factory", "old-factory")
            ),
        )

        # Factory should not be registered again
        self.assertFalse(site_manager_mock.registerUtility.called)

    def test_old_factory_not_unregistered_if_not_created_by_dexterity(self):
        portal_type = "testtype"
        fti = DexterityFTI(portal_type)

        # Mock the lookup of the site and the site manager at the site root
        dummy_site = self.create_dummy()
        self.mock_utility(dummy_site, ISiteRoot)

        site_manager_mock = Mock(
            wraps=PersistentComponents(bases=(getGlobalSiteManager(),))
        )
        from zope.component.hooks import getSiteManager

        self.patch_global(getSiteManager, return_value=site_manager_mock)

        # Pretend like we have a utility registered

        reg1 = self.create_dummy()
        reg1.provided = IFactory
        reg1.name = "old-factory"
        reg1.info = None

        site_manager_mock.registeredUtilities = Mock(return_value=[reg1])

        fti.factory = "new-factory"
        ftiModified(
            fti,
            ObjectModifiedEvent(
                fti, DexterityFTIModificationDescription("factory", "old-factory")
            ),
        )

        # This should not be removed, since we didn't create it
        self.assertFalse(site_manager_mock.unregisterUtility.called)
        # A new one may still be created, however
        self.assertEqual(
            site_manager_mock.registerUtility.call_args[0][2], "new-factory"
        )

    def test_renamed_factory_not_unregistered_if_not_unique(self):
        portal_type = "testtype"
        fti = DexterityFTI(portal_type, factory="common-factory")
        portal_type2 = "testtype2"
        fti2 = DexterityFTI(portal_type2, factory="common-factory")

        # Mock the lookup of the site and the site manager at the site root
        dummy_site = self.create_dummy()
        self.mock_utility(dummy_site, ISiteRoot)

        site_manager_mock = Mock(
            wraps=PersistentComponents(bases=(getGlobalSiteManager(),))
        )
        from zope.component.hooks import getSiteManager

        self.patch_global(getSiteManager, return_value=site_manager_mock)

        # Pretend two FTIs are registered, both using common-factory
        site_manager_mock.registeredUtilities = Mock(
            return_value=[
                self.create_dummy(
                    provided=IFactory,
                    name="common-factory",
                    info="plone.dexterity.dynamic",
                ),
                self.create_dummy(
                    component=fti,
                    provided=IDexterityFTI,
                    name="testtype",
                    info="plone.dexterity.dynamic",
                ),
                self.create_dummy(
                    component=fti2,
                    provided=IDexterityFTI,
                    name="testtype2",
                    info="plone.dexterity.dynamic",
                ),
            ]
        )

        fti.factory = "new-factory"
        ftiModified(
            fti,
            ObjectModifiedEvent(
                fti, DexterityFTIModificationDescription("factory", "common-factory")
            ),
        )

        # We shouldn't remove this since fti2 still uses it
        self.assertFalse(site_manager_mock.unregisterUtility.called)

        # A new one may still be created, however
        self.assertEqual(
            site_manager_mock.registerUtility.call_args[0][2], "new-factory"
        )

    def test_deleted_factory_not_unregistered_if_not_unique(self):
        portal_type = "testtype"
        fti = DexterityFTI(portal_type, factory="common-factory")
        portal_type2 = "testtype2"
        fti2 = DexterityFTI(portal_type2, factory="common-factory")
        container_dummy = self.create_dummy()

        # Mock the lookup of the site and the site manager at the site root
        dummy_site = self.create_dummy()
        self.mock_utility(dummy_site, ISiteRoot)

        site_manager_mock = Mock(
            wraps=PersistentComponents(bases=(getGlobalSiteManager(),))
        )
        from zope.component.hooks import getSiteManager

        self.patch_global(getSiteManager, return_value=site_manager_mock)

        # Pretend two FTIs are registered, both using common-factory
        # NB: Assuming that "testtype" was already removed when this gets
        #     called
        site_manager_mock.registeredUtilities = Mock(
            return_value=[
                self.create_dummy(
                    provided=IFactory,
                    name="common-factory",
                    info="plone.dexterity.dynamic",
                ),
                self.create_dummy(
                    component=fti2,
                    provided=IDexterityFTI,
                    name="testtype2",
                    info="plone.dexterity.dynamic",
                ),
            ]
        )

        ftiRemoved(fti, ObjectRemovedEvent(fti, container_dummy, fti.getId()))

        # We shouldn't remove this since fti2 still uses it
        # The type itself should be removed though
        site_manager_mock.unregisterUtility.assert_called_once_with(
            provided=IDexterityFTI, name="testtype"
        )

    def test_loockup_schema_with_p_mtime_roundable(self):
        fti = DexterityMtimeFTI("testtype")
        fti.schema = None  # use dynamic schema
        # Set a roundable _p_mtime
        fti._p_mtime = 1637689348.9999528

        portal = self.create_dummy(getPhysicalPath=lambda: ("", "site"))
        self.mock_utility(portal, ISiteRoot)

        # Generated schema name must be this.
        schemaName = "site_5_1637689348_2_9999528_0_testtype"
        setattr(plone.dexterity.schema.generated, schemaName, ITestSchema)

        self.assertEqual(ITestSchema, fti.lookupSchema())

        # cleanup
        delattr(plone.dexterity.schema.generated, schemaName)

    def test_fti_modified_with_p_mtime_roundable(self):
        portal_type = "testtype"
        fti = DexterityMtimeFTI(portal_type)
        # Set a roundable _p_mtime
        fti._p_mtime = 1637689348.9999528

        class INew(Interface):
            title = zope.schema.TextLine(title="title")

        model_dummy = Model({"": INew})

        fti.lookupModel = Mock(return_value=model_dummy)
        self.create_dummy()

        site_dummy = self.create_dummy(getPhysicalPath=lambda: ("", "siteid"))
        self.mock_utility(site_dummy, ISiteRoot)

        class IBlank1(Interface):
            pass

        # Set source interface
        # Generated schema name must be this.
        schemaName = "siteid_5_1637689348_2_9999528_0_testtype"
        setattr(plone.dexterity.schema.generated, schemaName, IBlank1)

        # Sync this with schema
        ftiModified(
            fti,
            ObjectModifiedEvent(
                fti, DexterityFTIModificationDescription("model_file", "")
            ),
        )

        self.assertTrue("title" in IBlank1)
        self.assertTrue(IBlank1["title"].title == "title")

        # cleanup
        delattr(plone.dexterity.schema.generated, schemaName)
