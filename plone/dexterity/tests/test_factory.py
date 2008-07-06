import unittest
from plone.mocktestcase import MockTestCase

from zope.interface import Interface
from zope.interface.interface import InterfaceClass

import zope.schema

from plone.dexterity.interfaces import IDexterityFTI

from plone.dexterity.fti import DexterityFTI
from plone.dexterity.factory import DexterityFactory

from plone.supermodel.model import Model, METADATA_KEY

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
        self.expect(fti_mock.lookup_schema()).result(IDummy)
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
    #   - schema is looked up from FTI
    #   - if schema is provided by object, object is returned
    #   - otherwise, schema is set on the object, using alsoProvides
    #   - and fields are initialised to default values if attributes are not present
    
    def test_create_with_schema_already_provided_and_portal_type_set(self):
        
        # Object returned by class
        obj_mock = self.mocker.mock()
        self.expect(obj_mock.portal_type).result(u"testtype")
        
        # Class set by factory
        klass_mock = self.mocker.mock()
        self.expect(klass_mock()).result(obj_mock)
        
        # Resolver
        resolver_mock = self.mocker.replace("plone.dexterity.utils.resolve_dotted_name")
        self.expect(resolver_mock("my.mocked.ContentTypeClass")).result(klass_mock)
        
        # Schema
        schema_mock = self.mocker.mock(InterfaceClass)
        self.expect(schema_mock.providedBy(obj_mock)).result(True)
        
        # FTI
        fti_mock = self.mocker.mock(DexterityFTI)
        self.expect(fti_mock.klass).result("my.mocked.ContentTypeClass")
        self.expect(fti_mock.lookup_schema()).result(schema_mock)
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
        resolver_mock = self.mocker.replace("plone.dexterity.utils.resolve_dotted_name")
        self.expect(resolver_mock("my.mocked.ContentTypeClass")).result(klass_mock)
        
        # Schema
        schema_mock = self.mocker.mock(InterfaceClass)
        self.expect(schema_mock.providedBy(obj_mock)).result(True)
        
        # FTI
        fti_mock = self.mocker.mock(DexterityFTI)
        self.expect(fti_mock.klass).result("my.mocked.ContentTypeClass")
        self.expect(fti_mock.lookup_schema()).result(schema_mock)
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
        resolver_mock = self.mocker.replace("plone.dexterity.utils.resolve_dotted_name")
        self.expect(resolver_mock("my.mocked.ContentTypeClass")).result(klass_mock)
        
        # Mock fields - we proxy a TextLine field since we don't care too much
        # about how they work internally. Each field will be found to the 
        # object and then be used to set the default.
        
        field1_mock = self.mocker.proxy(zope.schema.TextLine(__name__="field1", title=u"Field 1"))
        self.expect(field1_mock.bind(obj_mock)).result(field1_mock)
        self.expect(field1_mock.set(obj_mock, None))
        
        field2_mock = self.mocker.proxy(zope.schema.TextLine(__name__="field2", title=u"Field 2", default=u"Field two"))
        self.expect(field2_mock.bind(obj_mock)).result(field2_mock)
        self.expect(field2_mock.set(obj_mock, u"Field two"))
        
        # Schema
        schema_mock = self.mocker.mock(InterfaceClass)
        self.expect(schema_mock.providedBy(obj_mock)).result(False) # -> need to initialise schema
        self.expect(schema_mock.getBases()).result([]).count(0, None)
        self.expect(schema_mock.queryTaggedValue(METADATA_KEY)).result(None).count(0, None)
        
        alsoProvides_mock = self.mocker.replace('zope.interface.alsoProvides')
        self.expect(alsoProvides_mock(obj_mock, schema_mock))
        
        getFieldsInOrder_mock = self.mocker.replace('zope.schema.getFieldsInOrder')
        self.expect(getFieldsInOrder_mock(schema_mock)).result([('field1', field1_mock,), ('field2', field2_mock,)])
        
        # Dummy model
        model_dummy = Model({u"": schema_mock})
        
        # FTI
        fti_mock = self.mocker.mock(DexterityFTI)
        self.expect(fti_mock.klass).result("my.mocked.ContentTypeClass")
        self.expect(fti_mock.lookup_schema()).result(schema_mock)
        self.expect(fti_mock.lookup_model()).result(model_dummy)
        self.mock_utility(fti_mock, IDexterityFTI, name=u"testtype")
        
        self.replay()
        
        factory = DexterityFactory(portal_type=u"testtype")
        self.assertEquals(obj_mock, factory())
    
    def test_create_does_not_overwrite_attributes(self):
        
        # Object returned by class - use a dummy rather than a mock because
        # we just want to check the value that was set onto it later
        
        class Dummy(object):
            portal_type = u"testtype"
            field2 = u"Object's second field" # no field1 -> field1 will be set, field2 will not
        
        obj_dummy = Dummy()
        
        # Class set by factory
        klass_mock = self.mocker.mock()
        self.expect(klass_mock()).result(obj_dummy)
        
        # Resolver
        resolver_mock = self.mocker.replace("plone.dexterity.utils.resolve_dotted_name")
        self.expect(resolver_mock("my.mocked.ContentTypeClass")).result(klass_mock)
        
        # Mock fields - we proxy a TextLine field since we don't care too much
        # about how they work internally. Each field will be found to the 
        # object and then be used to set the default.
        
        field1_mock = self.mocker.proxy(zope.schema.TextLine(__name__="field1", title=u"Field 1", default=u"Field one"))
        self.expect(field1_mock.bind(obj_dummy)).result(field1_mock)
        self.expect(field1_mock.set(obj_dummy, u"Field one")).passthrough()
        
        field2_mock = self.mocker.proxy(zope.schema.TextLine(__name__="field2", title=u"Field 2", default=u"Field two"))
        # self.expect(field2_mock.bind(obj_dummy)).result(field2_mock)
        # self.expect(field2_mock.set(obj_dummy, u"Field two"))
        
        # Schema
        schema_mock = self.mocker.mock(InterfaceClass)
        self.expect(schema_mock.providedBy(obj_dummy)).result(False) # -> need to initialise schema
        self.expect(schema_mock.getBases()).result([]).count(0, None)
        self.expect(schema_mock.queryTaggedValue(METADATA_KEY)).result(None).count(0, None)
        
        alsoProvides_mock = self.mocker.replace('zope.interface.alsoProvides')
        self.expect(alsoProvides_mock(obj_dummy, schema_mock))
        
        getFieldsInOrder_mock = self.mocker.replace('zope.schema.getFieldsInOrder')
        self.expect(getFieldsInOrder_mock(schema_mock)).result([('field1', field1_mock,), ('field2', field2_mock,)])
        
        # Dummy model
        model_dummy = Model({u"": schema_mock})
        
        # FTI
        fti_mock = self.mocker.mock(DexterityFTI)
        self.expect(fti_mock.klass).result("my.mocked.ContentTypeClass")
        self.expect(fti_mock.lookup_schema()).result(schema_mock)
        self.expect(fti_mock.lookup_model()).result(model_dummy)
        self.mock_utility(fti_mock, IDexterityFTI, name=u"testtype")
        
        self.replay()
        
        factory = DexterityFactory(portal_type=u"testtype")
        returned = factory()
        
        self.assertEquals(obj_dummy, returned)
        self.assertEquals(u"Field one", returned.field1) # set by field
        self.assertEquals(u"Object's second field", returned.field2) # untouched
    
    def test_factory_passes_args_and_kwargs(self):
        
        # Object returned by class
        obj_mock = self.mocker.mock()
        self.expect(obj_mock.portal_type).result(u"testtype")
        
        # Class set by factory
        klass_mock = self.mocker.mock()
        self.expect(klass_mock(u"id", title=u"title")).result(obj_mock)
        
        # Resolver
        resolver_mock = self.mocker.replace("plone.dexterity.utils.resolve_dotted_name")
        self.expect(resolver_mock("my.mocked.ContentTypeClass")).result(klass_mock)
        
        # Schema
        schema_mock = self.mocker.mock(InterfaceClass)
        self.expect(schema_mock.providedBy(obj_mock)).result(True)
        
        # FTI
        fti_mock = self.mocker.mock(DexterityFTI)
        self.expect(fti_mock.klass).result("my.mocked.ContentTypeClass")
        self.expect(fti_mock.lookup_schema()).result(schema_mock)
        self.mock_utility(fti_mock, IDexterityFTI, name=u"testtype")
        
        self.replay()
        
        factory = DexterityFactory(portal_type=u"testtype")
        self.assertEquals(obj_mock, factory(u"id", title=u"title"))
    
    def test_create_initializes_security(self):
        
        # TODO: This is not properly worked out yet
        pass

def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestFactory))
    return suite
