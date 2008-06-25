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
from plone.supermodel.utils import ns

from elementtree import ElementTree

class TestSchemaModuleFactory(MockTestCase):
    
    def test_transient_schema(self):
        
        # No IDexterityFTI registered
        factory = schema.SchemaModuleFactory()
        schema_name = utils.portal_type_to_schema_name('testtype', prefix='site')
        klass = factory(schema_name, schema.generated)
        
        self.failUnless(isinstance(klass, InterfaceClass))
        self.failUnless(klass.isOrExtends(IDexteritySchema))
        self.failUnless(IContentType.providedBy(klass))
        self.assertEquals(schema_name, klass.__name__)
        self.assertEquals('plone.dexterity.schema.generated', klass.__module__)
        self.assertEquals((), tuple(zope.schema.getFields(klass)))
        
    def test_concrete_default_schema(self):
        
        # Mock schema model
        class IDummy(Interface):
            dummy = zope.schema.TextLine(title=u"Dummy")
        mock_model = Model({u"": IDummy})
        
        # Mock FTI
        fti_mock = self.mocker.mock(DexterityFTI)
        fti_mock.lookup_model()
        self.mocker.result(mock_model)
        self.mock_utility(fti_mock, IDexterityFTI, u'testtype')
        
        self.mocker.replay()
        
        factory = schema.SchemaModuleFactory()
        
        schema_name = utils.portal_type_to_schema_name('testtype', prefix='site')
        klass = factory(schema_name, schema.generated)
        
        self.failUnless(isinstance(klass, InterfaceClass))
        self.failUnless(klass.isOrExtends(IDexteritySchema))
        self.failUnless(IContentType.providedBy(klass))
        self.assertEquals(schema_name, klass.__name__)
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
        fti_mock.lookup_model()
        self.mocker.result(mock_model)
        self.mock_utility(fti_mock, IDexterityFTI, u'testtype')
        
        self.mocker.replay()
        
        factory = schema.SchemaModuleFactory()
        
        schema_name = utils.portal_type_to_schema_name('testtype', schema=u"named", prefix='site')
        klass = factory(schema_name, schema.generated)
        
        self.failUnless(isinstance(klass, InterfaceClass))
        self.failIf(klass.isOrExtends(IDexteritySchema)) # only default schema gets this
        self.failIf(IContentType.providedBy(klass))
        self.assertEquals(schema_name, klass.__name__)
        self.assertEquals('plone.dexterity.schema.generated', klass.__module__)
        self.assertEquals(('named',), tuple(zope.schema.getFieldNames(klass)))

    def test_transient_schema_made_concrete(self):
        
        factory = schema.SchemaModuleFactory()
        schema_name = utils.portal_type_to_schema_name('testtype', prefix='site')
        
        # No IDexterityFTI registered
        
        klass = factory(schema_name, schema.generated)
        self.failUnless(isinstance(klass, InterfaceClass))
        self.failUnless(klass.isOrExtends(IDexteritySchema))
        self.failUnless(IContentType.providedBy(klass))
        self.assertEquals(schema_name, klass.__name__)
        self.assertEquals('plone.dexterity.schema.generated', klass.__module__)
        self.assertEquals((), tuple(zope.schema.getFields(klass)))
        
        # Calling it again gives the same result
        
        klass = factory(schema_name, schema.generated)
        self.failUnless(isinstance(klass, InterfaceClass))
        self.failUnless(klass.isOrExtends(IDexteritySchema))
        self.failUnless(IContentType.providedBy(klass))
        self.assertEquals(schema_name, klass.__name__)
        self.assertEquals('plone.dexterity.schema.generated', klass.__module__)
        self.assertEquals((), tuple(zope.schema.getFields(klass)))
        
        # Now register a mock FTI and try again
        
        class IDummy(Interface):
            dummy = zope.schema.TextLine(title=u"Dummy")
        mock_model = Model({u"": IDummy})
        
        fti_mock = self.mocker.mock(DexterityFTI)
        fti_mock.lookup_model()
        self.mocker.result(mock_model)
        self.mock_utility(fti_mock, IDexterityFTI, u'testtype')
        
        self.mocker.replay()
        
        klass = factory(schema_name, schema.generated)
        
        self.failUnless(isinstance(klass, InterfaceClass))
        self.failUnless(klass.isOrExtends(IDexteritySchema))
        self.failUnless(IContentType.providedBy(klass))
        self.assertEquals(schema_name, klass.__name__)
        self.assertEquals('plone.dexterity.schema.generated', klass.__module__)
        
        # Now we get the fields from the FTI's model
        self.assertEquals(('dummy',), tuple(zope.schema.getFieldNames(klass)))

class TestSecuritySchema(unittest.TestCase):
    
    namespace = 'http://namespaces.plone.org/dexterity/security'
    
    def test_read(self):
        field_node = ElementTree.Element('field')
        field_node.set(ns("read-permission", self.namespace), "Read perm")
        field_node.set(ns("write-permission", self.namespace), "Write perm")
        field = zope.schema.TextLine(title=u"dummy", __name__=u'dummy')
        metadata = {}
        
        handler = schema.SecuritySchema()
        handler.read(field_node, field, metadata)
        self.assertEquals({u'dummy': {'read-permission': "Read perm",
                                      'write-permission': "Write perm"}}, metadata)
    
    def test_read_no_permissions(self):
        field_node = ElementTree.Element('field')
        field = zope.schema.TextLine(title=u"dummy", __name__=u'dummy')
        metadata = {}

        handler = schema.SecuritySchema()
        handler.read(field_node, field, metadata)
        self.assertEquals({}, metadata)
        
    def test_write(self):
        field_node = ElementTree.Element('field')
        field = zope.schema.TextLine(title=u"dummy", __name__=u'dummy')
        
        metadata = {u'dummy': {'read-permission': "Read perm",
                               'write-permission': "Write perm"}}
        handler = schema.SecuritySchema()
        handler.write(field_node, field, metadata)
        self.assertEquals("Read perm", field_node.get(ns("read-permission", self.namespace)))
        self.assertEquals("Write perm", field_node.get(ns("write-permission", self.namespace)))
    
    def test_write_no_permissions(self):
        field_node = ElementTree.Element('field')
        field = zope.schema.TextLine(title=u"dummy", __name__=u'dummy')
        
        metadata = {u'dummy': {}}
        handler = schema.SecuritySchema()
        handler.write(field_node, field, metadata)
        self.assertEquals(None, field_node.get(ns("read-permission", self.namespace)))
        self.assertEquals(None, field_node.get(ns("write-permission", self.namespace)))

    def test_write_no_metadata(self):
        field_node = ElementTree.Element('field')
        field = zope.schema.TextLine(title=u"dummy", __name__=u'dummy')
        
        metadata = {}
        handler = schema.SecuritySchema()
        handler.write(field_node, field, metadata)
        self.assertEquals(None, field_node.get(ns("read-permission", self.namespace)))
        self.assertEquals(None, field_node.get(ns("write-permission", self.namespace)))
        
class TestWidgetSchema(unittest.TestCase):
    
    namespace = 'http://namespaces.plone.org/dexterity/widget'
    
    def test_read(self):
        field_node = ElementTree.Element('field')
        field_node.set(ns("widget", self.namespace), "SomeWidget")
        field = zope.schema.TextLine(title=u"dummy", __name__=u'dummy')
        metadata = {}
        
        handler = schema.WidgetSchema()
        handler.read(field_node, field, metadata)
        self.assertEquals({u'dummy': 'SomeWidget'}, metadata)
    
    def test_read_no_widget(self):
        field_node = ElementTree.Element('field')
        field = zope.schema.TextLine(title=u"dummy", __name__=u'dummy')
        metadata = {}

        handler = schema.WidgetSchema()
        handler.read(field_node, field, metadata)
        self.assertEquals({}, metadata)
        
    def test_write(self):
        field_node = ElementTree.Element('field')
        field = zope.schema.TextLine(title=u"dummy", __name__=u'dummy')
        
        metadata = {u'dummy': 'SomeWidget'}
        handler = schema.WidgetSchema()
        handler.write(field_node, field, metadata)
        self.assertEquals("SomeWidget", field_node.get(ns("widget", self.namespace)))
    
    def test_write_no_widget(self):
        field_node = ElementTree.Element('field')
        field = zope.schema.TextLine(title=u"dummy", __name__=u'dummy')
        
        metadata = {u'dummy': {}}
        handler = schema.WidgetSchema()
        handler.write(field_node, field, metadata)
        self.assertEquals(None, field_node.get(ns("widget", self.namespace)))

    def test_write_no_metadata(self):
        field_node = ElementTree.Element('field')
        field = zope.schema.TextLine(title=u"dummy", __name__=u'dummy')
        
        metadata = {}
        handler = schema.WidgetSchema()
        handler.write(field_node, field, metadata)
        self.assertEquals(None, field_node.get(ns("widget", self.namespace)))
        
def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestSchemaModuleFactory))
    suite.addTest(unittest.makeSuite(TestSecuritySchema))
    suite.addTest(unittest.makeSuite(TestWidgetSchema))
    return suite
