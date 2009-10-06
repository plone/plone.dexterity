import unittest
from plone.mocktestcase import MockTestCase

from zope.interface import Interface

from plone.dexterity.interfaces import IDexterityFTI

from plone.dexterity.fti import DexterityFTI
from plone.dexterity.factory import DexterityFactory

class IDummy(Interface):
    pass

class TestFactory(MockTestCase):
    
    def test_title(self):
        fti_mock = self.mocker.mock(DexterityFTI)
        self.expect(fti_mock.title).result("Mock type")
        self.mock_utility(fti_mock, IDexterityFTI, name=u"testtype")
        
        self.replay()
        
        factory = DexterityFactory(portal_type=u"testtype")
        self.assertEquals("Mock type", factory.title)
    
    def test_description(self):
        fti_mock = self.mocker.mock(DexterityFTI)
        self.expect(fti_mock.description).result("Mock type description")
        self.mock_utility(fti_mock, IDexterityFTI, name=u"testtype")
        
        self.replay()
        
        factory = DexterityFactory(portal_type=u"testtype")
        self.assertEquals("Mock type description", factory.description)

    def test_get_interfaces(self):
        fti_mock = self.mocker.mock(DexterityFTI)
        self.expect(fti_mock.lookupSchema()).result(IDummy)
        self.mock_utility(fti_mock, IDexterityFTI, name=u"testtype")
    
        self.replay()
        
        factory = DexterityFactory(portal_type=u"testtype")
        spec = factory.getInterfaces()
        
        self.assertEquals(u"testtype", spec.__name__)
        self.assertEquals([IDummy, Interface], list(spec.flattened()))

    # We expect the following when creating an object from the factory:
    # 
    #   - FTI's klass attribute is asked for a class name
    #   - name is resolved to a callable
    #   - callable is called to get an object
    #   - portal_type is set if not set already

    
    def test_create_with_schema_already_provided_and_portal_type_set(self):
        
        # Object returned by class
        obj_mock = self.mocker.mock()
        self.expect(obj_mock.portal_type).result(u"testtype")
        
        # Class set by factory
        klass_mock = self.mocker.mock()
        self.expect(klass_mock()).result(obj_mock)
        
        # Resolver
        resolver_mock = self.mocker.replace("plone.dexterity.utils.resolveDottedName")
        self.expect(resolver_mock("my.mocked.ContentTypeClass")).result(klass_mock)
        
        # FTI
        fti_mock = self.mocker.mock(DexterityFTI)
        self.expect(fti_mock.klass).result("my.mocked.ContentTypeClass")
        self.mock_utility(fti_mock, IDexterityFTI, name=u"testtype")
        
        self.replay()
        
        factory = DexterityFactory(portal_type=u"testtype")
        self.assertEquals(obj_mock, factory())
    
    def test_create_sets_portal_type_if_not_set(self):
        
        # Object returned by class
        obj_mock = self.mocker.mock()
        self.expect(obj_mock.portal_type).throw(AttributeError) # -> need to set portal_type
        obj_mock.portal_type = u"testtype"
        
        # Class set by factory
        klass_mock = self.mocker.mock()
        self.expect(klass_mock()).result(obj_mock)
        
        # Resolver
        resolver_mock = self.mocker.replace("plone.dexterity.utils.resolveDottedName")
        self.expect(resolver_mock("my.mocked.ContentTypeClass")).result(klass_mock)
        
        # FTI
        fti_mock = self.mocker.mock(DexterityFTI)
        self.expect(fti_mock.klass).result("my.mocked.ContentTypeClass")
        self.mock_utility(fti_mock, IDexterityFTI, name=u"testtype")
        
        self.replay()
        
        factory = DexterityFactory(portal_type=u"testtype")
        self.assertEquals(obj_mock, factory())

    def test_create_sets_portal_type_if_wrong(self):
        
        # Object returned by class
        obj_mock = self.mocker.mock()
        self.expect(obj_mock.portal_type).result('othertype') # -> need to fix portal_type
        obj_mock.portal_type = u"testtype"
        
        # Class set by factory
        klass_mock = self.mocker.mock()
        self.expect(klass_mock()).result(obj_mock)
        
        # Resolver
        resolver_mock = self.mocker.replace("plone.dexterity.utils.resolveDottedName")
        self.expect(resolver_mock("my.mocked.ContentTypeClass")).result(klass_mock)
        
        # FTI
        fti_mock = self.mocker.mock(DexterityFTI)
        self.expect(fti_mock.klass).result("my.mocked.ContentTypeClass")
        self.mock_utility(fti_mock, IDexterityFTI, name=u"testtype")
        
        self.replay()
        
        factory = DexterityFactory(portal_type=u"testtype")
        self.assertEquals(obj_mock, factory())
    
    def test_create_initialises_schema_if_not_provided(self):
        
        # Object returned by class
        obj_mock = self.mocker.mock()
        self.expect(obj_mock.portal_type).result(u"testtype")
        
        # Class set by factory
        klass_mock = self.mocker.mock()
        self.expect(klass_mock()).result(obj_mock)
        
        # Resolver
        resolver_mock = self.mocker.replace("plone.dexterity.utils.resolveDottedName")
        self.expect(resolver_mock("my.mocked.ContentTypeClass")).result(klass_mock)
        
        # FTI
        fti_mock = self.mocker.mock(DexterityFTI)
        self.expect(fti_mock.klass).result("my.mocked.ContentTypeClass")
        self.mock_utility(fti_mock, IDexterityFTI, name=u"testtype")
        
        self.replay()
        
        factory = DexterityFactory(portal_type=u"testtype")
        self.assertEquals(obj_mock, factory())
        
    def test_factory_passes_args_and_kwargs(self):
        
        # Object returned by class
        obj_mock = self.mocker.mock()
        self.expect(obj_mock.portal_type).result(u"testtype")
        
        # Class set by factory
        klass_mock = self.mocker.mock()
        self.expect(klass_mock(u"id", title=u"title")).result(obj_mock)
        
        # Resolver
        resolver_mock = self.mocker.replace("plone.dexterity.utils.resolveDottedName")
        self.expect(resolver_mock("my.mocked.ContentTypeClass")).result(klass_mock)
                
        # FTI
        fti_mock = self.mocker.mock(DexterityFTI)
        self.expect(fti_mock.klass).result("my.mocked.ContentTypeClass")
        self.mock_utility(fti_mock, IDexterityFTI, name=u"testtype")
        
        self.replay()
        
        factory = DexterityFactory(portal_type=u"testtype")
        self.assertEquals(obj_mock, factory(u"id", title=u"title"))

def test_suite():
    return unittest.defaultTestLoader.loadTestsFromName(__name__)
