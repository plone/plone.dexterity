import unittest
from plone.mocktestcase import MockTestCase

from zope.interface import Interface

from plone.dexterity.interfaces import IDexterityFTI

from plone.dexterity.fti import DexterityFTI
from plone.dexterity.schema import SCHEMA_CACHE

class TestSchemaCache(MockTestCase):
    
    def setUp(self):
        SCHEMA_CACHE.clear()
    
    def test_repeated_lookup(self):

        class ISchema(Interface):
            pass

        # FTI mock
        fti_mock = self.mocker.proxy(DexterityFTI(u"testtype"))
        self.expect(fti_mock.lookupSchema()).result(ISchema)
        self.mock_utility(fti_mock, IDexterityFTI, name=u"testtype")
        
        self.replay()
        
        schema1 = SCHEMA_CACHE.get(u"testtype")
        schema2 = SCHEMA_CACHE.get(u"testtype")
        
        self.failUnless(schema1 is schema2 is ISchema)
    
    def test_repeated_lookup_with_changed_schema(self):

        class ISchema1(Interface):
            pass
            
        class ISchema2(Interface):
            pass

        # FTI mock
        fti_mock = self.mocker.proxy(DexterityFTI(u"testtype"))
        self.expect(fti_mock.lookupSchema()).result(ISchema1)
        self.expect(fti_mock.lookupSchema()).result(ISchema2).count(0,None)
        self.mock_utility(fti_mock, IDexterityFTI, name=u"testtype")
        
        self.replay()
        
        schema1 = SCHEMA_CACHE.get(u"testtype")
        schema2 = SCHEMA_CACHE.get(u"testtype")
        
        self.failUnless(schema1 is schema2 and schema2 is ISchema1)
    
    def test_repeated_lookup_with_changed_schema_and_invalidation(self):

        class ISchema1(Interface):
            pass
            
        class ISchema2(Interface):
            pass

        # FTI mock
        fti_mock = self.mocker.proxy(DexterityFTI(u"testtype"))
        self.expect(fti_mock.lookupSchema()).result(ISchema1)
        self.expect(fti_mock.lookupSchema()).result(ISchema2).count(0,None)
        self.mock_utility(fti_mock, IDexterityFTI, name=u"testtype")
        
        self.replay()
        
        schema1 = SCHEMA_CACHE.get(u"testtype")
        SCHEMA_CACHE.invalidate(u"testtype")
        schema2 = SCHEMA_CACHE.get(u"testtype")
        
        self.failUnless(schema1 is ISchema1)
        self.failUnless(schema2 is ISchema2)
    
    def test_none_not_cached(self):

        class ISchema1(Interface):
            pass
            
        # FTI mock
        fti_mock = self.mocker.proxy(DexterityFTI(u"testtype"))
        self.expect(fti_mock.lookupSchema()).result(None)
        self.expect(fti_mock.lookupSchema()).result(ISchema1)
        self.mock_utility(fti_mock, IDexterityFTI, name=u"testtype")
        
        self.replay()
        
        schema1 = SCHEMA_CACHE.get(u"testtype")
        schema2 = SCHEMA_CACHE.get(u"testtype")
        schema3 = SCHEMA_CACHE.get(u"testtype")
        
        self.failUnless(schema1 is None)
        self.failUnless(schema2 is schema3 is ISchema1)
    
    def test_attribute_and_value_error_not_cached(self):

        class ISchema1(Interface):
            pass
            
        # FTI mock
        fti_mock = self.mocker.proxy(DexterityFTI(u"testtype"))
        self.expect(fti_mock.lookupSchema()).throw(AttributeError)
        self.expect(fti_mock.lookupSchema()).throw(ValueError)
        self.expect(fti_mock.lookupSchema()).result(ISchema1)
        self.mock_utility(fti_mock, IDexterityFTI, name=u"testtype")
        
        self.replay()
        
        schema1 = SCHEMA_CACHE.get(u"testtype")
        schema2 = SCHEMA_CACHE.get(u"testtype")
        schema3 = SCHEMA_CACHE.get(u"testtype")
        
        self.failUnless(schema1 is None)
        self.failUnless(schema2 is None)
        self.failUnless(schema3 is ISchema1)
    
    def test_unknown_type_not_cached(self):

        class ISchema1(Interface):
            pass
            
        # FTI mock
        fti_mock = self.mocker.proxy(DexterityFTI(u"testtype"))
        self.expect(fti_mock.lookupSchema()).result(ISchema1)
        self.mock_utility(fti_mock, IDexterityFTI, name=u"testtype")
        
        self.replay()
        
        schema1 = SCHEMA_CACHE.get(u"othertype")
        schema2 = SCHEMA_CACHE.get(u"testtype")
        schema3 = SCHEMA_CACHE.get(u"testtype")
        
        self.failUnless(schema1 is None)
        self.failUnless(schema2 is schema3 is ISchema1)

def test_suite():
    return unittest.defaultTestLoader.loadTestsFromName(__name__)
