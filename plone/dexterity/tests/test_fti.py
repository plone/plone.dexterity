import unittest
import mocker
from plone.mocktestcase import MockTestCase

import os.path

from zope.interface import Interface
from zope.component import queryUtility

from zope.security.interfaces import IPermission

import zope.schema

from zope.component.interfaces import IFactory

from zope.component import getGlobalSiteManager
from zope.component.persistentregistry import PersistentComponents

from zope.app.component.hooks import setSite, setHooks

from zope.lifecycleevent.interfaces import IObjectModifiedEvent
from zope.lifecycleevent import ObjectModifiedEvent

from zope.app.container.contained import ObjectMovedEvent
from zope.app.container.contained import ObjectAddedEvent
from zope.app.container.contained import ObjectRemovedEvent

from plone.dexterity.interfaces import IDexterityFTI

from plone.dexterity.fti import DexterityFTI, DexterityFTIModificationDescription
from plone.dexterity.fti import ftiAdded, ftiRemoved, ftiRenamed, ftiModified

from plone.dexterity.factory import DexterityFactory

from plone.dexterity import utils
from plone.dexterity.tests.schemata import ITestSchema

from plone.supermodel.model import Model

from Products.CMFCore.interfaces import ISiteRoot

import plone.dexterity.schema.generated

class TestClass(object):
    meta_type = "Test Class"

class TestClass2(object):
    meta_type = "Test Class 2"


class TestFTI(MockTestCase):

    def test_factory_name_is_fti_id(self):
        fti = DexterityFTI(u"testtype")
        self.assertEquals(u"testtype", fti.getId())
        self.assertEquals(u"testtype", fti.factory)
    
    def test_hasDynamicSchema(self):
        fti = DexterityFTI(u"testtype")
        fti.schema = u"dummy.schema"
        self.assertEquals(False, fti.hasDynamicSchema)
        fti.schema = None
        self.assertEquals(True, fti.hasDynamicSchema)
    
    def test_lookupSchema_with_concrete_schema(self):
        fti = DexterityFTI(u"testtype")
        fti.schema = u"plone.dexterity.tests.schemata.ITestSchema"
        self.assertEquals(ITestSchema, fti.lookupSchema())
        self.assertEquals(ITestSchema, fti.lookupSchema()) # second time uses _v attribute

    def test_lookupSchema_with_dynamic_schema(self):
        fti = DexterityFTI(u"testtype")
        fti.schema = None # use dynamic schema

        portal = self.create_dummy(getPhysicalPath=lambda:('', 'site'))
        self.mock_utility(portal, ISiteRoot)

        schemaName = utils.portalTypeToSchemaName(fti.getId())
        setattr(plone.dexterity.schema.generated, schemaName, ITestSchema)
        
        self.assertEquals(ITestSchema, fti.lookupSchema())
        
        # cleanup
        delattr(plone.dexterity.schema.generated, schemaName)

    def test_lookupModel_from_string(self):
        fti = DexterityFTI(u"testtype")
        fti.schema = None
        fti.model_source = "<model />"
        fti.model_file = None
        
        model_dummy = Model()
        
        loadString_mock = self.mocker.replace("plone.supermodel.loadString")
        self.expect(loadString_mock(fti.model_source, policy=u"dexterity")).result(model_dummy)
        
        self.replay()
        
        model = fti.lookupModel()
        self.assertIs(model_dummy, model)
    
    def test_lookupModel_from_file_with_package(self):
        
        fti = DexterityFTI(u"testtype")
        fti.schema = None
        fti.model_source = None
        fti.model_file = u"plone.dexterity.tests:test.xml"
        
        model_dummy = Model()
        
        import plone.dexterity.tests
        abs_file = os.path.join(os.path.split(plone.dexterity.tests.__file__)[0], "test.xml")
        
        loadFile_mock = self.mocker.replace("plone.supermodel.loadFile")
        self.expect(loadFile_mock(abs_file, reload=True, policy=u"dexterity")).result(model_dummy)
        
        self.replay()
        
        model = fti.lookupModel()
        self.assertIs(model_dummy, model)
        
    def test_lookupModel_from_file_with_absolute_path(self):
        
        import plone.dexterity.tests
        abs_file = os.path.join(os.path.split(plone.dexterity.tests.__file__)[0], "test.xml")
        
        fti = DexterityFTI(u"testtype")
        fti.schema = None
        fti.model_source = None
        fti.model_file = abs_file
        
        model_dummy = Model()
        
        loadFile_mock = self.mocker.replace("plone.supermodel.loadFile")
        self.expect(loadFile_mock(abs_file, reload=True, policy=u"dexterity")).result(model_dummy)
        
        self.replay()
        
        model = fti.lookupModel()
        self.assertIs(model_dummy, model)
    
    def test_lookupModel_from_file_with_win32_absolute_path(self):
        
        fti = DexterityFTI(u"testtype")
        fti.schema = None
        fti.model_source = None
        fti.model_file = r"C:\models\testmodel.xml"
        
        model_dummy = Model()
        
        isabs_mock = self.mocker.replace("os.path.isabs")
        self.expect(isabs_mock(fti.model_file)).result(True)
        
        isfile_mock = self.mocker.replace("os.path.isfile")
        self.expect(isfile_mock(fti.model_file)).result(True)
        
        loadFile_mock = self.mocker.replace("plone.supermodel.loadFile")
        self.expect(loadFile_mock(fti.model_file, reload=True, policy=u"dexterity")).result(model_dummy)

        self.replay()
        
        model = fti.lookupModel()
        self.assertIs(model_dummy, model)

    def test_lookupModel_with_schema_only(self):
        fti = DexterityFTI(u"testtype")
        fti.schema = u"plone.dexterity.tests.schemata.ITestSchema"
        fti.model_source = None
        fti.model_file = None

        model = fti.lookupModel()
        self.assertEquals(1, len(model.schemata))
        self.assertEquals(ITestSchema, model.schema)

    def test_lookupModel_from_string_with_schema(self):
        fti = DexterityFTI(u"testtype")
        fti.schema = u"plone.dexterity.tests.schemata.ITestSchema" # effectively ignored
        fti.model_source = "<model />"
        fti.model_file = None
        
        model_dummy = Model()
        
        loadString_mock = self.mocker.replace("plone.supermodel.loadString")
        self.expect(loadString_mock(fti.model_source, policy=u"dexterity")).result(model_dummy)
        
        self.replay()
        
        model = fti.lookupModel()
        self.assertIs(model_dummy, model)
        self.assertIs(ITestSchema, fti.lookupSchema())

    def test_lookupModel_failure(self):
        fti = DexterityFTI(u"testtype")
        fti.schema = None
        fti.model_source = None
        fti.model_file = None
        
        self.assertRaises(ValueError, fti.lookupModel)
    
    
    def test_fires_modified_event_on_update_property_if_changed(self):
        fti = DexterityFTI(u"testtype")
        
        fti.title = u"Old title"
        fti.global_allow = False
        
        notify_mock = self.mocker.replace('zope.event.notify')
        self.expect(notify_mock(mocker.MATCH(lambda x: IObjectModifiedEvent.providedBy(x) \
                                                        and len(x.descriptions) == 1 \
                                                        and x.descriptions[0].attribute == 'title' \
                                                        and x.descriptions[0].oldValue == "Old title")))
        
        self.replay()
        
        fti._updateProperty('title', "New title") # fires event caught above
        fti._updateProperty('allow_discussion', False) # does not fire
            
    def test_fires_modified_event_on_change_properties_per_changed_property(self):
        fti = DexterityFTI(u"testtype")
        fti.title = "Old title"
        fti.allow_discussion = False
        fti.global_allow = True
        
        notify_mock = self.mocker.replace('zope.event.notify')
        self.expect(notify_mock(mocker.MATCH(lambda x: IObjectModifiedEvent.providedBy(x) \
                                                        and len(x.descriptions) == 1 \
                                                        and x.descriptions[0].attribute == 'title' \
                                                        and x.descriptions[0].oldValue == "Old title")))
                                                        
        self.expect(notify_mock(mocker.MATCH(lambda x: IObjectModifiedEvent.providedBy(x) \
                                                        and len(x.descriptions) == 1 \
                                                        and x.descriptions[0].attribute == 'global_allow' \
                                                        and x.descriptions[0].oldValue == True)))
        self.replay()
        
        fti.manage_changeProperties(title="New title", allow_discussion=False, global_allow=False)

    def test_checks_permission_in_is_construction_allowed_true(self):
        fti = DexterityFTI(u"testtype")
        fti.add_permission = "demo.Permission"
        container_dummy = self.create_dummy()
        
        permission_dummy = self.create_dummy()
        permission_dummy.id = 'demo.Permission'
        permission_dummy.title = 'Some add permission'
        
        self.mock_utility(permission_dummy, IPermission, name=u"demo.Permission")
        
        security_manager_mock = self.mocker.mock() 
        self.expect(security_manager_mock.checkPermission("Some add permission", container_dummy)).result(True) 
         
        getSecurityManager_mock = self.mocker.replace('AccessControl.getSecurityManager') 
        self.expect(getSecurityManager_mock()).result(security_manager_mock) 
        
        self.replay()
        
        self.assertEquals(True, fti.isConstructionAllowed(container_dummy))
    
    def test_checks_permission_in_is_construction_allowed_false(self):
        fti = DexterityFTI(u"testtype")
        fti.add_permission = "demo.Permission"
        container_dummy = self.create_dummy()
        
        permission_dummy = self.create_dummy()
        permission_dummy.id = 'demo.Permission'
        permission_dummy.title = 'Some add permission'
        
        self.mock_utility(permission_dummy, IPermission, name=u"demo.Permission")
        
        security_manager_mock = self.mocker.mock() 
        self.expect(security_manager_mock.checkPermission("Some add permission", container_dummy)).result(False) 
         
        getSecurityManager_mock = self.mocker.replace('AccessControl.getSecurityManager') 
        self.expect(getSecurityManager_mock()).result(security_manager_mock) 
        
        self.replay()
        
        self.assertEquals(False, fti.isConstructionAllowed(container_dummy))
    
    def test_no_permission_utility_means_no_construction(self):
        fti = DexterityFTI(u"testtype")
        fti.add_permission = 'demo.Permission' # not an IPermission utility
        container_dummy = self.create_dummy()
        self.assertEquals(False, fti.isConstructionAllowed(container_dummy))
    
    def test_no_permission_means_no_construction(self):
        fti = DexterityFTI(u"testtype")
        fti.add_permission = None
        container_dummy = self.create_dummy()
        self.assertEquals(False, fti.isConstructionAllowed(container_dummy))
    
    def test_add_view_url_set_on_creation(self):
        fti = DexterityFTI(u"testtype")
        self.assertEquals('string:${folder_url}/++add++testtype', fti.add_view_expr)

    def test_factory_set_on_creation(self):
        fti = DexterityFTI(u"testtype")
        self.assertEquals('testtype', fti.factory)

    def test_addview_and_factory_not_overridden_on_creation(self):
        fti = DexterityFTI(u"testtype",
                           add_view_expr="string:${folder_url}/@@my-addview",
                           factory="my.factory")
        self.assertEquals('string:${folder_url}/@@my-addview', fti.add_view_expr)
        self.assertEquals('my.factory', fti.factory)
    
    def test_meta_type(self):
        fti = DexterityFTI(u"testtype", klass="plone.dexterity.tests.test_fti.TestClass")
        self.assertEquals(TestClass.meta_type, fti.Metatype())
    
    def test_meta_type_change_class(self):
        fti = DexterityFTI(u"testtype", klass="plone.dexterity.tests.test_fti.TestClass")
        fti._updateProperty('klass', "plone.dexterity.tests.test_fti.TestClass2")
        self.assertEquals(TestClass2.meta_type, fti.Metatype())
    
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
        self.expect(site_manager_mock.registerUtility(fti, IDexterityFTI, portal_type, info='plone.dexterity.dynamic')).passthrough()
        self.expect(site_manager_mock.registerUtility(
                    mocker.MATCH(lambda x: isinstance(x, DexterityFactory) and x.portal_type == portal_type), 
                    IFactory, portal_type, info='plone.dexterity.dynamic')).passthrough()

        self.replay()
        
        ftiAdded(fti, ObjectAddedEvent(fti, container_dummy, fti.getId()))
        
        site_dummy = self.create_dummy(getSiteManager = lambda: site_manager_mock)
        setSite(site_dummy)
        setHooks()
        
        self.assertNotEquals(None, queryUtility(IDexterityFTI, name=portal_type))
        self.assertNotEquals(None, queryUtility(IFactory, name=portal_type))
    
    def test_components_not_registered_on_add_if_exist(self):
        portal_type = u"testtype"
        fti = DexterityFTI(portal_type)
        container_dummy = self.create_dummy()
        
        # Mock the lookup of the site and the site manager at the site root
        dummy_site = self.create_dummy()
        self.mock_utility(dummy_site, ISiteRoot)
        
        site_manager_mock = self.mocker.proxy(PersistentComponents(bases=(getGlobalSiteManager(),)))
        getSiteManager_mock = self.mocker.replace('zope.app.component.hooks.getSiteManager')
        self.expect(getSiteManager_mock(dummy_site)).result(site_manager_mock)

        # Register FTI utility and factory utility
        
        self.mock_utility(fti, IDexterityFTI, name=portal_type)
        self.mock_utility(DexterityFactory(portal_type), IFactory, name=portal_type)
        
        # We expect that all components are registered, so do not expect any registrations
        
        self.expect(site_manager_mock.registerUtility(fti, IDexterityFTI, portal_type)).passthrough().count(0)
        self.expect(site_manager_mock.registerUtility(
                    mocker.MATCH(lambda x: isinstance(x, DexterityFactory) and x.portal_type == portal_type), 
                    IFactory, portal_type)).passthrough().count(0)
        
        self.replay()
        
        ftiAdded(fti, ObjectAddedEvent(fti, container_dummy, fti.getId()))

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
        
        self.replay()
        
        # First add the components
        ftiAdded(fti, ObjectAddedEvent(fti, container_dummy, fti.getId()))
        
        # Then remove them again
        ftiRemoved(fti, ObjectRemovedEvent(fti, container_dummy, fti.getId()))
        
        site_dummy = self.create_dummy(getSiteManager = lambda: site_manager_mock)
        setSite(site_dummy)
        setHooks()
        
        self.assertEquals(None, queryUtility(IDexterityFTI, name=portal_type))
        self.assertEquals(None, queryUtility(IFactory, name=portal_type))

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
        
        self.replay()
        
        ftiRemoved(fti, ObjectRemovedEvent(fti, container_dummy, fti.getId()))
    
    def test_global_components_not_unregistered_on_delete(self):
        portal_type = u"testtype"
        fti = DexterityFTI(portal_type)
        container_dummy = self.create_dummy()
        
        # Mock the lookup of the site and the site manager at the site root
        dummy_site = self.create_dummy()
        self.mock_utility(dummy_site, ISiteRoot)
        
        site_manager_mock = self.mocker.proxy(PersistentComponents(bases=(getGlobalSiteManager(),)))
        getSiteManager_mock = self.mocker.replace('zope.app.component.hooks.getSiteManager')
        self.expect(getSiteManager_mock(dummy_site)).result(site_manager_mock)
        
        # Register FTI utility and factory utility
        
        self.mock_utility(fti, IDexterityFTI, name=portal_type)
        self.mock_utility(DexterityFactory(portal_type), IFactory, name=portal_type)
        
        # We expect to always be able to unregister without error, even if the
        # component exists. The factory is only unregistered if it was registered
        # with info='plone.dexterity.dynamic'.
        
        self.expect(site_manager_mock.unregisterUtility(provided=IDexterityFTI, name=portal_type)).passthrough()
        

        self.replay()
        
        ftiRemoved(fti, ObjectRemovedEvent(fti, container_dummy, fti.getId()))
        
        site_dummy = self.create_dummy(getSiteManager = lambda: site_manager_mock)
        setSite(site_dummy)
        setHooks()
        
        self.assertNotEquals(None, queryUtility(IDexterityFTI, name=portal_type))
        self.assertNotEquals(None, queryUtility(IFactory, name=portal_type))
    
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
        
        # Then look for re-registration of global components
        self.expect(site_manager_mock.registerUtility(fti, IDexterityFTI, portal_type, info='plone.dexterity.dynamic')).passthrough()
        self.expect(site_manager_mock.registerUtility(
                    mocker.MATCH(lambda x: isinstance(x, DexterityFactory) and x.portal_type == portal_type), 
                    IFactory, portal_type, info='plone.dexterity.dynamic')).passthrough()

        self.assertEquals('string:${folder_url}/++add++testtype', fti.add_view_expr)

        self.replay()
        
        ftiRenamed(fti, ObjectMovedEvent(fti, container_dummy, fti.getId(), container_dummy, u"newtype"))
        
        site_dummy = self.create_dummy(getSiteManager = lambda: site_manager_mock)
        setSite(site_dummy)
        setHooks()
        
        self.assertNotEquals(None, queryUtility(IDexterityFTI, name=portal_type))
        self.assertNotEquals(None, queryUtility(IFactory, name=portal_type))
     
    def test_dynamic_schema_refreshed_on_modify_model_file(self):
        portal_type = u"testtype"
        fti = self.mocker.proxy(DexterityFTI(portal_type))
        
        class INew(Interface):
            title = zope.schema.TextLine(title=u"title")
        
        model_dummy = Model({u"": INew})
        
        self.expect(fti.lookupModel()).result(model_dummy)
        self.create_dummy()
        
        site_dummy = self.create_dummy(getPhysicalPath = lambda: ('', 'siteid'))
        self.mock_utility(site_dummy, ISiteRoot)
        
        class IBlank(Interface):
            pass
        
        self.replay()
        
        # Set source interface
        schemaName = utils.portalTypeToSchemaName(fti.getId())
        setattr(plone.dexterity.schema.generated, schemaName, IBlank)
                
        # Sync this with schema
        ftiModified(fti, ObjectModifiedEvent(fti, DexterityFTIModificationDescription('model_file', '')))
        
        self.failUnless('title' in IBlank)
        self.failUnless(IBlank['title'].title == u"title")
    
    def test_dynamic_schema_refreshed_on_modify_model_source(self):
        portal_type = u"testtype"
        fti = self.mocker.proxy(DexterityFTI(portal_type))
        
        class INew(Interface):
            title = zope.schema.TextLine(title=u"title")
        
        model_dummy = Model({u"": INew})
        
        self.expect(fti.lookupModel()).result(model_dummy)
        self.create_dummy()
        
        site_dummy = self.create_dummy(getPhysicalPath = lambda: ('', 'siteid'))
        self.mock_utility(site_dummy, ISiteRoot)
        
        class IBlank(Interface):
            pass
        
        self.replay()
        
        # Set source interface
        schemaName = utils.portalTypeToSchemaName(fti.getId())
        setattr(plone.dexterity.schema.generated, schemaName, IBlank)
                
        # Sync this with schema
        ftiModified(fti, ObjectModifiedEvent(fti, DexterityFTIModificationDescription('model_source', '')))
        
        self.failUnless('title' in IBlank)
        self.failUnless(IBlank['title'].title == u"title")
        
    def test_concrete_schema_not_refreshed_on_modify_schema(self):
        portal_type = u"testtype"
        fti = self.mocker.proxy(DexterityFTI(portal_type))
        
        class IBlank(Interface):
            pass
        
        class INew(Interface):
            title = zope.schema.TextLine(title=u"title")
        
        model_dummy = Model({u"": INew})
        self.expect(fti.lookupModel()).result(model_dummy).count(0, None)
        self.create_dummy()
        
        site_dummy = self.create_dummy(getPhysicalPath = lambda: ('', 'siteid'))
        self.mock_utility(site_dummy, ISiteRoot)
        
        self.replay()
        
        # Set schema to something so that hasDynamicSchema is false
        fti.schema = IBlank.__identifier__
        assert not fti.hasDynamicSchema
        
        # Set source for dynamic FTI - should not be used
        schemaName = utils.portalTypeToSchemaName(fti.getId())
        setattr(plone.dexterity.schema.generated, schemaName, IBlank)
                
        # Sync should not happen now
        
        ftiModified(fti, ObjectModifiedEvent(fti, DexterityFTIModificationDescription('schema', '')))
        
        self.failIf('title' in IBlank)
    
    def test_old_factory_unregistered_after_name_changed_if_dynamic(self):
        portal_type = u"testtype"
        fti = DexterityFTI(portal_type)
        
        # Mock the lookup of the site and the site manager at the site root
        dummy_site = self.create_dummy()
        self.mock_utility(dummy_site, ISiteRoot)
        
        site_manager_mock = self.mocker.proxy(PersistentComponents(bases=(getGlobalSiteManager(),)))
        getSiteManager_mock = self.mocker.replace('zope.app.component.hooks.getSiteManager')
        self.expect(getSiteManager_mock(dummy_site)).result(site_manager_mock).count(1,None)
        
        # Pretend like we have a utility registered
        
        reg1 = self.create_dummy()
        reg1.provided = IFactory
        reg1.name = 'old-factory'
        reg1.info = 'plone.dexterity.dynamic'
        
        self.expect(site_manager_mock.registeredUtilities()).result([reg1])
        
        # Expect this to get removed
        self.expect(site_manager_mock.unregisterUtility(provided=IFactory, name='old-factory'))
        
        # And a new one to be created with the new factory name
        self.expect(site_manager_mock.registerUtility(
                    mocker.MATCH(lambda x: isinstance(x, DexterityFactory) and x.portal_type == portal_type),
                    IFactory, 'new-factory', info='plone.dexterity.dynamic')).passthrough()
        
        self.replay()
        fti.factory = 'new-factory'
        ftiModified(fti, ObjectModifiedEvent(fti, DexterityFTIModificationDescription('factory', 'old-factory')))
    
    def test_new_factory_not_registered_after_name_changed_if_exists(self):
        portal_type = u"testtype"
        fti = DexterityFTI(portal_type)
        
        # Mock the lookup of the site and the site manager at the site root
        dummy_site = self.create_dummy()
        self.mock_utility(dummy_site, ISiteRoot)
        
        site_manager_mock = self.mocker.proxy(PersistentComponents(bases=(getGlobalSiteManager(),)))
        getSiteManager_mock = self.mocker.replace('zope.app.component.hooks.getSiteManager')
        self.expect(getSiteManager_mock(dummy_site)).result(site_manager_mock).count(1,None)
        
        # Create a global default for the new name
        self.mock_utility(DexterityFactory(portal_type), IFactory, name='new-factory')
        
        # Factory should not be registered again
        self.expect(site_manager_mock.registerUtility(
                    mocker.MATCH(lambda x: isinstance(x, DexterityFactory) and x.portal_type == portal_type),
                    IFactory, 'new-factory', info='plone.dexterity.dynamic')).passthrough().count(0)
        
        self.replay()
        fti.factory = 'new-factory'
        ftiModified(fti, ObjectModifiedEvent(fti, DexterityFTIModificationDescription('factory', 'old-factory')))        

    def test_old_factory_not_unregistered_if_not_created_by_dexterity(self):
        portal_type = u"testtype"
        fti = DexterityFTI(portal_type)
        
        # Mock the lookup of the site and the site manager at the site root
        dummy_site = self.create_dummy()
        self.mock_utility(dummy_site, ISiteRoot)
        
        site_manager_mock = self.mocker.proxy(PersistentComponents(bases=(getGlobalSiteManager(),)))
        getSiteManager_mock = self.mocker.replace('zope.app.component.hooks.getSiteManager')
        self.expect(getSiteManager_mock(dummy_site)).result(site_manager_mock).count(1,None)
        
        # Pretend like we have a utility registered
        
        reg1 = self.create_dummy()
        reg1.provided = IFactory
        reg1.name = 'old-factory'
        reg1.info = None
        
        self.expect(site_manager_mock.registeredUtilities()).result([reg1])
        
        # This should not be removed, since we didn't create it
        self.expect(site_manager_mock.unregisterUtility(provided=IFactory, name='old-factory')).count(0)
        
        # A new one may still be created, however
        self.expect(site_manager_mock.registerUtility(
                    mocker.MATCH(lambda x: isinstance(x, DexterityFactory) and x.portal_type == portal_type),
                    IFactory, 'new-factory', info='plone.dexterity.dynamic')).passthrough()
        
        
        self.replay()
        fti.factory = 'new-factory'
        ftiModified(fti, ObjectModifiedEvent(fti, DexterityFTIModificationDescription('factory', 'old-factory')))
    
    def test_renamed_factory_not_unregistered_if_not_unique(self):
        portal_type = u"testtype"
        fti = DexterityFTI(portal_type, factory='common-factory')
        portal_type2 = u"testtype2"
        fti2 = DexterityFTI(portal_type2, factory='common-factory')
        
        # Mock the lookup of the site and the site manager at the site root
        dummy_site = self.create_dummy()
        self.mock_utility(dummy_site, ISiteRoot)
        
        site_manager_mock = self.mocker.proxy(PersistentComponents(bases=(getGlobalSiteManager(),)))
        getSiteManager_mock = self.mocker.replace('zope.app.component.hooks.getSiteManager')
        self.expect(getSiteManager_mock(dummy_site)).result(site_manager_mock).count(1,None)
        
        # Pretend two FTIs are registered, both using common-factory
        self.expect(site_manager_mock.registeredUtilities()).result([
            self.create_dummy(provided=IFactory, name='common-factory', info='plone.dexterity.dynamic'),
            self.create_dummy(component=fti, provided=IDexterityFTI, name='testtype', info='plone.dexterity.dynamic'),
            self.create_dummy(component=fti2, provided=IDexterityFTI, name='testtype2', info='plone.dexterity.dynamic'),
        ])
        
        # We shouldn't remove this since fti2 still uses it
        self.expect(site_manager_mock.unregisterUtility(provided=IFactory, name='common-factory')).count(0)
        
        # And a new one to be created with the new factory name
        self.expect(site_manager_mock.registerUtility(
                    mocker.MATCH(lambda x: isinstance(x, DexterityFactory) and x.portal_type == portal_type),
                    IFactory, 'new-factory', info='plone.dexterity.dynamic')).passthrough()
        
        self.replay()
        fti.factory = 'new-factory'
        ftiModified(fti, ObjectModifiedEvent(fti, DexterityFTIModificationDescription('factory', 'common-factory')))
    
    def test_deleted_factory_not_unregistered_if_not_unique(self):
        portal_type = u"testtype"
        fti = DexterityFTI(portal_type, factory='common-factory')
        portal_type2 = u"testtype2"
        fti2 = DexterityFTI(portal_type2, factory='common-factory')
        container_dummy = self.create_dummy()
        
        # Mock the lookup of the site and the site manager at the site root
        dummy_site = self.create_dummy()
        self.mock_utility(dummy_site, ISiteRoot)
        
        site_manager_mock = self.mocker.proxy(PersistentComponents(bases=(getGlobalSiteManager(),)))
        getSiteManager_mock = self.mocker.replace('zope.app.component.hooks.getSiteManager')
        self.expect(getSiteManager_mock(dummy_site)).result(site_manager_mock).count(1,None)
        
        # Pretend two FTIs are registered, both using common-factory
        # NB: Assuming that "testtype" was already removed when this gets called
        self.expect(site_manager_mock.registeredUtilities()).result([
            self.create_dummy(provided=IFactory, name='common-factory', info='plone.dexterity.dynamic'),
            self.create_dummy(component=fti2, provided=IDexterityFTI, name='testtype2', info='plone.dexterity.dynamic'),
        ])
        
        # We shouldn't remove this since fti2 still uses it
        self.expect(site_manager_mock.unregisterUtility(provided=IFactory, name='common-factory')).count(0)
        # The type itself should be removed though
        self.expect(site_manager_mock.unregisterUtility(provided=IDexterityFTI, name=u"testtype")).count(1)
        
        self.replay()
        ftiRemoved(fti, ObjectRemovedEvent(fti, container_dummy, fti.getId()))

def test_suite():
    return unittest.defaultTestLoader.loadTestsFromName(__name__)
