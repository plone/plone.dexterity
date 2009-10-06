import unittest
from plone.mocktestcase import MockTestCase

from zope.interface import Interface
from zope.interface.interface import InterfaceClass

import zope.schema

from zope.app.content.interfaces import IContentType

from plone.dexterity.interfaces import IDexterityFTI
from plone.dexterity.interfaces import IDexteritySchema

from plone.dexterity.fti import DexterityFTI

from plone.dexterity import schema
from plone.dexterity import utils

from plone.supermodel.model import Model

class TestSchemaModuleFactory(MockTestCase):
    
    def test_transient_schema(self):
        
        # No IDexterityFTI registered
        factory = schema.SchemaModuleFactory()
        schemaName = utils.portalTypeToSchemaName('testtype', prefix='site')
        klass = factory(schemaName, schema.generated)
        
        self.failUnless(isinstance(klass, InterfaceClass))
        self.failUnless(klass.isOrExtends(IDexteritySchema))
        self.failUnless(IContentType.providedBy(klass))
        self.assertEquals(schemaName, klass.__name__)
        self.assertEquals('plone.dexterity.schema.generated', klass.__module__)
        self.assertEquals((), tuple(zope.schema.getFields(klass)))
        
    def test_concrete_default_schema(self):
        
        # Mock schema model
        class IDummy(Interface):
            dummy = zope.schema.TextLine(title=u"Dummy")
        mock_model = Model({u"": IDummy})
        
        # Mock FTI
        fti_mock = self.mocker.mock(DexterityFTI)
        fti_mock.lookupModel()
        self.mocker.result(mock_model)
        self.mock_utility(fti_mock, IDexterityFTI, u'testtype')
        
        self.mocker.replay()
        
        factory = schema.SchemaModuleFactory()
        
        schemaName = utils.portalTypeToSchemaName('testtype', prefix='site')
        klass = factory(schemaName, schema.generated)
        
        self.failUnless(isinstance(klass, InterfaceClass))
        self.failUnless(klass.isOrExtends(IDexteritySchema))
        self.failUnless(IContentType.providedBy(klass))
        self.assertEquals(schemaName, klass.__name__)
        self.assertEquals('plone.dexterity.schema.generated', klass.__module__)
        self.assertEquals(('dummy',), tuple(zope.schema.getFieldNames(klass)))

    def test_named_schema(self):
        
        # Mock schema model
        class IDummy(Interface):
            dummy = zope.schema.TextLine(title=u"Dummy")
        class INamedDummy(Interface):
            named = zope.schema.TextLine(title=u"Named")
        mock_model = Model({u"": IDummy,
                            u"named": INamedDummy})
        
        # Mock FTI
        fti_mock = self.mocker.mock(DexterityFTI)
        fti_mock.lookupModel()
        self.mocker.result(mock_model)
        self.mock_utility(fti_mock, IDexterityFTI, u'testtype')
        
        self.mocker.replay()
        
        factory = schema.SchemaModuleFactory()
        
        schemaName = utils.portalTypeToSchemaName('testtype', schema=u"named", prefix='site')
        klass = factory(schemaName, schema.generated)
        
        self.failUnless(isinstance(klass, InterfaceClass))
        self.failIf(klass.isOrExtends(IDexteritySchema)) # only default schema gets this
        self.failIf(IContentType.providedBy(klass))
        self.assertEquals(schemaName, klass.__name__)
        self.assertEquals('plone.dexterity.schema.generated', klass.__module__)
        self.assertEquals(('named',), tuple(zope.schema.getFieldNames(klass)))

    def test_transient_schema_made_concrete(self):
        
        factory = schema.SchemaModuleFactory()
        schemaName = utils.portalTypeToSchemaName('testtype', prefix='site')
        
        # No IDexterityFTI registered
        
        klass = factory(schemaName, schema.generated)
        self.failUnless(isinstance(klass, InterfaceClass))
        self.failUnless(klass.isOrExtends(IDexteritySchema))
        self.failUnless(IContentType.providedBy(klass))
        self.assertEquals(schemaName, klass.__name__)
        self.assertEquals('plone.dexterity.schema.generated', klass.__module__)
        self.assertEquals((), tuple(zope.schema.getFields(klass)))
        
        # Calling it again gives the same result
        
        klass = factory(schemaName, schema.generated)
        self.failUnless(isinstance(klass, InterfaceClass))
        self.failUnless(klass.isOrExtends(IDexteritySchema))
        self.failUnless(IContentType.providedBy(klass))
        self.assertEquals(schemaName, klass.__name__)
        self.assertEquals('plone.dexterity.schema.generated', klass.__module__)
        self.assertEquals((), tuple(zope.schema.getFields(klass)))
        
        # Now register a mock FTI and try again
        
        class IDummy(Interface):
            dummy = zope.schema.TextLine(title=u"Dummy")
        mock_model = Model({u"": IDummy})
        
        fti_mock = self.mocker.mock(DexterityFTI)
        fti_mock.lookupModel()
        self.mocker.result(mock_model)
        self.mock_utility(fti_mock, IDexterityFTI, u'testtype')
        
        self.mocker.replay()
        
        klass = factory(schemaName, schema.generated)
        
        self.failUnless(isinstance(klass, InterfaceClass))
        self.failUnless(klass.isOrExtends(IDexteritySchema))
        self.failUnless(IContentType.providedBy(klass))
        self.assertEquals(schemaName, klass.__name__)
        self.assertEquals('plone.dexterity.schema.generated', klass.__module__)
        
        # Now we get the fields from the FTI's model
        self.assertEquals(('dummy',), tuple(zope.schema.getFieldNames(klass)))

def test_suite():
    return unittest.defaultTestLoader.loadTestsFromName(__name__)
