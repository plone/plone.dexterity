import unittest
from plone.mocktestcase import MockTestCase

from zope.interface import Interface

import zope.schema

from plone.dexterity.interfaces import IDexterityFTI

from plone.dexterity.fti import DexterityFTI
from plone.dexterity.schema import schema_cache

class TestSchemaCache(MockTestCase):
    
    def setUp(self):
        schema_cache.clear()
    
    def test_repeated_lookup(self):

        class ISchema(Interface):
            pass

        # FTI mock
        fti_mock = self.mocker.proxy(DexterityFTI(u"testtype"))
        self.expect(fti_mock.lookup_schema()).result(ISchema)
        self.mock_utility(fti_mock, IDexterityFTI, name=u"testtype")
        
        self.replay()
        
        schema1 = schema_cache.get(u"testtype")
        schema2 = schema_cache.get(u"testtype")
        
        self.failUnless(schema1 is schema2 is ISchema)
    
    def test_repeated_lookup_with_changed_schema(self):

        class ISchema1(Interface):
            pass
            
        class ISchema2(Interface):
            pass

        # FTI mock
        fti_mock = self.mocker.proxy(DexterityFTI(u"testtype"))
        self.expect(fti_mock.lookup_schema()).result(ISchema1)
        self.expect(fti_mock.lookup_schema()).result(ISchema2).count(0,None)
        self.mock_utility(fti_mock, IDexterityFTI, name=u"testtype")
        
        self.replay()
        
        schema1 = schema_cache.get(u"testtype")
        schema2 = schema_cache.get(u"testtype")
        
        self.failUnless(schema1 is schema2 and schema2 is ISchema1)
    
    def test_repeated_lookup_with_changed_schema_and_invalidation(self):

        class ISchema1(Interface):
            pass
            
        class ISchema2(Interface):
            pass

        # FTI mock
        fti_mock = self.mocker.proxy(DexterityFTI(u"testtype"))
        self.expect(fti_mock.lookup_schema()).result(ISchema1)
        self.expect(fti_mock.lookup_schema()).result(ISchema2).count(0,None)
        self.mock_utility(fti_mock, IDexterityFTI, name=u"testtype")
        
        self.replay()
        
        schema1 = schema_cache.get(u"testtype")
        schema_cache.invalidate(u"testtype")
        schema2 = schema_cache.get(u"testtype")
        
        self.failUnless(schema1 is ISchema1)
        self.failUnless(schema2 is ISchema2)
    
    def test_none_not_cached(self):

        class ISchema1(Interface):
            pass
            
        # FTI mock
        fti_mock = self.mocker.proxy(DexterityFTI(u"testtype"))
        self.expect(fti_mock.lookup_schema()).result(None)
        self.expect(fti_mock.lookup_schema()).result(ISchema1)
        self.mock_utility(fti_mock, IDexterityFTI, name=u"testtype")
        
        self.replay()
        
        schema1 = schema_cache.get(u"testtype")
        schema2 = schema_cache.get(u"testtype")
        schema3 = schema_cache.get(u"testtype")
        
        self.failUnless(schema1 is None)
        self.failUnless(schema2 is schema3 is ISchema1)
    
    def test_attribute_and_value_error_not_cached(self):

        class ISchema1(Interface):
            pass
            
        # FTI mock
        fti_mock = self.mocker.proxy(DexterityFTI(u"testtype"))
        self.expect(fti_mock.lookup_schema()).throw(AttributeError)
        self.expect(fti_mock.lookup_schema()).throw(ValueError)
        self.expect(fti_mock.lookup_schema()).result(ISchema1)
        self.mock_utility(fti_mock, IDexterityFTI, name=u"testtype")
        
        self.replay()
        
        schema1 = schema_cache.get(u"testtype")
        schema2 = schema_cache.get(u"testtype")
        schema3 = schema_cache.get(u"testtype")
        
        self.failUnless(schema1 is None)
        self.failUnless(schema2 is None)
        self.failUnless(schema3 is ISchema1)
    
    def test_unknown_type_not_cached(self):

        class ISchema1(Interface):
            pass
            
        # FTI mock
        fti_mock = self.mocker.proxy(DexterityFTI(u"testtype"))
        self.expect(fti_mock.lookup_schema()).result(ISchema1)
        self.mock_utility(fti_mock, IDexterityFTI, name=u"testtype")
        
        self.replay()
        
        schema1 = schema_cache.get(u"othertype")
        schema2 = schema_cache.get(u"testtype")
        schema3 = schema_cache.get(u"testtype")
        
        self.failUnless(schema1 is None)
        self.failUnless(schema2 is schema3 is ISchema1)
    

def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestSchemaCache))
    return suite
