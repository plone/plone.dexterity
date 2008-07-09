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
        
        class IDummy(Interface):
            dummy = zope.schema.TextLine(title=u"dummy")
        
        handler = schema.SecuritySchema()
        handler.read(field_node, IDummy, IDummy['dummy'])
        
        self.assertEquals({u'dummy': {'read-permission': "Read perm",
                                      'write-permission': "Write perm"}},
                            IDummy.getTaggedValue(u"dexterity.security"))
    
    def test_read_no_permissions(self):
        field_node = ElementTree.Element('field')
        
        class IDummy(Interface):
            dummy = zope.schema.TextLine(title=u"dummy")

        handler = schema.SecuritySchema()
        handler.read(field_node, IDummy, IDummy['dummy'])
        
        self.failIf(u'dexterity.security' in IDummy.getTaggedValueTags())
        
    def test_write(self):
        field_node = ElementTree.Element('field')
        
        class IDummy(Interface):
            dummy = zope.schema.TextLine(title=u"dummy")
        
        IDummy.setTaggedValue(u'dexterity.security',
                                {u'dummy': {'read-permission': "Read perm",
                                            'write-permission': "Write perm"}})
                               
        handler = schema.SecuritySchema()
        handler.write(field_node, IDummy, IDummy['dummy'])
        
        self.assertEquals("Read perm", field_node.get(ns("read-permission", self.namespace)))
        self.assertEquals("Write perm", field_node.get(ns("write-permission", self.namespace)))
    
    def test_write_no_permissions(self):
        field_node = ElementTree.Element('field')
        
        class IDummy(Interface):
            dummy = zope.schema.TextLine(title=u"dummy")
        
        IDummy.setTaggedValue(u'dexterity.security', {u'dummy': {}})
        
        handler = schema.SecuritySchema()
        handler.write(field_node, IDummy, IDummy['dummy'])
        
        self.assertEquals(None, field_node.get(ns("read-permission", self.namespace)))
        self.assertEquals(None, field_node.get(ns("write-permission", self.namespace)))

    def test_write_no_metadata(self):
        field_node = ElementTree.Element('field')
        
        class IDummy(Interface):
            dummy = zope.schema.TextLine(title=u"dummy")
        
        handler = schema.SecuritySchema()
        handler.write(field_node, IDummy, IDummy['dummy'])
        
        self.assertEquals(None, field_node.get(ns("read-permission", self.namespace)))
        self.assertEquals(None, field_node.get(ns("write-permission", self.namespace)))
        
class TestFormSchema(unittest.TestCase):
    
    namespace = 'http://namespaces.plone.org/dexterity/form'
    
    def test_read(self):
        field_node = ElementTree.Element('field')
        field_node.set(ns("widget", self.namespace), "SomeWidget")
        field_node.set(ns("mode", self.namespace), "hidden")
        field_node.set(ns("omitted", self.namespace), "true")
        field_node.set(ns("before", self.namespace), "somefield")
        
        class IDummy(Interface):
            dummy = zope.schema.TextLine(title=u"dummy")
        
        handler = schema.FormSchema()
        handler.read(field_node, IDummy, IDummy['dummy'])
        
        metadata = IDummy.getTaggedValue(u"dexterity.form")
        
        self.assertEquals({'widgets': [('dummy', 'SomeWidget')], 
                           'omitted': [('dummy', 'true')],
                           'modes': [('dummy', 'hidden')],
                           'before': [('dummy', 'somefield')]}, metadata)

    def test_read_multiple(self):
        field_node1 = ElementTree.Element('field')
        field_node1.set(ns("widget", self.namespace), "SomeWidget")
        field_node1.set(ns("mode", self.namespace), "hidden")
        field_node1.set(ns("omitted", self.namespace), "true")
        field_node1.set(ns("before", self.namespace), "somefield")
        
        field_node2 = ElementTree.Element('field')
        field_node2.set(ns("mode", self.namespace), "display")
        field_node2.set(ns("omitted", self.namespace), "yes")
        
        class IDummy(Interface):
            dummy1 = zope.schema.TextLine(title=u"dummy1")
            dummy2 = zope.schema.TextLine(title=u"dummy2")
        
        handler = schema.FormSchema()
        handler.read(field_node1, IDummy, IDummy['dummy1'])
        handler.read(field_node2, IDummy, IDummy['dummy2'])
        
        metadata = IDummy.getTaggedValue(u"dexterity.form")
        
        self.assertEquals({'widgets': [('dummy1', 'SomeWidget')], 
                           'omitted': [('dummy1', 'true'), ('dummy2', 'yes')],
                           'modes': [('dummy1', 'hidden'), ('dummy2', 'display')],
                           'before': [('dummy1', 'somefield')]}, metadata)
    
    def test_read_no_data(self):
        field_node = ElementTree.Element('field')
        
        class IDummy(Interface):
            dummy = zope.schema.TextLine(title=u"dummy1")

        handler = schema.FormSchema()
        handler.read(field_node, IDummy, IDummy['dummy'])
        
        self.assertEquals(None, IDummy.queryTaggedValue(u'dexterity.form'))
        
    def test_write(self):
        field_node = ElementTree.Element('field')
        
        class IDummy(Interface):
            dummy = zope.schema.TextLine(title=u"dummy1")
            
        IDummy.setTaggedValue(u"dexterity.form", { 'widgets': [('dummy', 'SomeWidget')], 
                                                   'omitted': [('dummy', 'true')],
                                                   'modes': [('dummy', 'hidden')],
                                                   'before': [('dummy', 'somefield')]})
        
        handler = schema.FormSchema()
        handler.write(field_node, IDummy, IDummy['dummy'])
        
        self.assertEquals("SomeWidget", field_node.get(ns("widget", self.namespace)))
        self.assertEquals("true", field_node.get(ns("omitted", self.namespace)))
        self.assertEquals("hidden", field_node.get(ns("mode", self.namespace)))
        self.assertEquals("somefield", field_node.get(ns("before", self.namespace)))
    
    def test_write_partial(self):
        field_node = ElementTree.Element('field')
        
        class IDummy(Interface):
            dummy = zope.schema.TextLine(title=u"dummy1")
            
        IDummy.setTaggedValue(u"dexterity.form", { 'widgets': [('dummy', 'SomeWidget')], 
                                                   'omitted': [('dummy2', 'true')],
                                                   'modes': [('dummy', 'display'), ('dummy2', 'hidden')],
                                                   'before': []})
        
        handler = schema.FormSchema()
        handler.write(field_node, IDummy, IDummy['dummy'])
        
        self.assertEquals("SomeWidget", field_node.get(ns("widget", self.namespace)))
        self.assertEquals(None, field_node.get(ns("omitted", self.namespace)))
        self.assertEquals("display", field_node.get(ns("mode", self.namespace)))
        self.assertEquals(None, field_node.get(ns("before", self.namespace)))

    def test_write_no_data(self):
        field_node = ElementTree.Element('field')
        
        class IDummy(Interface):
            dummy = zope.schema.TextLine(title=u"dummy1")
            
        handler = schema.FormSchema()
        handler.write(field_node, IDummy, IDummy['dummy'])
        
        self.assertEquals(None, field_node.get(ns("widget", self.namespace)))
        self.assertEquals(None, field_node.get(ns("omitted", self.namespace)))
        self.assertEquals(None, field_node.get(ns("mode", self.namespace)))
        self.assertEquals(None, field_node.get(ns("before", self.namespace)))
        
def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestSchemaModuleFactory))
    suite.addTest(unittest.makeSuite(TestSecuritySchema))
    suite.addTest(unittest.makeSuite(TestFormSchema))
    return suite
