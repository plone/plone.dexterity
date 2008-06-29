import unittest
import mocker
from plone.mocktestcase import MockTestCase

from zope.interface import implements, Interface
from zope import schema

from zope.configuration.interfaces import IConfigurationContext

from grokcore.component.testing import grok, grok_component

from plone.dexterity.directives import meta_type, add_permission
from plone.dexterity.content import Item
from plone.supermodel.directives import Schema

class TestDirectives(MockTestCase):

    def setUp(self):
        super(TestDirectives, self).setUp()
        grok('plone.dexterity.directives')

    def test_register_class_with_meta_type_and_add_permission(self):
        class Content(Item):
            meta_type("ContentMT")
            add_permission(u"mock.AddPermission")
        
        registerClass_mock = self.mocker.replace('Products.Five.fiveconfigure.registerClass')
        self.expect(registerClass_mock(self.match_provides(IConfigurationContext), 
                                        Content, "ContentMT", u"mock.AddPermission"))
    
        self.replay()
        
        grok_component('Content', Content)
        
    def test_no_register_class_with_meta_type_and_default_add_permission(self):
        class Content(Item):
            meta_type("ContentMT")
        
        registerClass_mock = self.mocker.replace('Products.Five.fiveconfigure.registerClass')
        self.expect(registerClass_mock(self.match_provides(IConfigurationContext), 
                                        Content, "ContentMT", u"cmf.AddPortalContent"))

        self.replay()
        
        grok_component('Content', Content)

    def test_no_register_class_without_meta_type(self):
        class Content(Item):
            pass
        
        registerClass_mock = self.mocker.replace('Products.Five.fiveconfigure.registerClass')
        self.expect(registerClass_mock(mocker.ANY, Content, mocker.ANY, mocker.ANY)).count(0)
    
        self.replay()
        
        grok_component('Content', Content)

    def test_schema_interfaces_initalised(self):
        
        class IContent(Schema):
            
            foo = schema.TextLine(title=u"Foo", default=u"bar")
        
        class Content(Item):
            implements(IContent)
        
        self.replay()

        self.failIf(hasattr(Content, "foo"))
        grok_component('Content', Content)
        self.assertEquals(u"bar", Content.foo)
    
    def test_schema_interface_initialisation_does_not_overwrite(self):
        
        class IContent(Schema):
            
            foo = schema.TextLine(title=u"Foo", default=u"bar")
        
        class Content(Item):
            implements(IContent)
        
            foo = u"baz"
        
        self.replay()

        grok_component('Content', Content)
        self.assertEquals(u"baz", Content.foo)
    
    def test_non_schema_interfaces_not_initialised(self):
        
        class IContent(Interface):
            
            foo = schema.TextLine(title=u"Foo", default=u"bar")
        
        class Content(Item):
            implements(IContent)
        
        self.replay()

        self.failIf(hasattr(Content, "foo"))
        grok_component('Content', Content)
        self.failIf(hasattr(Content, "foo"))
        
    def test_security_initialised(self):
        # TODO: Add tests here as part of security implementation
        pass
    
def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestDirectives))
    return suite
