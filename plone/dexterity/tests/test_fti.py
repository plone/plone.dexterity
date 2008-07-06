import unittest
import mocker
from plone.mocktestcase import MockTestCase

import os.path

from zope.interface import Interface
from zope.component import queryUtility, queryMultiAdapter

import zope.schema

from zope.component.interfaces import IFactory

from zope.component import getGlobalSiteManager
from zope.component.persistentregistry import PersistentComponents

from zope.interface.declarations import Implements

from zope.publisher.interfaces.browser import IBrowserView
from zope.publisher.interfaces.browser import IBrowserRequest

from zope.app.component.hooks import setSite, setHooks
from zope.app.container.interfaces import IAdding

from zope.lifecycleevent.interfaces import IObjectModifiedEvent
from zope.lifecycleevent import ObjectModifiedEvent

from zope.app.container.contained import ObjectMovedEvent
from zope.app.container.contained import ObjectAddedEvent
from zope.app.container.contained import ObjectRemovedEvent

from plone.dexterity.interfaces import IDexterityFTI

from plone.dexterity.fti import DexterityFTI
from plone.dexterity.fti import fti_added, fti_removed, fti_renamed, fti_modified

from plone.dexterity.factory import DexterityFactory

from plone.dexterity.browser.add import AddViewFactory

from plone.dexterity import utils
from plone.dexterity.tests.schemata import ITestSchema
from plone.dexterity.tests.schemata import ITaggedValueSchema
from plone.dexterity.tests.schemata import IDerivedFromTaggedValueSchema

from plone.supermodel.model import Model

from Products.CMFCore.interfaces import ISiteRoot

import plone.dexterity.schema.generated

class TestFTI(MockTestCase):

    def test_factory_name_is_fti_id(self):
        fti = DexterityFTI(u"testtype")
        self.assertEquals(u"testtype", fti.getId())
        self.assertEquals(u"testtype", fti.factory)
    
    def test_has_dynamic_schema(self):
        fti = DexterityFTI(u"testtype")
        fti.schema = u"dummy.schema"
        self.assertEquals(False, fti.has_dynamic_schema)
        fti.schema = None
        self.assertEquals(True, fti.has_dynamic_schema)
    
    def test_lookup_schema_with_concrete_schema(self):
        fti = DexterityFTI(u"testtype")
        fti.schema = u"plone.dexterity.tests.schemata.ITestSchema"
        self.assertEquals(ITestSchema, fti.lookup_schema())
        self.assertEquals(ITestSchema, fti.lookup_schema()) # second time uses _v attribute

    def test_lookup_schema_with_dynamic_schema(self):
        fti = DexterityFTI(u"testtype")
        fti.schema = None # use dynamic schema

        portal = self.create_dummy(getId=lambda:"site")
        self.mock_utility(portal, ISiteRoot)

        schema_name = utils.portal_type_to_schema_name(fti.getId())
        setattr(plone.dexterity.schema.generated, schema_name, ITestSchema)
        
        self.assertEquals(ITestSchema, fti.lookup_schema())
        
        # cleanup
        delattr(plone.dexterity.schema.generated, schema_name)

    def test_lookup_model_from_string(self):
        fti = DexterityFTI(u"testtype")
        fti.schema = None
        fti.model_source = "<model />"
        fti.model_file = None
        
        model_dummy = Model()
        
        load_string_mock = self.mocker.replace("plone.supermodel.load_string")
        self.expect(load_string_mock(fti.model_source, policy=u"dexterity")).result(model_dummy)
        
        self.replay()
        
        model = fti.lookup_model()
        self.assertIs(model_dummy, model)
    
    def test_lookup_model_from_file_with_package(self):
        
        fti = DexterityFTI(u"testtype")
        fti.schema = None
        fti.model_source = None
        fti.model_file = u"plone.dexterity.tests:test.xml"
        
        model_dummy = Model()
        
        import plone.dexterity.tests
        abs_file = os.path.join(os.path.split(plone.dexterity.tests.__file__)[0], "test.xml")
        
        load_file_mock = self.mocker.replace("plone.supermodel.load_file")
        self.expect(load_file_mock(abs_file, reload=True, policy=u"dexterity")).result(model_dummy)
        
        self.replay()
        
        model = fti.lookup_model()
        self.assertIs(model_dummy, model)
        
    def test_lookup_model_from_file_with_absolute_path(self):
        
        import plone.dexterity.tests
        abs_file = os.path.join(os.path.split(plone.dexterity.tests.__file__)[0], "test.xml")
        
        fti = DexterityFTI(u"testtype")
        fti.schema = None
        fti.model_source = None
        fti.model_file = abs_file
        
        model_dummy = Model()
        
        load_file_mock = self.mocker.replace("plone.supermodel.load_file")
        self.expect(load_file_mock(abs_file, reload=True, policy=u"dexterity")).result(model_dummy)
        
        self.replay()
        
        model = fti.lookup_model()
        self.assertIs(model_dummy, model)
    
    def test_lookup_model_from_file_with_win32_absolute_path(self):
        
        fti = DexterityFTI(u"testtype")
        fti.schema = None
        fti.model_source = None
        fti.model_file = r"C:\models\testmodel.xml"
        
        model_dummy = Model()
        
        isabs_mock = self.mocker.replace("os.path.isabs")
        self.expect(isabs_mock(fti.model_file)).result(True)
        
        isfile_mock = self.mocker.replace("os.path.isfile")
        self.expect(isfile_mock(fti.model_file)).result(True)
        
        load_file_mock = self.mocker.replace("plone.supermodel.load_file")
        self.expect(load_file_mock(fti.model_file, reload=True, policy=u"dexterity")).result(model_dummy)

        self.replay()
        
        model = fti.lookup_model()
        self.assertIs(model_dummy, model)

    def test_lookup_model_with_schema_only(self):
        fti = DexterityFTI(u"testtype")
        fti.schema = u"plone.dexterity.tests.schemata.ITestSchema"
        fti.model_source = None
        fti.model_file = None

        model = fti.lookup_model()
        self.assertEquals(1, len(model.schemata))
        self.assertEquals(ITestSchema, model.schema)
        self.assertEquals({}, model.metadata)

    def test_lookup_model_from_string_with_schema(self):
        fti = DexterityFTI(u"testtype")
        fti.schema = u"plone.dexterity.tests.schemata.ITestSchema" # effectively ignored
        fti.model_source = "<model />"
        fti.model_file = None
        
        model_dummy = Model()
        
        load_string_mock = self.mocker.replace("plone.supermodel.load_string")
        self.expect(load_string_mock(fti.model_source, policy=u"dexterity")).result(model_dummy)
        
        self.replay()
        
        model = fti.lookup_model()
        self.assertIs(model_dummy, model)
        self.assertIs(ITestSchema, fti.lookup_schema())

    def test_lookup_model_failure(self):
        fti = DexterityFTI(u"testtype")
        fti.schema = None
        fti.model_source = None
        fti.model_file = None
        
        self.assertRaises(ValueError, fti.lookup_model)
        
    def test_fires_modified_event_on_edit_properties(self):
        fti = DexterityFTI(u"testtype")
        
        notify_mock = self.mocker.replace('zope.event.notify')
        self.expect(notify_mock(self.match_provides(IObjectModifiedEvent)))
        
        self.replay()
        
        fti.manage_editProperties(REQUEST={})
        
    def test_fires_modified_event_on_change_properties(self):
        fti = DexterityFTI(u"testtype")
        
        notify_mock = self.mocker.replace('zope.event.notify')
        self.expect(notify_mock(self.match_provides(IObjectModifiedEvent)))
        
        self.replay()
        
        fti.manage_changeProperties()
        
    def test_checks_permission_in_is_construction_allowed_true(self):
        fti = DexterityFTI(u"testtype")
        fti.add_permission = "Some add permission"
        container_dummy = self.create_dummy()
        
        security_manager_mock = self.mocker.mock()
        self.expect(security_manager_mock.checkPermission("Some add permission", container_dummy)).result(True)
        
        getSecurityManager_mock = self.mocker.replace('AccessControl.getSecurityManager')
        self.expect(getSecurityManager_mock()).result(security_manager_mock)
        
        self.replay()
        
        self.assertEquals(True, fti.isConstructionAllowed(container_dummy))
    
    def test_checks_permission_in_is_construction_allowed_false(self):
        fti = DexterityFTI(u"testtype")
        fti.add_permission = "Some add permission"
        container_dummy = self.create_dummy()
        
        security_manager_mock = self.mocker.mock()
        self.expect(security_manager_mock.checkPermission("Some add permission", container_dummy)).result(False)
        
        getSecurityManager_mock = self.mocker.replace('AccessControl.getSecurityManager')
        self.expect(getSecurityManager_mock()).result(security_manager_mock)
        
        self.replay()
        
        self.assertEquals(False, fti.isConstructionAllowed(container_dummy))
    
    def test_no_permission_means_no_construction(self):
        fti = DexterityFTI(u"testtype")
        fti.add_permission = None
        container_dummy = self.create_dummy()
        self.assertEquals(False, fti.isConstructionAllowed(container_dummy))
    
class TestFTIEvents(MockTestCase):

    # These tests are a bit verbose, but the basic premise is pretty simple.
    # We create a proxy mock of a PersistentComponents() registry, and
    # use this for mock assertions as well as to verify that the right 
    # components really do get added/removed (using passthrough).
    
    def test_components_registered_on_add(self):
        portal_type = u"testtype"
        fti = DexterityFTI(portal_type)
        container_dummy = self.create_dummy()
        
        # Mock the lookup of the site and the site manager at the site root
        dummy_site = self.create_dummy()
        self.mock_utility(dummy_site, ISiteRoot)
        
        site_manager_mock = self.mocker.proxy(PersistentComponents(bases=(getGlobalSiteManager(),)))
        getSiteManager_mock = self.mocker.replace('zope.app.component.hooks.getSiteManager')
        self.expect(getSiteManager_mock(dummy_site)).result(site_manager_mock)
        
        # We expect that no components are registered , so look for all registrations
        self.expect(site_manager_mock.registerUtility(fti, IDexterityFTI, portal_type)).passthrough()
        self.expect(site_manager_mock.registerUtility(
                    mocker.MATCH(lambda x: isinstance(x, DexterityFactory) and x.portal_type == portal_type), 
                    IFactory, portal_type)).passthrough()
        self.expect(site_manager_mock.registerAdapter(
                    factory=mocker.MATCH(lambda x: isinstance(x, AddViewFactory) and x.portal_type == portal_type),
                    provided=IBrowserView,
                    required=(IAdding, IBrowserRequest),
                    name=portal_type,)).passthrough()
        
        self.replay()
        
        fti_added(fti, ObjectAddedEvent(fti, container_dummy, fti.getId()))
        
        site_dummy = self.create_dummy(getSiteManager = lambda: site_manager_mock)
        setSite(site_dummy)
        setHooks()
        
        self.assertNotEquals(None, queryUtility(IDexterityFTI, name=portal_type))
        self.assertNotEquals(None, queryUtility(IFactory, name=portal_type))
        self.assertNotEquals(None, site_manager_mock.adapters.lookup((Implements(IAdding), Implements(IBrowserRequest)), IBrowserView, name=portal_type))
    
    def test_components_not_registered_on_add_if_exist(self):
        portal_type = u"testtype"
        fti = DexterityFTI(portal_type)
        container_dummy = self.create_dummy()
        addview_dummy = self.create_dummy()
        
        # Mock the lookup of the site and the site manager at the site root
        dummy_site = self.create_dummy()
        self.mock_utility(dummy_site, ISiteRoot)
        
        site_manager_mock = self.mocker.proxy(PersistentComponents(bases=(getGlobalSiteManager(),)))
        getSiteManager_mock = self.mocker.replace('zope.app.component.hooks.getSiteManager')
        self.expect(getSiteManager_mock(dummy_site)).result(site_manager_mock)

        # Register FTI utility, factory utility and addview
        
        self.mock_utility(fti, IDexterityFTI, name=portal_type)
        self.mock_utility(DexterityFactory(portal_type), IFactory, name=portal_type)
        self.mock_adapter(addview_dummy, IBrowserView, (IAdding, IBrowserRequest,), name=portal_type)
        
        # We expect that all components are registered, so do not expect any registrations
        
        self.expect(site_manager_mock.registerUtility(fti, IDexterityFTI, portal_type)).passthrough().count(0)
        self.expect(site_manager_mock.registerUtility(
                    mocker.MATCH(lambda x: isinstance(x, DexterityFactory) and x.portal_type == portal_type), 
                    IFactory, portal_type)).passthrough().count(0)
        self.expect(site_manager_mock.registerAdapter(
                    factory=mocker.MATCH(lambda x: isinstance(x, AddViewFactory) and x.portal_type == portal_type),
                    provided=IBrowserView,
                    required=(IAdding, IBrowserRequest),
                    name=portal_type,)).passthrough().count(0)
        
        self.replay()
        
        fti_added(fti, ObjectAddedEvent(fti, container_dummy, fti.getId()))
    
    def test_addview_not_registered_on_add_if_addview_registered_providing_interface(self):
        portal_type = u"testtype"
        fti = DexterityFTI(portal_type)
        container_dummy = self.create_dummy()
        addview_dummy = self.create_dummy()
        
        # Mock the lookup of the site and the site manager at the site root
        dummy_site = self.create_dummy()
        self.mock_utility(dummy_site, ISiteRoot)
        
        site_manager_mock = self.mocker.proxy(PersistentComponents(bases=(getGlobalSiteManager(),)))
        getSiteManager_mock = self.mocker.replace('zope.app.component.hooks.getSiteManager')
        self.expect(getSiteManager_mock(dummy_site)).result(site_manager_mock)

        # Register addview - others we'll still expect as local components
        
        self.mock_adapter(addview_dummy, Interface, (IAdding, IBrowserRequest,), name=portal_type)
        
        # We expect that all components are registered, so do not expect any registrations
        
        self.expect(site_manager_mock.registerUtility(fti, IDexterityFTI, portal_type)).passthrough()
        self.expect(site_manager_mock.registerUtility(
                    mocker.MATCH(lambda x: isinstance(x, DexterityFactory) and x.portal_type == portal_type), 
                    IFactory, portal_type)).passthrough()
        self.expect(site_manager_mock.registerAdapter(
                    factory=mocker.MATCH(lambda x: isinstance(x, AddViewFactory) and x.portal_type == portal_type),
                    provided=IBrowserView,
                    required=(IAdding, IBrowserRequest),
                    name=portal_type,)).passthrough().count(0)
        
        self.replay()
        
        fti_added(fti, ObjectAddedEvent(fti, container_dummy, fti.getId()))

    def test_components_unregistered_on_delete(self):
        portal_type = u"testtype"
        fti = DexterityFTI(portal_type)
        container_dummy = self.create_dummy()
        
        # Mock the lookup of the site and the site manager at the site root
        dummy_site = self.create_dummy()
        self.mock_utility(dummy_site, ISiteRoot)
        
        site_manager_mock = self.mocker.proxy(PersistentComponents(bases=(getGlobalSiteManager(),)))
        getSiteManager_mock = self.mocker.replace('zope.app.component.hooks.getSiteManager')
        self.expect(getSiteManager_mock(dummy_site)).result(site_manager_mock).count(1,None)
        
        # We expect to always be able to unregister without error, even if the
        # components do not exists (as here)
        
        self.expect(site_manager_mock.unregisterUtility(provided=IDexterityFTI, name=portal_type)).passthrough()
        self.expect(site_manager_mock.unregisterUtility(provided=IFactory, name=portal_type)).passthrough()
        self.expect(site_manager_mock.unregisterAdapter(provided=IBrowserView, required=(IAdding, IBrowserRequest), name=portal_type)).passthrough()
        
        self.replay()
        
        # First add the components
        fti_added(fti, ObjectAddedEvent(fti, container_dummy, fti.getId()))
        
        # Then remove them again
        fti_removed(fti, ObjectRemovedEvent(fti, container_dummy, fti.getId()))
        
        site_dummy = self.create_dummy(getSiteManager = lambda: site_manager_mock)
        setSite(site_dummy)
        setHooks()
        
        self.assertEquals(None, queryUtility(IDexterityFTI, name=portal_type))
        self.assertEquals(None, queryUtility(IFactory, name=portal_type))
        self.assertEquals(None, site_manager_mock.adapters.lookup((Implements(IAdding), Implements(IBrowserRequest)), IBrowserView, name=portal_type))

    def test_components_unregistered_on_delete_does_not_error_with_no_components(self):
        portal_type = u"testtype"
        fti = DexterityFTI(portal_type)
        container_dummy = self.create_dummy()
        
        # Mock the lookup of the site and the site manager at the site root
        dummy_site = self.create_dummy()
        self.mock_utility(dummy_site, ISiteRoot)
        
        site_manager_mock = self.mocker.proxy(PersistentComponents(bases=(getGlobalSiteManager(),)))
        getSiteManager_mock = self.mocker.replace('zope.app.component.hooks.getSiteManager')
        self.expect(getSiteManager_mock(dummy_site)).result(site_manager_mock)
        
        # We expect to always be able to unregister without error, even if the
        # components do not exists (as here)
        
        self.expect(site_manager_mock.unregisterUtility(provided=IDexterityFTI, name=portal_type)).passthrough()
        self.expect(site_manager_mock.unregisterUtility(provided=IFactory, name=portal_type)).passthrough()
        self.expect(site_manager_mock.unregisterAdapter(provided=IBrowserView, required=(IAdding, IBrowserRequest), name=portal_type)).passthrough()
        
        self.replay()
        
        fti_removed(fti, ObjectRemovedEvent(fti, container_dummy, fti.getId()))
    
    def test_global_components_not_unregistered_on_delete(self):
        portal_type = u"testtype"
        fti = DexterityFTI(portal_type)
        container_dummy = self.create_dummy()
        addview_dummy = self.create_dummy()
        
        # Mock the lookup of the site and the site manager at the site root
        dummy_site = self.create_dummy()
        self.mock_utility(dummy_site, ISiteRoot)
        
        site_manager_mock = self.mocker.proxy(PersistentComponents(bases=(getGlobalSiteManager(),)))
        getSiteManager_mock = self.mocker.replace('zope.app.component.hooks.getSiteManager')
        self.expect(getSiteManager_mock(dummy_site)).result(site_manager_mock)
        
        # Register FTI utility, factory utility and addview
        
        self.mock_utility(fti, IDexterityFTI, name=portal_type)
        self.mock_utility(DexterityFactory(portal_type), IFactory, name=portal_type)
        self.mock_adapter(addview_dummy, IBrowserView, (IAdding, IBrowserRequest,), name=portal_type)
        
        # We expect to always be able to unregister without error, even if the
        # component exists
        
        self.expect(site_manager_mock.unregisterUtility(provided=IDexterityFTI, name=portal_type)).passthrough()
        self.expect(site_manager_mock.unregisterUtility(provided=IFactory, name=portal_type)).passthrough()
        self.expect(site_manager_mock.unregisterAdapter(provided=IBrowserView, required=(IAdding, IBrowserRequest), name=portal_type)).passthrough()
        
        self.replay()
        
        fti_removed(fti, ObjectRemovedEvent(fti, container_dummy, fti.getId()))
        
        site_dummy = self.create_dummy(getSiteManager = lambda: site_manager_mock)
        setSite(site_dummy)
        setHooks()
        
        self.assertNotEquals(None, queryUtility(IDexterityFTI, name=portal_type))
        self.assertNotEquals(None, queryUtility(IFactory, name=portal_type))
        self.assertNotEquals(None, getGlobalSiteManager().adapters.lookup((Implements(IAdding), Implements(IBrowserRequest)), IBrowserView, name=portal_type))
    
    def test_components_reregistered_on_rename(self):
        portal_type = u"testtype"
        fti = DexterityFTI(portal_type)
        container_dummy = self.create_dummy()
        
        # Mock the lookup of the site and the site manager at the site root
        dummy_site = self.create_dummy()
        self.mock_utility(dummy_site, ISiteRoot)
        
        site_manager_mock = self.mocker.proxy(PersistentComponents(bases=(getGlobalSiteManager(),)))
        getSiteManager_mock = self.mocker.replace('zope.app.component.hooks.getSiteManager')
        self.expect(getSiteManager_mock(dummy_site)).result(site_manager_mock).count(1,None)
        
        # First look for unregistration of all local components
        
        self.expect(site_manager_mock.unregisterUtility(provided=IDexterityFTI, name=portal_type)).passthrough()
        self.expect(site_manager_mock.unregisterUtility(provided=IFactory, name=portal_type)).passthrough()
        self.expect(site_manager_mock.unregisterAdapter(provided=IBrowserView, required=(IAdding, IBrowserRequest), name=portal_type)).passthrough()
        
        # Then look for re-registration of global components
        self.expect(site_manager_mock.registerUtility(fti, IDexterityFTI, portal_type)).passthrough()
        self.expect(site_manager_mock.registerUtility(
                    mocker.MATCH(lambda x: isinstance(x, DexterityFactory) and x.portal_type == portal_type), 
                    IFactory, portal_type)).passthrough()
        self.expect(site_manager_mock.registerAdapter(
                    factory=mocker.MATCH(lambda x: isinstance(x, AddViewFactory) and x.portal_type == portal_type),
                    provided=IBrowserView,
                    required=(IAdding, IBrowserRequest),
                    name=portal_type,)).passthrough()
        
        self.replay()
        
        fti_renamed(fti, ObjectMovedEvent(fti, container_dummy, fti.getId(), container_dummy, u"newtype"))
        
        site_dummy = self.create_dummy(getSiteManager = lambda: site_manager_mock)
        setSite(site_dummy)
        setHooks()
        
        self.assertNotEquals(None, queryUtility(IDexterityFTI, name=portal_type))
        self.assertNotEquals(None, queryUtility(IFactory, name=portal_type))
        self.assertNotEquals(None, site_manager_mock.adapters.lookup((Implements(IAdding), Implements(IBrowserRequest)), IBrowserView, name=portal_type))
        
    def test_dynamic_schema_refreshed_on_modify(self):
        portal_type = u"testtype"
        fti = self.mocker.proxy(DexterityFTI(portal_type))
        
        class INew(Interface):
            title = zope.schema.TextLine(title=u"title")
        
        model_dummy = Model({u"": INew})
        
        self.expect(fti.lookup_model()).result(model_dummy)
        container_dummy = self.create_dummy()
        
        site_dummy = self.create_dummy(getId = lambda: "site")
        self.mock_utility(site_dummy, ISiteRoot)
        
        class IBlank(Interface):
            pass
        
        
        self.replay()
        
        # Set source interface
        schema_name = utils.portal_type_to_schema_name(fti.getId())
        setattr(plone.dexterity.schema.generated, schema_name, IBlank)
                
        # Sync this with schema
        fti_modified(fti, ObjectModifiedEvent(fti))
        
        self.failUnless('title' in IBlank)
        self.failUnless(IBlank['title'].title == u"title")
        
    def test_concrete_schema_not_refreshed_on_modify(self):
        portal_type = u"testtype"
        fti = self.mocker.proxy(DexterityFTI(portal_type))
        
        class IBlank(Interface):
            pass
        
        class INew(Interface):
            title = zope.schema.TextLine(title=u"title")
        
        model_dummy = Model({u"": INew})
        self.expect(fti.lookup_model()).result(model_dummy).count(0, None)
        container_dummy = self.create_dummy()
        
        site_dummy = self.create_dummy(getId = lambda: "site")
        self.mock_utility(site_dummy, ISiteRoot)
        
        self.replay()
        
        # Set schema to something so that has_dynamic_schema is false
        fti.schema = IBlank.__identifier__
        assert not fti.has_dynamic_schema
        
        # Set source for dynamic FTI - should not be used
        schema_name = utils.portal_type_to_schema_name(fti.getId())
        setattr(plone.dexterity.schema.generated, schema_name, IBlank)
                
        # Sync should not happen now
        
        fti_modified(fti, ObjectModifiedEvent(fti))
        
        self.failIf('title' in IBlank)
    
def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestFTI))
    suite.addTest(unittest.makeSuite(TestFTIEvents))
    return suite
