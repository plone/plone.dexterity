import unittest

from zope.interface.interface import InterfaceClass

from plone.dexterity.interfaces import ITemporarySchema
from plone.dexterity.interfaces import IDexteritySchema

from plone.dexterity import schema
from plone.dexterity import utils

class TestSchemaModuleFactory(unittest.TestCase):
    
    def test_default_schema(self):
        factory = schema.SchemaModuleFactory()
        
        schema_name = utils.portal_type_to_schema_name('testtype', prefix='site')
        klass = factory(schema_name, schema.generated)
        
        self.failUnless(isinstance(klass, InterfaceClass))
        self.failUnless(ITemporarySchema.providedBy(klass))
        self.failUnless(klass.isOrExtends(IDexteritySchema))
        
        self.assertEquals(schema_name, klass.__name__)
        self.assertEquals('plone.dexterity.schema.generated', klass.__module__)
        
    def test_named_schema(self):
        factory = schema.SchemaModuleFactory()
        
        schema_name = utils.portal_type_to_schema_name('testtype', schema="foo", prefix='site')
        klass = factory(schema_name, schema.generated)
        
        self.failUnless(isinstance(klass, InterfaceClass))
        self.failUnless(ITemporarySchema.providedBy(klass))
        self.failIf(klass.isOrExtends(IDexteritySchema))
        
        self.assertEquals(schema_name, klass.__name__)
        self.assertEquals('plone.dexterity.schema.generated', klass.__module__)

def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestSchemaModuleFactory))
    return suite
