import unittest
import mocker
from plone.mocktestcase import MockTestCase

from zope.interface import implements, Interface
import zope.schema

from zope.configuration.interfaces import IConfigurationContext

from zope.component.interfaces import IFactory

from zope.publisher.interfaces.browser import IBrowserRequest
from zope.app.container.interfaces import IAdding

from grokcore.component.testing import grok, grok_component
import five.grok

from plone.dexterity.directives.content import add_permission
from plone.dexterity.content import Item

from plone.dexterity.directives import schema
from plone.supermodel.directives import Schema

from plone.dexterity.directives import form

from zope.publisher.interfaces.browser import IDefaultBrowserLayer
from Products.CMFCore.interfaces import IFolderish

class DummyWidget(object):
    pass

class TestContentDirectives(MockTestCase):

    def setUp(self):
        super(TestContentDirectives, self).setUp()
        grok('plone.dexterity.directives.content')

    def test_register_class_with_meta_type_and_add_permission(self):
        class Content(Item):
            meta_type = "ContentMT"
            add_permission(u"mock.AddPermission")
        
        registerClass_mock = self.mocker.replace('Products.Five.fiveconfigure.registerClass')
        self.expect(registerClass_mock(self.match_provides(IConfigurationContext), 
                                        Content, "ContentMT", u"mock.AddPermission"))
    
        self.replay()
        
        grok_component('Content', Content)
        
    def test_register_class_with_meta_type_and_default_add_permission(self):
        class Content(Item):
            meta_type = "ContentMT"
        
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
            
            foo = zope.schema.TextLine(title=u"Foo", default=u"bar")
        
        class Content(Item):
            implements(IContent)
        
        self.replay()

        self.failIf(hasattr(Content, "foo"))
        grok_component('Content', Content)
        self.assertEquals(u"bar", Content.foo)
    
    def test_schema_interface_initialisation_does_not_overwrite(self):
        
        class IContent(Schema):
            
            foo = zope.schema.TextLine(title=u"Foo", default=u"bar")
        
        class Content(Item):
            implements(IContent)
        
            foo = u"baz"
        
        self.replay()

        grok_component('Content', Content)
        self.assertEquals(u"baz", Content.foo)
    
    def test_non_schema_interfaces_not_initialised(self):
        
        class IContent(Interface):
            
            foo = zope.schema.TextLine(title=u"Foo", default=u"bar")
        
        class Content(Item):
            implements(IContent)
        
        self.replay()

        self.failIf(hasattr(Content, "foo"))
        grok_component('Content', Content)
        self.failIf(hasattr(Content, "foo"))
        
    def test_security_initialised(self):
        # TODO: Add tests here as part of security implementation
        pass
        
    def test_portal_type_registers_factory_and_addview(self):
        
        class Content(Item):
            portal_type = 'my.type'
        
        provideUtility_mock = self.mocker.replace('zope.component.provideUtility')
        self.expect(provideUtility_mock(self.match_provides(IFactory), IFactory, 'my.type'))

        self.replay()
        
        grok_component('Content', Content)
    
    def test_portal_type_does_not_overwrite_factory_and_addview(self):
        
        class Content(Item):
            portal_type = 'my.type'
        
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

class TestSchemaDirectives(MockTestCase):

    def setUp(self):
        super(TestSchemaDirectives, self).setUp()
        grok('plone.dexterity.directives.schema')

    def test_schema_directives_store_tagged_values(self):
        
        class IDummy(Schema):
            
            schema.omitted('foo', 'bar')
            schema.widget(foo='some.dummy.Widget', baz='other.Widget')
            schema.mode(bar='hidden')
            schema.order_before(baz='title')
            
            
            foo = zope.schema.TextLine(title=u"Foo")
            bar = zope.schema.TextLine(title=u"Bar")
            baz = zope.schema.TextLine(title=u"Baz")
            
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
            
            schema.widget(foo=DummyWidget)
            
            foo = zope.schema.TextLine(title=u"Foo")
            bar = zope.schema.TextLine(title=u"Bar")
            baz = zope.schema.TextLine(title=u"Baz")
            
        self.replay()
        
        self.assertEquals(None, IDummy.queryTaggedValue(u'dexterity.form'))
        grok_component('IDummy', IDummy)
        self.assertEquals({u'widgets': [('foo', 'plone.dexterity.tests.test_directives.DummyWidget')]}, 
                            IDummy.queryTaggedValue(u"dexterity.form"))
        
    def test_schema_directives_extend_existing_tagged_values(self):
        
        class IDummy(Schema):
            schema.widget(foo='some.dummy.Widget')
            
            foo = zope.schema.TextLine(title=u"Foo")
            bar = zope.schema.TextLine(title=u"Bar")
            baz = zope.schema.TextLine(title=u"Baz")
            
        IDummy.setTaggedValue(u'dexterity.form', {u'widgets': [('alpha', 'some.Widget')]})
            
        self.replay()
        
        self.assertEquals({u'widgets': [('alpha', 'some.Widget')]}, 
                            IDummy.queryTaggedValue(u'dexterity.form'))
        grok_component('IDummy', IDummy)
        self.assertEquals({u'widgets': [('alpha', 'some.Widget'), ('foo', 'some.dummy.Widget')]}, 
                            IDummy.queryTaggedValue(u"dexterity.form"))
        
    def test_multiple_invocations(self):
        
        class IDummy(Schema):
            
            schema.omitted('foo')
            schema.omitted('bar')
            schema.widget(foo='some.dummy.Widget')
            schema.widget(baz='other.Widget')
            schema.mode(bar='hidden')
            schema.mode(foo='display')
            schema.order_before(baz='title')
            schema.order_before(foo='body')
            
            
            foo = zope.schema.TextLine(title=u"Foo")
            bar = zope.schema.TextLine(title=u"Bar")
            baz = zope.schema.TextLine(title=u"Baz")
            
        self.replay()
        
        self.assertEquals(None, IDummy.queryTaggedValue(u'dexterity.form'))
        grok_component('IDummy', IDummy)
        self.assertEquals({u'widgets': [('foo', 'some.dummy.Widget'), ('baz', 'other.Widget')],
                           u'omitted': [('foo', 'true'), ('bar', 'true')],
                           u'moves': [('baz', 'title'), ('foo', 'body')],
                           u'modes': [('bar', 'hidden'), ('foo', 'display')]}, 
                            IDummy.queryTaggedValue(u"dexterity.form"))

class TestFormDirectives(MockTestCase):

    def setUp(self):
        super(TestFormDirectives, self).setUp()
        grok('plone.dexterity.directives.form')
        
    def test_addform_grokker_bails_without_portal_type(self):
        
        class AddForm(form.AddForm):
            pass
        
        self.replay()
        
        self.assertEquals(False, grok_component('AddForm', AddForm))

    def test_addform_registers_page_with_portal_type(self):
        
        class AddForm(form.AddForm):
            portal_type = 'my.type'
        
        wrapped = self.create_dummy()
        
        wrap_form_mock = self.mocker.replace('plone.z3cform.layout.wrap_form')
        self.expect(wrap_form_mock(AddForm)).result(wrapped)
        
        page_mock = self.mocker.replace('Products.Five.browser.metaconfigure.page')
        self.expect(page_mock(mocker.ANY, 
                              name='add-my.type',
                              permission='cmf.AddPortalContent',
                              for_=IFolderish,
                              layer=IDefaultBrowserLayer,
                              class_=wrapped))
        
        self.replay()
        
        self.assertEquals(True, grok_component('AddForm', AddForm))

    def test_addform_registers_page_with_custom_name_and_layer(self):
        
        class ILayer(IDefaultBrowserLayer):
            pass
        
        class AddForm(form.AddForm):
            portal_type = 'my.type'
            five.grok.name('add-foo')
            five.grok.layer(ILayer)
            five.grok.require('my.permission')
        
        wrapped = self.create_dummy()
        
        wrap_form_mock = self.mocker.replace('plone.z3cform.layout.wrap_form')
        self.expect(wrap_form_mock(AddForm)).result(wrapped)
        
        page_mock = self.mocker.replace('Products.Five.browser.metaconfigure.page')
        self.expect(page_mock(mocker.ANY, 
                              name='add-foo',
                              permission='my.permission',
                              for_=IFolderish,
                              layer=ILayer,
                              class_=wrapped))
        
        self.replay()
        
        self.assertEquals(True, grok_component('AddForm', AddForm))

    def test_edit_form_bails_without_context(self):
        
        class EditForm(form.AddForm):
            pass
        
        self.replay()
        
        self.assertEquals(False, grok_component('EditForm', EditForm))

    def test_edit_form_bails_without_interface_as_context(self):
        
        class Foo(object):
            pass
        
        class EditForm(form.AddForm):
            five.grok.context(Foo)
        
        self.replay()
        
        self.assertEquals(False, grok_component('EditForm', EditForm))

    def test_editform_with_defaults(self):
        
        class IDummyContent(Interface):
            pass
        
        class EditForm(form.EditForm):
            five.grok.context(IDummyContent)
        
        wrapped = self.create_dummy()
        
        wrap_form_mock = self.mocker.replace('plone.z3cform.layout.wrap_form')
        self.expect(wrap_form_mock(EditForm)).result(wrapped)
        
        page_mock = self.mocker.replace('Products.Five.browser.metaconfigure.page')
        self.expect(page_mock(mocker.ANY, 
                              name='edit',
                              permission='cmf.ModifyPortalContent',
                              for_=IDummyContent,
                              layer=IDefaultBrowserLayer,
                              class_=wrapped))
        
        self.replay()
        
        self.assertEquals(True, grok_component('EditForm', EditForm))
        
    def test_editform_with_custom_layer_name_permission(self):
        
        class IDummyContent(Interface):
            pass
        
        class ILayer(IDefaultBrowserLayer):
            pass
        
        class EditForm(form.EditForm):
            five.grok.context(IDummyContent)
            five.grok.name('edith')
            five.grok.require('my.permission')
            five.grok.layer(ILayer)
        
        wrapped = self.create_dummy()
        
        wrap_form_mock = self.mocker.replace('plone.z3cform.layout.wrap_form')
        self.expect(wrap_form_mock(EditForm)).result(wrapped)
        
        page_mock = self.mocker.replace('Products.Five.browser.metaconfigure.page')
        self.expect(page_mock(mocker.ANY, 
                              name='edith',
                              permission='my.permission',
                              for_=IDummyContent,
                              layer=ILayer,
                              class_=wrapped))
        
        self.replay()
        
        self.assertEquals(True, grok_component('EditForm', EditForm))

def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestContentDirectives))
    suite.addTest(unittest.makeSuite(TestSchemaDirectives))
    suite.addTest(unittest.makeSuite(TestFormDirectives))
    return suite
