import unittest
import mocker
from plone.mocktestcase import MockTestCase

from zope.interface import implements, Interface
from zope import schema

from zope.configuration.interfaces import IConfigurationContext

from grokcore.component.testing import grok, grok_component

from plone.dexterity.directives.content import meta_type, add_permission
from plone.dexterity.content import Item

from plone.dexterity.directives import form
from plone.supermodel.directives import Schema

class DummyWidget(object):
    pass

class TestContentDirectives(MockTestCase):

    def setUp(self):
        super(TestContentDirectives, self).setUp()
        grok('plone.dexterity.directives.content')

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

class TestFormDirectives(MockTestCase):

    def setUp(self):
        super(TestFormDirectives, self).setUp()
        grok('plone.dexterity.directives.form')

    def test_form_directives_store_tagged_values(self):
        
        class IDummy(Schema):
            
            form.omitted('foo', 'bar')
            form.widget(foo='some.dummy.Widget', baz='other.Widget')
            form.mode(bar='hidden')
            form.order_before(baz='title')
            
            
            foo = schema.TextLine(title=u"Foo")
            bar = schema.TextLine(title=u"Bar")
            baz = schema.TextLine(title=u"Baz")
            
        self.replay()
        
        self.assertEquals(None, IDummy.queryTaggedValue(u'dexterity.form'))
        grok_component('IDummy', IDummy)
        self.assertEquals({u'widgets': [('foo', 'some.dummy.Widget'), ('baz', 'other.Widget')],
                           u'omitted': [('foo', 'true'), ('bar', 'true')],
                           u'moves': [('baz', 'title')],
                           u'modes': [('bar', 'hidden')]},
                            IDummy.queryTaggedValue(u"dexterity.form"))
        
    def test_widget_supports_instances_and_strings(self):
        
        class IDummy(Schema):
            
            form.widget(foo=DummyWidget)
            
            foo = schema.TextLine(title=u"Foo")
            bar = schema.TextLine(title=u"Bar")
            baz = schema.TextLine(title=u"Baz")
            
        self.replay()
        
        self.assertEquals(None, IDummy.queryTaggedValue(u'dexterity.form'))
        grok_component('IDummy', IDummy)
        self.assertEquals({u'widgets': [('foo', 'plone.dexterity.tests.test_directives.DummyWidget')]}, 
                            IDummy.queryTaggedValue(u"dexterity.form"))
        
    def test_form_directives_extend_existing_tagged_values(self):
        
        class IDummy(Schema):
            form.widget(foo='some.dummy.Widget')
            
            foo = schema.TextLine(title=u"Foo")
            bar = schema.TextLine(title=u"Bar")
            baz = schema.TextLine(title=u"Baz")
            
        IDummy.setTaggedValue(u'dexterity.form', {u'widgets': [('alpha', 'some.Widget')]})
            
        self.replay()
        
        self.assertEquals({u'widgets': [('alpha', 'some.Widget')]}, 
                            IDummy.queryTaggedValue(u'dexterity.form'))
        grok_component('IDummy', IDummy)
        self.assertEquals({u'widgets': [('alpha', 'some.Widget'), ('foo', 'some.dummy.Widget')]}, 
                            IDummy.queryTaggedValue(u"dexterity.form"))
        
    def test_multiple_invocations(self):
        
        class IDummy(Schema):
            
            form.omitted('foo')
            form.omitted('bar')
            form.widget(foo='some.dummy.Widget')
            form.widget(baz='other.Widget')
            form.mode(bar='hidden')
            form.mode(foo='display')
            form.order_before(baz='title')
            form.order_before(foo='body')
            
            
            foo = schema.TextLine(title=u"Foo")
            bar = schema.TextLine(title=u"Bar")
            baz = schema.TextLine(title=u"Baz")
            
        self.replay()
        
        self.assertEquals(None, IDummy.queryTaggedValue(u'dexterity.form'))
        grok_component('IDummy', IDummy)
        self.assertEquals({u'widgets': [('foo', 'some.dummy.Widget'), ('baz', 'other.Widget')],
                           u'omitted': [('foo', 'true'), ('bar', 'true')],
                           u'moves': [('baz', 'title'), ('foo', 'body')],
                           u'modes': [('bar', 'hidden'), ('foo', 'display')]}, 
                            IDummy.queryTaggedValue(u"dexterity.form"))

def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestContentDirectives))
    suite.addTest(unittest.makeSuite(TestFormDirectives))
    return suite
