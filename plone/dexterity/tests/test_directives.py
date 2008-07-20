import unittest
import mocker
from plone.mocktestcase import MockTestCase

from zope.configuration.config import ConfigurationExecutionError
from martian.error import GrokImportError

from zope.interface import implements, Interface
from zope import schema

from zope.configuration.interfaces import IConfigurationContext

from zope.component.interfaces import IFactory

from plone.dexterity.browser.add import AddViewFactory

from zope.publisher.interfaces.browser import IBrowserView
from zope.publisher.interfaces.browser import IBrowserRequest
from zope.app.container.interfaces import IAdding

from grokcore.component.testing import grok, grok_component

from plone.dexterity.directives.content import meta_type, add_permission, portal_type
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
        
    def test_portal_type_sets_portal_type(self):
        
        class Content(Item):
            portal_type('my.type')
        
        provideUtility_mock = self.mocker.replace('zope.component.provideUtility')
        self.expect(provideUtility_mock(self.match_provides(IFactory), IFactory, 'my.type'))
    
        provideAdapter_mock = self.mocker.replace('zope.component.provideAdapter')
        self.expect(provideAdapter_mock(factory=self.match_type(AddViewFactory),
                                        adapts=(IAdding, IBrowserRequest),
                                        provides=IBrowserView,
                                        name='my.type'))
    
        self.replay()
        
        self.assertNotEquals('my.type', Content.portal_type)
        grok_component('Content', Content)
        self.assertEquals('my.type', Content.portal_type)

    def test_portal_type_fails_if_portal_type_inconsistent(self):
        
        class Content(Item):
            portal_type('my.type')
            portal_type = 'other.type'
        
        self.replay()
        
        self.assertEquals('other.type', Content.portal_type)
        try:
            grok_component('Content', Content)
        except ConfigurationExecutionError, e:
            self.assertEquals(e.etype, GrokImportError)
        else:
            self.fail()
        
    
    def test_portal_type_registers_factory_and_addview(self):
        
        class Content(Item):
            portal_type('my.type')
        
        provideUtility_mock = self.mocker.replace('zope.component.provideUtility')
        self.expect(provideUtility_mock(self.match_provides(IFactory), IFactory, 'my.type'))
    
        provideAdapter_mock = self.mocker.replace('zope.component.provideAdapter')
        self.expect(provideAdapter_mock(factory=self.match_type(AddViewFactory),
                                        adapts=(IAdding, IBrowserRequest),
                                        provides=IBrowserView,
                                        name='my.type'))
    
        self.replay()
        
        grok_component('Content', Content)
    
    def test_portal_type_does_not_overwrite_factory_and_addview(self):
        
        class Content(Item):
            portal_type('my.type')
        
        factory_dummy = self.create_dummy()
        self.mock_utility(factory_dummy, IFactory, 'my.type')
        
        addview_dummy = self.create_dummy()
        self.mock_adapter(addview_dummy, Interface, (IAdding, IBrowserRequest), 'my.type')
        
        provideUtility_mock = self.mocker.replace('zope.component.provideUtility')
        self.expect(provideUtility_mock(mocker.ANY, IFactory, 'my.type')).count(0)
    
        provideAdapter_mock = self.mocker.replace('zope.component.provideAdapter')
        self.expect(provideAdapter_mock(factory=mocker.ANY,
                                        adapts=(IAdding, IBrowserRequest),
                                        provides=mocker.ANY,
                                        name='my.type')).count(0)
    
        self.replay()
        
        grok_component('Content', Content)

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
